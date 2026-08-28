"""Evaluate a CUDA PPO checkpoint against fixed held-out arena seeds and record 2D replays."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import torch

from .environment import EnvironmentConfig, TankTrainVectorEnv
from .model import ActorCritic
from .runtime import load_yaml, repository_root, require_cuda, write_json


def decode_replay_frame(obs: np.ndarray, action: list[int] | None = None, reward: float = 0.0, value: float = 0.0) -> dict[str, Any]:
    """Decode a 376-element observation into a structured visual frame for the Canvas 2D player."""
    width, height = 660.0, 420.0
    player = {
        "x": round(float(obs[0]) * width, 1),
        "y": round(float(obs[1]) * height, 1),
        "angle": round(float(obs[2]) * 360.0, 1),
        "ammo": int(round(float(obs[3]) * 5.0)),
    }
    opponent = {
        "x": round(float(obs[4]) * width, 1),
        "y": round(float(obs[5]) * height, 1),
        "angle": round(float(obs[6]) * 360.0, 1),
        "ammo": int(round(float(obs[7]) * 5.0)),
    }

    shells = []
    # 8 shells * 7 features each, starting at index 12
    for i in range(8):
        base = 12 + i * 7
        if base + 6 < len(obs) and obs[base] > 0.5:
            shells.append(
                {
                    "x": round(float(obs[base + 1]) * width, 1),
                    "y": round(float(obs[base + 2]) * height, 1),
                    "angle": round(float(obs[base + 3]) * 360.0, 1),
                    "owner": int(round(float(obs[base + 4]))),
                    "ttl": int(round(float(obs[base + 5]) * 180.0)),
                }
            )

    return {
        "player": player,
        "opponent": opponent,
        "shells": shells,
        "action": action or [0, 0, 0],
        "reward": round(reward, 3),
        "value": round(value, 3),
    }


def extract_maze_walls(obs: np.ndarray) -> list[dict[str, float]]:
    """Extract maze walls from the 308-element wall mask in observation."""
    walls = []
    cell_w, cell_h = 60.0, 60.0
    cols, rows = 11, 7
    base = 68

    # Outer boundary walls
    walls.append({"x1": 0.0, "y1": 0.0, "x2": 660.0, "y2": 0.0})
    walls.append({"x1": 660.0, "y1": 0.0, "x2": 660.0, "y2": 420.0})
    walls.append({"x1": 660.0, "y1": 420.0, "x2": 0.0, "y2": 420.0})
    walls.append({"x1": 0.0, "y1": 420.0, "x2": 0.0, "y2": 0.0})

    for cell in range(cols * rows):
        col = cell % cols
        row = cell // cols
        cx = col * cell_w
        cy = row * cell_h

        # 4 directions: 0=North, 1=East, 2=South, 3=West
        if base + cell * 4 + 3 < len(obs):
            north = obs[base + cell * 4 + 0] > 0.5
            east = obs[base + cell * 4 + 1] > 0.5
            south = obs[base + cell * 4 + 2] > 0.5
            west = obs[base + cell * 4 + 3] > 0.5

            if north and row > 0:
                walls.append({"x1": cx, "y1": cy, "x2": cx + cell_w, "y2": cy})
            if east and col < cols - 1:
                walls.append({"x1": cx + cell_w, "y1": cy, "x2": cx + cell_w, "y2": cy + cell_h})
            if south and row < rows - 1:
                walls.append({"x1": cx, "y1": cy + cell_h, "x2": cx + cell_w, "y2": cy + cell_h})
            if west and col > 0:
                walls.append({"x1": cx, "y1": cy, "x2": cx, "y2": cy + cell_h})

    return walls


def record_replay_episode(
    model: torch.nn.Module,
    environment_config: EnvironmentConfig,
    seed: int,
    device: torch.device,
    max_steps: int = 600,
) -> dict[str, Any]:
    """Simulate a single deterministic evaluation match and return the replay trace."""
    eval_config = EnvironmentConfig(
        seed=seed,
        num_envs=1,
        ticks_per_action=environment_config.ticks_per_action,
        max_decisions=max_steps,
        win_reward=environment_config.win_reward,
        loss_reward=environment_config.loss_reward,
        survival_reward=environment_config.survival_reward,
        hit_opponent_reward=environment_config.hit_opponent_reward,
        hit_by_opponent_reward=environment_config.hit_by_opponent_reward,
    )
    env = TankTrainVectorEnv(eval_config)
    obs = env.reset(seed)
    raw_obs = obs[0]

    walls = extract_maze_walls(raw_obs)
    frames = [decode_replay_frame(raw_obs)]
    total_reward = 0.0
    winner = "draw"

    for step_idx in range(max_steps):
        obs_tensor = torch.as_tensor(obs, dtype=torch.float32, device=device)
        with torch.no_grad():
            distributions, value = model(obs_tensor)
            action = torch.stack([d.probs.argmax(dim=-1) for d in distributions], dim=-1)
            val = float(value.item())

        action_np = action.cpu().numpy()
        action_list = action_np[0].tolist()

        next_obs, reward, terminated, truncated = env.step(action_np)
        step_reward = float(reward[0])
        total_reward += step_reward

        frame = decode_replay_frame(next_obs[0], action=action_list, reward=step_reward, value=val)
        frames.append(frame)
        obs = next_obs

        if bool(terminated[0]):
            winner = "player" if step_reward > 0.0 else "opponent"
            break
        if bool(truncated[0]):
            winner = "timeout"
            break

    return {
        "seed": seed,
        "total_frames": len(frames),
        "total_reward": round(total_reward, 3),
        "winner": winner,
        "dimensions": {"width": 660, "height": 420, "cols": 11, "rows": 7},
        "walls": walls,
        "frames": frames,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--config", default="config/training/evaluation_v1.yaml")
    parser.add_argument("--record-replay", action="store_true", help="Record and save replay JSON for the best match")
    args = parser.parse_args()
    device = require_cuda()
    evaluation = load_yaml(args.config)
    checkpoint = torch.load(args.checkpoint, map_location=device, weights_only=False)
    model = ActorCritic(int(checkpoint["observation_size"]), list(checkpoint["hidden_sizes"])).to(device)
    model.load_state_dict(checkpoint["model"])
    model.eval()
    environment_data = checkpoint["environment_config"]

    env_config = EnvironmentConfig(
        seed=17,
        num_envs=int(environment_data["num_envs"]),
        ticks_per_action=int(environment_data["ticks_per_action"]),
        max_decisions=int(environment_data["max_decisions"]),
        win_reward=float(environment_data["reward"]["win"]),
        loss_reward=float(environment_data["reward"]["loss"]),
        survival_reward=float(environment_data["reward"]["survival_per_tick"]),
        hit_opponent_reward=float(environment_data["reward"]["hit_opponent"]),
        hit_by_opponent_reward=float(environment_data["reward"]["hit_by_opponent"]),
    )

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

    if args.record_replay:
        best_seed = int(evaluation["held_out_seeds"][0])
        replay_data = record_replay_episode(model, env_config, seed=best_seed, device=device)
        replay_file = output / "latest_replay.json"
        write_json(replay_file, replay_data)
        print(f"Recorded evaluation replay saved to {replay_file}")


if __name__ == "__main__":
    main()
