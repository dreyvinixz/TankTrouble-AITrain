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
    survival_reward: float = 0.002
    hit_opponent_reward: float = 0.10
    hit_by_opponent_reward: float = -0.10


class TankTrainVectorEnv:
    """Batched CPU simulation with NumPy I/O and deterministic auto-resets."""

    observation_size = int(tanktrain_env.OBSERVATION_SIZE)

    def __init__(self, config: EnvironmentConfig) -> None:
        self.config = config
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
        )

    def reset(self, seed: int | None = None) -> np.ndarray:
        return self._native.reset(self.config.seed if seed is None else seed)

    def step(self, actions: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        actions = np.ascontiguousarray(actions, dtype=np.int32)
        if actions.shape != (self.config.num_envs, 3):
            raise ValueError(f"expected action shape {(self.config.num_envs, 3)}, got {actions.shape}")
        observation, reward, terminated, truncated = self._native.step(actions)
        return (
            np.asarray(observation, dtype=np.float32),
            np.asarray(reward, dtype=np.float32),
            np.asarray(terminated, dtype=np.bool_),
            np.asarray(truncated, dtype=np.bool_),
        )
