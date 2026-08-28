"""Run the versioned five-seed CUDA PPO benchmark against Agent Smith."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from .environment import EnvironmentConfig, TankTrainVectorEnv
from .runtime import git_revision, load_yaml, repository_root, require_cuda, write_json


def environment_config(data: dict[str, Any], seed: int) -> EnvironmentConfig:
    reward = data["reward"]
    return EnvironmentConfig(
        seed=seed,
        num_envs=int(data["num_envs"]),
        ticks_per_action=int(data["ticks_per_action"]),
        max_decisions=int(data["max_decisions"]),
        win_reward=float(reward["win"]),
        loss_reward=float(reward["loss"]),
        survival_reward=float(reward["survival_per_tick"]),
        hit_opponent_reward=float(reward["hit_opponent"]),
        hit_by_opponent_reward=float(reward["hit_by_opponent"]),
    )


def random_policy_report(
    environment_data: dict[str, Any], evaluation: dict[str, Any], policy_seed: int
) -> dict[str, Any]:
    """Evaluate a reproducible random policy on the exact held-out protocol."""
    generator = np.random.default_rng(policy_seed)
    total_wins = total_episodes = 0
    by_seed: dict[str, dict[str, float]] = {}
    episodes_per_seed = int(evaluation["episodes_per_seed"])

    for arena_seed in evaluation["held_out_seeds"]:
        environment = TankTrainVectorEnv(environment_config(environment_data, int(arena_seed)))
        environment.reset(int(arena_seed))
        wins = episodes = 0
        while episodes < episodes_per_seed:
            actions = np.column_stack(
                (
                    generator.integers(0, 3, size=environment.config.num_envs),
                    generator.integers(0, 3, size=environment.config.num_envs),
                    generator.integers(0, 2, size=environment.config.num_envs),
                )
            ).astype(np.int32)
            _, reward, terminated, truncated = environment.step(actions)
            finished = terminated | truncated
            remaining = episodes_per_seed - episodes
            indices = finished.nonzero()[0][:remaining]
            wins += int(((reward[indices] > 0.0) & terminated[indices]).sum())
            episodes += len(indices)
        by_seed[str(arena_seed)] = {
            "episodes": float(episodes),
            "wins": float(wins),
            "win_rate": wins / max(episodes, 1),
        }
        total_wins += wins
        total_episodes += episodes

    return {
        "policy": "random",
        "policy_seed": policy_seed,
        "episodes": total_episodes,
        "wins": total_wins,
        "win_rate": total_wins / max(total_episodes, 1),
        "by_seed": by_seed,
    }


def latest_run(run_name: str) -> Path:
    candidates = sorted((repository_root() / "runs").glob(f"{run_name}_*"))
    if not candidates:
        raise RuntimeError(f"Training run {run_name!r} did not create an output directory.")
    return candidates[-1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/training/benchmark_v1.yaml")
    args = parser.parse_args()
    require_cuda()
    benchmark = load_yaml(args.config)
    training_config_path = str(benchmark["training_config"])
    evaluation_config_path = str(benchmark["evaluation_config"])
    training_config = load_yaml(training_config_path)
    environment_data = load_yaml(training_config["environment"])
    evaluation = load_yaml(evaluation_config_path)

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    output = repository_root() / "outputs" / "benchmarks" / f"ppo_agent_smith_v1_{timestamp}"
    output.mkdir(parents=True, exist_ok=False)
    write_json(
        output / "metadata.json",
        {
            "git_revision": git_revision(),
            "benchmark_config": benchmark,
            "training_config": training_config,
            "evaluation_config": evaluation,
        },
    )

    random_report = random_policy_report(
        environment_data, evaluation, int(benchmark["random_policy_seed"])
    )
    write_json(output / "random_policy.json", random_report)

    runs: list[dict[str, Any]] = []
    for seed in benchmark["training_seeds"]:
        run_name = f"{training_config['run_name']}_seed_{seed}"
        subprocess.run(
            [
                sys.executable,
                "-m",
                "tanktrain.train",
                "--config",
                training_config_path,
                "--seed",
                str(seed),
                "--run-name",
                run_name,
            ],
            cwd=repository_root(),
            check=True,
        )
        run_directory = latest_run(run_name)
        checkpoints = sorted(run_directory.glob("policy_*.pt"))
        if not checkpoints:
            raise RuntimeError(f"No checkpoint produced by {run_directory}.")
        checkpoint = checkpoints[-1]
        subprocess.run(
            [
                sys.executable,
                "-m",
                "tanktrain.evaluate",
                "--checkpoint",
                str(checkpoint),
                "--config",
                evaluation_config_path,
            ],
            cwd=repository_root(),
            check=True,
        )
        report_path = repository_root() / "outputs" / "evaluation" / "latest.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        write_json(output / f"seed_{seed}.json", report)
        runs.append({"seed": int(seed), "run_directory": str(run_directory), "evaluation": report})

    win_rates = [entry["evaluation"]["win_rate"] for entry in runs]
    summary = {
        "random_policy": random_report,
        "ppo_runs": runs,
        "ppo_win_rate_mean": float(np.mean(win_rates)),
        "ppo_win_rate_std": float(np.std(win_rates)),
    }
    write_json(output / "summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    print(f"Benchmark saved to {output}")


if __name__ == "__main__":
    main()
