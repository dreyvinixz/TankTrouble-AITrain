"""CUDA-only PPO implementation with GPU-resident rollout buffers."""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import nn

from .model import ActorCritic


@dataclass(frozen=True)
class PPOConfig:
    rollout_steps: int
    learning_rate: float
    gamma: float
    gae_lambda: float
    clip_ratio: float
    entropy_coefficient: float
    value_coefficient: float
    max_grad_norm: float
    update_epochs: int
    minibatch_size: int


class PPO:
    def __init__(self, model: ActorCritic, config: PPOConfig, device: torch.device) -> None:
        if device.type != "cuda":
            raise RuntimeError("PPO is CUDA-only by project policy.")
        self.model = model.to(device)
        self.config = config
        self.device = device
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=config.learning_rate, eps=1e-5)
        self._episode_returns: torch.Tensor | None = None
        self._episode_wins: int = 0
        self._episode_count: int = 0

    def collect(
        self,
        environment: Any,
        observation: torch.Tensor,
        step_callback: Any | None = None,
    ) -> tuple[torch.Tensor, dict[str, torch.Tensor], dict[str, float]]:
        observations: list[torch.Tensor] = []
        actions: list[torch.Tensor] = []
        log_probabilities: list[torch.Tensor] = []
        rewards: list[torch.Tensor] = []
        dones: list[torch.Tensor] = []
        values: list[torch.Tensor] = []
        completed = 0
        completed_reward = 0.0
        completed_wins = 0
        completed_kills = 0
        completed_losses = 0
        completed_suicides = 0
        completed_timeouts = 0
        if self._episode_returns is None or self._episode_returns.shape[0] != observation.shape[0]:
            self._episode_returns = torch.zeros(observation.shape[0], device=self.device)

        for step_idx in range(self.config.rollout_steps):
            with torch.no_grad():
                action, log_probability, value = self.model.sample(observation)

            if step_callback is not None and step_idx % 4 == 0:
                try:
                    step_callback(
                        observation[0].cpu().numpy(),
                        action[0].cpu().tolist(),
                        float(value[0].item()),
                        step_idx,
                    )
                except Exception:
                    pass

            step_result = environment.step(action.cpu().numpy())
            next_observation, reward, terminated, truncated = step_result[:4]
            causes = step_result[4] if len(step_result) > 4 else np.zeros_like(terminated, dtype=np.uint8)
            done = terminated | truncated
            observations.append(observation)
            actions.append(action)
            log_probabilities.append(log_probability)
            values.append(value)
            reward_tensor = torch.as_tensor(reward, dtype=torch.float32, device=self.device)
            done_tensor = torch.as_tensor(done, dtype=torch.float32, device=self.device)
            rewards.append(reward_tensor)
            dones.append(done_tensor)
            self._episode_returns += reward_tensor

            if bool(done.any()):
                done_mask = done_tensor.bool()
                finished_rewards = self._episode_returns[done_mask]
                completed += int(done.sum())
                completed_reward += float(finished_rewards.sum())
                
                finished_causes = causes[done]
                completed_kills += int((finished_causes == 3).sum())
                completed_losses += int((finished_causes == 1).sum())
                completed_suicides += int((finished_causes == 2).sum())
                completed_timeouts += int((finished_causes == 6).sum())
                completed_wins += int((finished_causes == 3).sum())
                self._episode_returns[done_mask] = 0.0

            observation = torch.as_tensor(next_observation, dtype=torch.float32, device=self.device)

        with torch.no_grad():
            _, bootstrap_value = self.model(observation)
        reward_tensor = torch.stack(rewards)
        done_tensor = torch.stack(dones)
        value_tensor = torch.stack(values)
        advantages = torch.zeros_like(reward_tensor, device=self.device)
        last_advantage = torch.zeros_like(bootstrap_value, device=self.device)
        next_value = bootstrap_value
        for index in reversed(range(self.config.rollout_steps)):
            non_terminal = 1.0 - done_tensor[index]
            delta = reward_tensor[index] + self.config.gamma * next_value * non_terminal - value_tensor[index]
            last_advantage = delta + self.config.gamma * self.config.gae_lambda * non_terminal * last_advantage
            advantages[index] = last_advantage
            next_value = value_tensor[index]
        returns = advantages + value_tensor
        batch = {
            "observation": torch.cat(observations),
            "action": torch.cat(actions),
            "log_probability": torch.cat(log_probabilities),
            "advantage": advantages.flatten(),
            "return": returns.flatten(),
            "value": value_tensor.flatten(),
        }
        mean_ret = (completed_reward / completed) if completed > 0 else 0.0
        win_rate = (completed_kills / completed) if completed > 0 else 0.0
        metrics = {
            "completed_episodes": float(completed),
            "completed_reward": mean_ret,
            "mean_reward": mean_ret,
            "win_rate": win_rate,
            "timeout_rate": (completed_timeouts / completed) if completed > 0 else 0.0,
            "suicide_rate": (completed_suicides / completed) if completed > 0 else 0.0,
            "loss_rate": (completed_losses / completed) if completed > 0 else 0.0,
            "episodes": float(completed),
        }
        return observation, batch, metrics

    def update(self, batch: dict[str, torch.Tensor]) -> dict[str, float]:
        advantage = batch["advantage"]
        batch["advantage"] = (advantage - advantage.mean()) / (advantage.std(unbiased=False) + 1e-8)
        batch_size = batch["observation"].shape[0]
        indices = torch.arange(batch_size, device=self.device)
        policy_loss_total = value_loss_total = entropy_total = 0.0
        approx_kl_total = clip_fraction_total = grad_norm_total = 0.0
        updates = 0
        for _ in range(self.config.update_epochs):
            for minibatch in indices[torch.randperm(batch_size, device=self.device)].split(self.config.minibatch_size):
                new_log_probability, entropy, value = self.model.evaluate_actions(
                    batch["observation"][minibatch], batch["action"][minibatch]
                )
                log_ratio = new_log_probability - batch["log_probability"][minibatch]
                ratio = log_ratio.exp()
                unclipped = ratio * batch["advantage"][minibatch]
                clipped = ratio.clamp(1.0 - self.config.clip_ratio, 1.0 + self.config.clip_ratio) * batch["advantage"][minibatch]
                policy_loss = -torch.minimum(unclipped, clipped).mean()
                value_loss = 0.5 * (value - batch["return"][minibatch]).square().mean()
                entropy_loss = entropy.mean()
                loss = policy_loss + self.config.value_coefficient * value_loss - self.config.entropy_coefficient * entropy_loss

                with torch.no_grad():
                    approx_kl = ((ratio - 1.0) - log_ratio).mean()
                    clip_frac = ((ratio - 1.0).abs() > self.config.clip_ratio).float().mean()

                self.optimizer.zero_grad(set_to_none=True)
                loss.backward()
                grad_norm = nn.utils.clip_grad_norm_(self.model.parameters(), self.config.max_grad_norm)
                self.optimizer.step()

                policy_loss_total += float(policy_loss.detach())
                value_loss_total += float(value_loss.detach())
                entropy_total += float(entropy_loss.detach())
                approx_kl_total += float(approx_kl.detach())
                clip_fraction_total += float(clip_frac.detach())
                grad_norm_total += float(grad_norm)
                updates += 1

        return {
            "policy_loss": policy_loss_total / max(updates, 1),
            "value_loss": value_loss_total / max(updates, 1),
            "entropy": entropy_total / max(updates, 1),
            "approx_kl": approx_kl_total / max(updates, 1),
            "clip_fraction": clip_fraction_total / max(updates, 1),
            "grad_norm": grad_norm_total / max(updates, 1),
            "learning_rate": float(self.optimizer.param_groups[0]["lr"]),
        }
