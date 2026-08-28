"""Evaluate a CUDA PPO checkpoint against fixed held-out arena seeds."""

from __future__ import annotations

import argparse
from pathlib import Path

import torch

from .environment import EnvironmentConfig, TankTrainVectorEnv
from .model import ActorCritic
from .runtime import load_yaml, repository_root, require_cuda, write_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--config", default="config/training/evaluation_v1.yaml")
    args = parser.parse_args()
    device = require_cuda()
    evaluation = load_yaml(args.config)
    checkpoint = torch.load(args.checkpoint, map_location=device, weights_only=False)
    model = ActorCritic(int(checkpoint["observation_size"]), list(checkpoint["hidden_sizes"])).to(device)
    model.load_state_dict(checkpoint["model"])
    model.eval()
    environment_data = checkpoint["environment_config"]
    total_wins = total_episodes = 0
    results: dict[str, dict[str, float]] = {}

    for seed in evaluation["held_out_seeds"]:
        environment = TankTrainVectorEnv(
            EnvironmentConfig(
                seed=int(seed),
                num_envs=int(environment_data["num_envs"]),
                ticks_per_action=int(environment_data["ticks_per_action"]),
                max_decisions=int(environment_data["max_decisions"]),
                win_reward=float(environment_data["reward"]["win"]),
                loss_reward=float(environment_data["reward"]["loss"]),
                survival_reward=float(environment_data["reward"]["survival_per_tick"]),
                hit_opponent_reward=float(environment_data["reward"]["hit_opponent"]),
                hit_by_opponent_reward=float(environment_data["reward"]["hit_by_opponent"]),
            )
        )
        observation = torch.as_tensor(environment.reset(int(seed)), dtype=torch.float32, device=device)
        wins = episodes = 0
        while episodes < int(evaluation["episodes_per_seed"]):
            with torch.no_grad():
                distributions, _ = model(observation)
                action = torch.stack([distribution.probs.argmax(dim=-1) for distribution in distributions], dim=-1)
            next_observation, reward, terminated, truncated = environment.step(action.cpu().numpy())
            finished = terminated | truncated
            remaining = int(evaluation["episodes_per_seed"]) - episodes
            finished_indices = finished.nonzero()[0][:remaining]
            wins += int(((reward[finished_indices] > 0.0) & terminated[finished_indices]).sum())
            episodes += len(finished_indices)
            observation = torch.as_tensor(next_observation, dtype=torch.float32, device=device)
        episodes = min(episodes, int(evaluation["episodes_per_seed"]))
        results[str(seed)] = {"episodes": float(episodes), "wins": float(wins), "win_rate": wins / max(episodes, 1)}
        total_wins += wins
        total_episodes += episodes

    report = {
        "checkpoint": str(Path(args.checkpoint).resolve()),
        "device": str(device),
        "episodes": total_episodes,
        "wins": total_wins,
        "win_rate": total_wins / max(total_episodes, 1),
        "by_seed": results,
    }
    output = repository_root() / "outputs" / "evaluation"
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "latest.json", report)
    print(report)


if __name__ == "__main__":
    main()
