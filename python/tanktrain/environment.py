"""pybind11 adapter for the deterministic C++ TankArena vector environment."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

try:
    import tanktrain_env
except ImportError as exc:  # pragma: no cover - setup failure is user-facing
    raise RuntimeError(
        "Native environment module is missing. Run "
        "scripts/training/build_native.sh from WSL2 first."
    ) from exc


@dataclass(frozen=True)
class EnvironmentConfig:
    seed: int = 17
    num_envs: int = 32
    ticks_per_action: int = 3
    max_decisions: int = 600
    win_reward: float = 1.0
    loss_reward: float = -1.0
    survival_reward: float = 0.0
    hit_opponent_reward: float = 0.0
    hit_by_opponent_reward: float = 0.0
    timeout_reward: float = -0.20
    draw_reward: float = 0.0
    frame_stack: int = 1


class TankTrainVectorEnv:
    """Batched CPU simulation with NumPy I/O and deterministic auto-resets."""

    def __init__(self, config: EnvironmentConfig) -> None:
        self.config = config
        self.frame_stack = max(1, int(config.frame_stack))
        self.base_obs_size = int(tanktrain_env.OBSERVATION_SIZE)
        self.observation_size = self.base_obs_size * self.frame_stack
        self._native = tanktrain_env.VectorTankArena(
            config.num_envs,
            config.seed,
            config.ticks_per_action,
            config.max_decisions,
            config.win_reward,
            config.loss_reward,
            config.survival_reward,
            config.hit_opponent_reward,
            config.hit_by_opponent_reward,
            config.timeout_reward,
            config.draw_reward,
        )
        self._frames = np.zeros((config.num_envs, self.frame_stack, self.base_obs_size), dtype=np.float32)

    def reset(self, seed: int | None = None) -> np.ndarray:
        obs = self._native.reset(self.config.seed if seed is None else seed)
        for k in range(self.frame_stack):
            self._frames[:, k, :] = obs
        if self.frame_stack == 1:
            return np.asarray(obs, dtype=np.float32)
        return self._frames.reshape(self.config.num_envs, -1).astype(np.float32)

    def step(self, actions: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        actions = np.ascontiguousarray(actions, dtype=np.int32)
        if actions.shape != (self.config.num_envs, 3):
            raise ValueError(f"expected action shape {(self.config.num_envs, 3)}, got {actions.shape}")
        next_obs, reward, terminated, truncated, causes = self._native.step(actions)
        
        if self.frame_stack > 1:
            self._frames[:, 1:, :] = self._frames[:, :-1, :]
            self._frames[:, 0, :] = next_obs
            done = terminated | truncated
            if bool(done.any()):
                for k in range(self.frame_stack):
                    self._frames[done, k, :] = next_obs[done]
            stacked_obs = self._frames.reshape(self.config.num_envs, -1).astype(np.float32)
            return (
                stacked_obs,
                np.asarray(reward, dtype=np.float32),
                np.asarray(terminated, dtype=np.bool_),
                np.asarray(truncated, dtype=np.bool_),
                np.asarray(causes, dtype=np.uint8),
            )

        return (
            np.asarray(next_obs, dtype=np.float32),
            np.asarray(reward, dtype=np.float32),
            np.asarray(terminated, dtype=np.bool_),
            np.asarray(truncated, dtype=np.bool_),
            np.asarray(causes, dtype=np.uint8),
        )
