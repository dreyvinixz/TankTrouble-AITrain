"""Train the first CUDA PPO baseline against the deterministic Agent Smith opponent."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import torch

from .environment import EnvironmentConfig, TankTrainVectorEnv
from .model import ActorCritic
from .ppo import PPO, PPOConfig
from .runtime import git_revision, load_yaml, repository_root, require_cuda, seed_everything, write_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/training/ppo_v1.yaml")
    parser.add_argument("--seed", type=int, help="Override the YAML seed for benchmark runs.")
    parser.add_argument("--run-name", help="Override the YAML run name for benchmark runs.")
    args = parser.parse_args()
    config = load_yaml(args.config)
    if args.seed is not None:
        config["seed"] = args.seed
    if args.run_name is not None:
        config["run_name"] = args.run_name
    if config.get("device") != "cuda":
        raise RuntimeError("The training configuration must explicitly request device: cuda.")
    device = require_cuda()
    seed = int(config["seed"])
    seed_everything(seed)

    environment_data = load_yaml(config["environment"])
    environment_config = EnvironmentConfig(
        seed=int(environment_data["seed"]),
        num_envs=int(environment_data["num_envs"]),
        ticks_per_action=int(environment_data["ticks_per_action"]),
        max_decisions=int(environment_data["max_decisions"]),
        win_reward=float(environment_data["reward"]["win"]),
        loss_reward=float(environment_data["reward"]["loss"]),
        survival_reward=float(environment_data["reward"]["survival_per_tick"]),
        hit_opponent_reward=float(environment_data["reward"]["hit_opponent"]),
        hit_by_opponent_reward=float(environment_data["reward"]["hit_by_opponent"]),
    )
    environment = TankTrainVectorEnv(environment_config)
    observation = torch.as_tensor(environment.reset(seed), dtype=torch.float32, device=device)
    hidden_sizes = [int(value) for value in config["hidden_sizes"]]
    model = ActorCritic(environment.observation_size, hidden_sizes)
    ppo = PPO(
        model,
        PPOConfig(
            rollout_steps=int(config["rollout_steps"]),
            learning_rate=float(config["learning_rate"]),
            gamma=float(config["gamma"]),
            gae_lambda=float(config["gae_lambda"]),
            clip_ratio=float(config["clip_ratio"]),
            entropy_coefficient=float(config["entropy_coefficient"]),
            value_coefficient=float(config["value_coefficient"]),
            max_grad_norm=float(config["max_grad_norm"]),
            update_epochs=int(config["update_epochs"]),
            minibatch_size=int(config["minibatch_size"]),
        ),
        device,
    )

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    run_directory = repository_root() / "runs" / f"{config['run_name']}_{timestamp}"
    run_directory.mkdir(parents=True, exist_ok=False)
    write_json(
        run_directory / "metadata.json",
        {
            "git_revision": git_revision(),
            "device": str(device),
            "gpu": torch.cuda.get_device_name(0),
            "torch": torch.__version__,
            "cuda": torch.version.cuda,
            "training_config": config,
            "environment_config": environment_data,
        },
    )

    history_path = run_directory / "metrics.jsonl"
    with history_path.open("w", encoding="utf-8") as history:
        for update in range(1, int(config["total_updates"]) + 1):
            observation, batch, rollout_metrics = ppo.collect(environment, observation)
            update_metrics = ppo.update(batch)
            metrics = {"update": update, **rollout_metrics, **update_metrics}
            history.write(json.dumps(metrics, sort_keys=True) + "\n")
            history.flush()
            if update == 1 or update % int(config["checkpoint_interval"]) == 0:
                torch.save(
                    {
                        "model": model.state_dict(),
                        "hidden_sizes": hidden_sizes,
                        "observation_size": environment.observation_size,
                        "environment_config": environment_data,
                        "training_config": config,
                    },
                    run_directory / f"policy_{update:05d}.pt",
                )
            print(json.dumps(metrics, sort_keys=True))

    print(f"Run saved to {run_directory}")


if __name__ == "__main__":
    main()
