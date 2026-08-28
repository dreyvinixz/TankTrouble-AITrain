# Architecture

## Current game-client foundation

The imported TankTrouble client keeps gameplay, rendering, and networking in separate components:

| Component | Responsibility |
| --- | --- |
| `src/app/` | GTKmm screens, keyboard input, application entry point, and game window. |
| `src/game/` | Game loop, map, objects, controllers, input events, and networking protocol. |
| `src/core/` | Geometry, vectors, collision checks, and identifiers. |
| `src/ai/baselines/agent_smith/` | Existing rule-based opponent: evasion, pathfinding, targeting, and firing. |
| `third_party/ev/` | Attributed event-driven networking dependency. |

## AI-training boundary

New training features must not depend on GTKmm. The intended project-owned structure is:

```text
src/training/
  environment/  # C++ deterministic reset/step arena
  bindings/     # pybind11 vector-environment module
python/tanktrain/
  model.py      # CUDA actor-critic network
  ppo.py        # CUDA rollout buffer and PPO update
  train.py      # Reproducible experiment entry point
config/training/ # Versioned environment, PPO, and evaluation templates
tests/training/  # Deterministic C++ regression tests
```

`TankArena` exposes `reset(seed)` and `step(TankAction)`. Each step accepts
`MultiDiscrete(3, 3, 2)` controls, advances a fixed number of simulation
ticks, and returns a fixed privileged observation vector, reward, terminal
state, and truncation state. GTKmm remains an optional visualizer and
human-control frontend. This separation permits headless simulation, parallel
episodes, and repeatable experiments.

## Design constraints

- Preserve the original game behavior unless a documented training extension requires a change.
- Keep seeds, environment configuration, and agent hyperparameters serializable.
- Keep online networking separate from offline training.
- Treat Agent Smith as a baseline opponent, not as a training dependency.
- Keep PyTorch policy, rollout, GAE, loss, and optimizer tensors on CUDA; do
  not silently fall back to CPU.
