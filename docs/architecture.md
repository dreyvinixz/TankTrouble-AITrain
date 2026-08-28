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
  environment/  # Reset, step, observations, rewards, and terminal states
  agents/       # Trainable policies and baseline adapters
  evaluation/   # Metrics, match runners, and reproducible benchmarks
  config/       # Versioned experiment templates
tests/          # Deterministic environment and regression tests
```

The environment layer will call game-domain logic directly. GTKmm will remain an optional visualizer and human-control frontend. This separation permits headless simulation, parallel episodes, and repeatable experiments.

## Design constraints

- Preserve the original game behavior unless a documented training extension requires a change.
- Keep seeds, environment configuration, and agent hyperparameters serializable.
- Keep online networking separate from offline training.
- Treat Agent Smith as a baseline opponent, not as a training dependency.
