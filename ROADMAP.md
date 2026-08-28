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
| 1. CUDA bootstrap | DONE | Reproducible WSL2 Python environment, CUDA verification, and GPU-only guardrails. |
| 2. Headless arena & Perf | DONE | Deterministic reset/step simulation, seeded maze generation, actions, observations, rewards, and test runner. |
| 3. Python bridge | DONE | pybind11 vector-environment module with NumPy batch I/O and contract tests. |
| 4. CUDA PPO baseline | IN PROGRESS | PyTorch PPO policy, CUDA rollout/update path, checkpoints, and metrics logging. |
| 5. Benchmark protocol | BACKLOG | Five seeds, fixed held-out evaluation seeds, random baseline, and experiment reports. |
| 6. Live Dashboard & Visualizer | BACKLOG | Real-time telemetry, reward curves, GPU monitor, neural activation graph, and best-tank replay. |
| 7. GPU simulation & Research | BACKLOG | Native CUDA vectorized stepping, self-play, curriculum, learned opponents, and GUI replay. |

## Live Training Dashboard & Neural Visualizer

Interactive telemetry HUD and visualizer adapted for TankTrouble reinforcement learning:

- **Real-Time Telemetry & Progress**: Epochs, total environment steps, training duration, win-rate against baseline, and action distributions.
- **Dynamic Reward & Loss Charts**: Live plotting of mean/max episodic reward, policy loss, value loss, and entropy.
- **Hardware Monitor**: GPU device utilization, allocated/reserved VRAM (GTX 1650 4 GB footprint), and throughput (steps/sec).
- **Neural Network Activation Graph**: Interactive visual inspection of the Actor-Critic network (74 observation input features $\to$ hidden layer activations $\to$ discrete actions: Move, Rotate, Shoot).
- **Best Tank Live Replay**: Real-time canvas/window replay rendering the highest-fitness episode in the generated maze with bouncing projectile trajectories.

## Current executable targets

```bash
source scripts/wsl_cuda_env.sh
scripts/training/verify_cuda.sh
scripts/training/build_native.sh
scripts/training/train_ppo.sh config/training/ppo_v1.yaml
scripts/training/evaluate_ppo.sh checkpoints/<run>/policy.pt
```

## Completion gates

- [x] CUDA guard rejects CPU-only execution.
- [x] Same seed and actions reproduce the arena trace exactly.
- [x] C++ action, collision, reward, and truncation tests pass.
- [x] Native vector environment builds and passes Python shape tests.
- [x] PPO smoke run completes on CUDA within 4 GB VRAM.
- [ ] Live training telemetry dashboard with real-time charts and GPU monitor.
- [ ] Neural activation graph visualizing Actor-Critic decision flow.
- [ ] Five-seed PPO benchmark is evaluated against held-out Agent Smith arenas.

## Data and artifact policy

Version control contains source code, test fixtures, and experiment
configuration only. Checkpoints, TensorBoard files, logs, videos, and result
tables are generated locally under ignored directories. Each run records its
configuration, Git revision, random seed, and GPU metadata.
