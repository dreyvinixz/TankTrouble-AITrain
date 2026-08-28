"""Train the first CUDA PPO baseline against the deterministic Agent Smith opponent."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import torch

from .environment import EnvironmentConfig, TankTrainVectorEnv
from .evaluate import (
    ARENA_HEIGHT,
    ARENA_WIDTH,
    COLS,
    ROWS,
    decode_replay_frame,
    extract_maze_walls,
    record_replay_episode,
)
from .model import ActorCritic
from .ppo import PPO, PPOConfig
from .runtime import git_revision, load_yaml, repository_root, require_cuda, seed_everything, write_json
from .telemetry import TelemetryTracker


def _write_live_frame(
    run_directory: Path,
    obs_np: "np.ndarray",
    action: list[int] | None = None,
    value: float = 0.0,
    update: int = 1,
    step: int = 0,
) -> None:
    """Write the current decoded arena state as live_frame.json for real-time dashboard streaming."""
    import numpy as np
    try:
        frame = decode_replay_frame(obs_np, action=action, value=value, step_idx=step)
        frame["walls"] = extract_maze_walls(obs_np)
        frame["dimensions"] = {"width": ARENA_WIDTH, "height": ARENA_HEIGHT, "cols": COLS, "rows": ROWS}
        frame["update"] = update
        frame["live"] = True
        tmp = run_directory / "live_frame.tmp"
        tmp.write_text(json.dumps(frame), encoding="utf-8")
        tmp.rename(run_directory / "live_frame.json")  # atomic replace
    except Exception:
        pass


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/training/ppo_v1.yaml")
    args = parser.parse_args()
    config = load_yaml(args.config)
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
        survival_reward=float(environment_data["reward"].get("survival_per_tick", 0.0)),
        hit_opponent_reward=float(environment_data["reward"].get("hit_opponent", 0.0)),
        hit_by_opponent_reward=float(environment_data["reward"].get("hit_by_opponent", 0.0)),
        timeout_reward=float(environment_data["reward"].get("timeout", -0.20)),
        draw_reward=float(environment_data["reward"].get("draw", 0.0)),
        frame_stack=int(environment_data.get("frame_stack", 1)),
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
    replays_dir = run_directory / "replays"
    replays_dir.mkdir(parents=True, exist_ok=True)
    checkpoints_dir = run_directory / "checkpoints"
    checkpoints_dir.mkdir(parents=True, exist_ok=True)

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
            "created_at": timestamp,
        },
    )

    tracker = TelemetryTracker(
        run_name=config["run_name"],
        total_updates=int(config["total_updates"]),
        rollout_steps=int(config["rollout_steps"]),
        num_envs=int(environment_data["num_envs"]),
        run_directory=run_directory,
    )

    best_reward = float("-inf")
    history_path = run_directory / "metrics.jsonl"
    try:
        with history_path.open("w", encoding="utf-8") as history:
            for update in range(1, int(config["total_updates"]) + 1):
                def _live_step(obs_np, action, value, step_idx):
                    _write_live_frame(
                        run_directory,
                        obs_np,
                        action=action,
                        value=value,
                        update=update,
                        step=update * int(config["rollout_steps"]) + step_idx,
                    )

                observation, batch, rollout_metrics = ppo.collect(
                    environment,
                    observation,
                    step_callback=_live_step,
                )
                update_metrics = ppo.update(batch)
                raw_metrics = {**rollout_metrics, **update_metrics}

                # Update live telemetry state & inspect network
                progress = tracker.update(update, raw_metrics, model=model, sample_obs=observation[:1])
                full_metrics = {"update": update, **progress.latest_metrics}

                history.write(json.dumps(full_metrics, sort_keys=True) + "\n")
                history.flush()

                if update == 1 or update % int(config["checkpoint_interval"]) == 0 or update == int(config["total_updates"]):
                    tracker.set_status("evaluating")
                    ckpt_payload = {
                        "model": model.state_dict(),
                        "hidden_sizes": hidden_sizes,
                        "observation_size": environment.observation_size,
                        "environment_config": environment_data,
                        "training_config": config,
                        "update": update,
                        "mean_reward": progress.mean_reward,
                        "win_rate": progress.win_rate,
                    }
                    ckpt_path = checkpoints_dir / f"policy_{update:05d}.pt"
                    torch.save(ckpt_payload, ckpt_path)

                    # Generate evaluation replay
                    try:
                        eval_seed = seed + update * 31
                        replay_data = record_replay_episode(
                            model, environment_config, seed=eval_seed, device=device, max_steps=400
                        )
                        replay_data["update"] = update
                        replay_file = replays_dir / f"replay_update_{update:05d}.json"
                        write_json(replay_file, replay_data)
                        write_json(replays_dir / "latest.json", replay_data)

                        # Check if this is the best validated checkpoint
                        if progress.mean_reward >= best_reward:
                            best_reward = progress.mean_reward
                            torch.save(ckpt_payload, checkpoints_dir / "policy_best.pt")
                            write_json(replays_dir / "best.json", replay_data)
                    except Exception as replay_err:
                        print(f"Warning: could not record replay snapshot: {replay_err}")

                    tracker.set_status("training" if update < int(config["total_updates"]) else "completed")

                print(json.dumps(full_metrics, sort_keys=True))

        tracker.set_status("completed")
    except Exception as exc:
        tracker.set_status("error")
        raise exc


if __name__ == "__main__":
    main()
