# Architecture

## Current game-client foundation

The imported TankTrouble client keeps gameplay, rendering, and networking in separate components:

| Component | Responsibility |
| --- | --- |
| `view/` | GTKmm screens, keyboard input, lobby, and game rendering. |
| `controller/` | Local game loop and online-state coordination. |
| `smithAI/` | Existing rule-based opponent: evasion, pathfinding, targeting, and firing. |
| `event/` | Input actions passed from the interface to controllers. |
| `protocol/` | Client/server serialization for online mode. |
| `util/` | Geometry, vectors, collision checks, and identifiers. |

## AI-training boundary

New training features must not depend on GTKmm. The intended project-owned structure is:

```text
training/
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
