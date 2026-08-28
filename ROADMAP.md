# TankTrouble AI Train Roadmap

Status: active
Last update: 2026-08-28
Training target: CUDA PPO on Linux/WSL2

## Goal

Build a reproducible CUDA-first reinforcement-learning benchmark in which a
trainable tank policy competes against the attributed Agent Smith baseline.
The GTKmm client remains a human-facing visualizer; training runs headlessly.

## Phases

| Phase | Status | Objective |
| --- | --- | --- |
| 0. Project foundation | DONE | Import, attribute, translate, and reorganize the game foundation. |
| 1. CUDA bootstrap | IN PROGRESS | Reproducible WSL2 Python environment, CUDA verification, and GPU-only guardrails. |
| 2. Headless arena | IN PROGRESS | Deterministic reset/step simulation, seeded maze generation, actions, observations, and rewards. |
| 3. Python bridge | IN PROGRESS | pybind11 vector-environment module with NumPy batch I/O. |
| 4. CUDA PPO baseline | IN PROGRESS | PyTorch PPO policy, CUDA rollout/update path, checkpoints, and metrics. |
| 5. Benchmark protocol | BACKLOG | Five seeds, fixed held-out evaluation seeds, random baseline, and reports. |
| 6. GPU simulation | BACKLOG | Native CUDA vectorized stepping after the CPU arena baseline is validated. |
| 7. Research expansion | BACKLOG | Self-play, curriculum, ablations, learned opponents, and GUI replay. |

## Current executable targets

```bash
source scripts/wsl_cuda_env.sh
scripts/training/verify_cuda.sh
scripts/training/build_native.sh
scripts/training/train_ppo.sh config/training/ppo_v1.yaml
scripts/training/evaluate_ppo.sh checkpoints/<run>/policy.pt
```

## Completion gates

- [ ] CUDA guard rejects CPU-only execution.
- [ ] Same seed and actions reproduce the arena trace exactly.
- [ ] C++ action, collision, reward, and truncation tests pass.
- [ ] Native vector environment builds and passes Python shape tests.
- [ ] PPO smoke run completes on CUDA within 4 GB VRAM.
- [ ] Five-seed PPO benchmark is evaluated against held-out Agent Smith arenas.

## Data and artifact policy

Version control contains source code, test fixtures, and experiment
configuration only. Checkpoints, TensorBoard files, logs, videos, and result
tables are generated locally under ignored directories. Each run records its
configuration, Git revision, random seed, and GPU metadata.
