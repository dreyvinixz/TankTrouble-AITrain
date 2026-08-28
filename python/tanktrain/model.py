"""MultiDiscrete actor-critic network for CUDA PPO."""

from __future__ import annotations

import torch
from torch import nn
from torch.distributions import Categorical


class ActorCritic(nn.Module):
    def __init__(self, observation_size: int, hidden_sizes: list[int]) -> None:
        super().__init__()
        layers: list[nn.Module] = []
        previous = observation_size
        for size in hidden_sizes:
            layers.extend([nn.Linear(previous, size), nn.Tanh()])
            previous = size
        self.backbone = nn.Sequential(*layers)
        self.movement = nn.Linear(previous, 3)
        self.rotation = nn.Linear(previous, 3)
        self.fire = nn.Linear(previous, 2)
        self.value = nn.Linear(previous, 1)

    def forward(self, observation: torch.Tensor) -> tuple[list[Categorical], torch.Tensor]:
        latent = self.backbone(observation)
        distributions = [
            Categorical(logits=self.movement(latent)),
            Categorical(logits=self.rotation(latent)),
            Categorical(logits=self.fire(latent)),
        ]
        return distributions, self.value(latent).squeeze(-1)

    def sample(self, observation: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        distributions, value = self(observation)
        action = torch.stack([distribution.sample() for distribution in distributions], dim=-1)
        log_probability = torch.stack(
            [distribution.log_prob(action[:, index]) for index, distribution in enumerate(distributions)], dim=-1
        ).sum(dim=-1)
        return action, log_probability, value

    def evaluate_actions(
        self, observation: torch.Tensor, action: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        distributions, value = self(observation)
        log_probability = torch.stack(
            [distribution.log_prob(action[:, index]) for index, distribution in enumerate(distributions)], dim=-1
        ).sum(dim=-1)
        entropy = torch.stack([distribution.entropy() for distribution in distributions], dim=-1).sum(dim=-1)
        return log_probability, entropy, value
