"""Evaluate a CUDA PPO checkpoint against fixed held-out arena seeds and record 2D replays."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import numpy as np
import torch

from .environment import EnvironmentConfig, TankTrainVectorEnv
from .model import ActorCritic
from .runtime import load_yaml, repository_root, require_cuda, write_json

# Arena physical constants matching TankArena.cc
ARENA_WIDTH = 660.0
ARENA_HEIGHT = 420.0
CELL_SIZE = 60.0
COLS = 11
ROWS = 7


def decode_replay_frame(
    obs: np.ndarray,
    action: list[int] | None = None,
    reward: float = 0.0,
    value: float = 0.0,
    step_idx: int = 0,
) -> dict[str, Any]:
    """Decode a 376-element observation into a structured visual frame according to the exact TankArena.cc contract."""
    # 1. Player Tank (indices 0..5): x/width, y/height, sin(angle), cos(angle), ammo/5, alive
    player_x = float(obs[0]) * ARENA_WIDTH
    player_y = float(obs[1]) * ARENA_HEIGHT
    player_sin = float(obs[2])
    player_cos = float(obs[3])
    player_angle = math.degrees(math.atan2(player_sin, player_cos)) % 360.0
    player_ammo = int(round(float(obs[4]) * 5.0))
    player_alive = bool(obs[5] > 0.5)

    player = {
        "x": round(player_x, 1),
        "y": round(player_y, 1),
        "angle": round(player_angle, 1),
        "ammo": max(0, min(5, player_ammo)),
        "alive": player_alive,
    }

    # 2. Opponent Tank (indices 6..11): x/width, y/height, sin(angle), cos(angle), ammo/5, alive
    opponent_x = float(obs[6]) * ARENA_WIDTH
    opponent_y = float(obs[7]) * ARENA_HEIGHT
    opponent_sin = float(obs[8])
    opponent_cos = float(obs[9])
    opponent_angle = math.degrees(math.atan2(opponent_sin, opponent_cos)) % 360.0
    opponent_ammo = int(round(float(obs[10]) * 5.0))
    opponent_alive = bool(obs[11] > 0.5)

    opponent = {
        "x": round(opponent_x, 1),
        "y": round(opponent_y, 1),
        "angle": round(opponent_angle, 1),
        "ammo": max(0, min(5, opponent_ammo)),
        "alive": opponent_alive,
    }

    # 3. Active Shells (indices 12..67 = 8 shells * 7 features each)
    shells = []
    for i in range(8):
        base = 12 + i * 7
        if base + 6 < len(obs):
            active = obs[base + 6] > 0.5
            if active:
                shell_x = player_x + float(obs[base + 0]) * ARENA_WIDTH
                shell_y = player_y + float(obs[base + 1]) * ARENA_HEIGHT
                shell_sin = float(obs[base + 2])
                shell_cos = float(obs[base + 3])
                shell_angle = math.degrees(math.atan2(shell_sin, shell_cos)) % 360.0
                shell_owner = 0 if obs[base + 4] > 0.0 else 1
                shell_ttl = int(round(float(obs[base + 5]) * 180.0))

                shells.append(
                    {
                        "x": round(shell_x, 1),
                        "y": round(shell_y, 1),
                        "angle": round(shell_angle, 1),
                        "owner": shell_owner,
                        "ttl": max(0, shell_ttl),
                    }
                )

    return {
        "step": step_idx,
        "player": player,
        "opponent": opponent,
        "shells": shells,
        "action": action or [0, 0, 0],
        "reward": round(reward, 3),
        "value": round(value, 3),
    }


def extract_maze_walls(obs: np.ndarray) -> list[dict[str, float]]:
    """Extract unique line segments representing maze walls from the 308-element wall mask."""
    walls = []
    base = 68

    # Outer boundary walls
    walls.append({"x1": 0.0, "y1": 0.0, "x2": ARENA_WIDTH, "y2": 0.0})
    walls.append({"x1": ARENA_WIDTH, "y1": 0.0, "x2": ARENA_WIDTH, "y2": ARENA_HEIGHT})
    walls.append({"x1": ARENA_WIDTH, "y1": ARENA_HEIGHT, "x2": 0.0, "y2": ARENA_HEIGHT})
    walls.append({"x1": 0.0, "y1": ARENA_HEIGHT, "x2": 0.0, "y2": 0.0})

    # Internal cell walls
    for cell in range(COLS * ROWS):
        col = cell % COLS
        row = cell // COLS
        cx = col * CELL_SIZE
        cy = row * CELL_SIZE

        # 4 directions: 0=North, 1=East, 2=South, 3=West
        idx = base + cell * 4
        if idx + 3 < len(obs):
            north = obs[idx + 0] > 0.5
            east = obs[idx + 1] > 0.5

            if north and row > 0:
                walls.append({"x1": cx, "y1": cy, "x2": cx + CELL_SIZE, "y2": cy})
            if east and col < COLS - 1:
                walls.append({"x1": cx + CELL_SIZE, "y1": cy, "x2": cx + CELL_SIZE, "y2": cy + CELL_SIZE})

    return walls


def record_replay_episode(
    model: torch.nn.Module,
    environment_config: EnvironmentConfig,
    seed: int,
    device: torch.device,
    max_steps: int = 600,
) -> dict[str, Any]:
    """Simulate a single deterministic evaluation match and return the complete replay trace."""
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
    frames = [decode_replay_frame(raw_obs, step_idx=0)]
    total_reward = 0.0
    winner = "draw"

    for step_idx in range(1, max_steps + 1):
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

        frame = decode_replay_frame(
            next_obs[0], action=action_list, reward=step_reward, value=val, step_idx=step_idx
        )
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
        "dimensions": {"width": int(ARENA_WIDTH), "height": int(ARENA_HEIGHT), "cols": COLS, "rows": ROWS},
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
