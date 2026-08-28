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
| 4. CUDA PPO baseline (V1) | DONE | PyTorch PPO policy, CUDA rollout/update path, checkpoints, and metrics logging. |
| 4.1 Arena V2 (Realistic Physics) | DONE | Symmetric ricochet self-hit/friendly fire, continuous Smith AI (170px range, 30 ticks cooldown), draw=0.0, timeout=-0.20, and survival=0.0. |
| 4.2 Arena V3 (Egocentric Navigation & Curriculum) | IN PROGRESS | 8-ray relative Lidar sensors (384-d obs), anti-stall & wall-bump telemetry, ablation studies (V3-A 384-d vs V3-B 76-d), and progressive Smith curriculum. |
| 5. Benchmark protocol | BACKLOG | Multi-seed benchmark runs, fixed held-out evaluation seeds, and comparative analysis reports. |
| 6. Live Dashboard & Visualizer | DONE (v1.0) | Real-time WebSocket telemetry, OLED Full Black UI, 1-Click Trainer, neural activations inspector, and 2D arena visualizer (60 FPS LERP in backlog). |
| 7. GPU simulation & Research | BACKLOG | Native CUDA vectorized stepping, self-play, learned opponents, and GUI replay. |

---

## Arena V3 Specification (Egocentric Lidar & Navigation)

1. **Egocentric 8-Ray Lidar Sensor**:
   - 8 rays relative to tank heading ($\theta_{ray} = \theta_{tank} + \Delta\theta$):
     - `0°`: Front
     - `45°`: Front-Left
     - `90°`: Left
     - `135°`: Back-Left
     - `180°`: Back
     - `225°`: Back-Right
     - `270°`: Right
     - `315°`: Front-Right
   - Geometric ray-segment intersection against horizontal/vertical maze walls.
   - Max distance: $180\text{px}$ (3 cells), normalized to $[0.0, 1.0]$ with `Tanh` compatibility.
2. **Observation Vector (384-d)**:
   - `0..5`: Player tank state (6)
   - `6..11`: Opponent tank state (6)
   - `12..67`: Shells ordered by proximity ($8 \times 7 = 56$, includes owner $\pm 1.0$)
   - `68..375`: Maze topology ($77 \times 4 = 308$)
   - `376..383`: Wall Lidar ($8$)
3. **Anti-Stall & Exploration Telemetry**:
   - Tracking `stationary_ratio`, `wall_bump_rate`, `distance_traveled_mean`, and `unique_cells_visited`.
4. **Curriculum Learning Stages**:
   - Stage 1: Exploration & Navigation (Smith fire disabled)
   - Stage 2: Easy Combat (Smith fire cooldown 120 ticks, range 150px)
   - Stage 3: Medium Combat (Smith fire cooldown 60 ticks, range 170px)
   - Stage 4: Full Arena (Full Agent Smith cooldown 30 ticks, range 170px)

---

## Current executable targets

```bash
source scripts/wsl_cuda_env.sh
scripts/training/verify_cuda.sh
scripts/training/build_native.sh
scripts/training/train_ppo.sh config/training/ppo_v3.yaml
scripts/training/evaluate_ppo.sh checkpoints/<run>/policy.pt
```

## Completion gates

- [x] CUDA guard rejects CPU-only execution.
- [x] Same seed and actions reproduce the arena trace exactly.
- [x] C++ action, collision, reward, timeout, and friendly fire tests pass.
- [x] Native vector environment builds and passes Python shape tests.
- [x] PPO baseline runs on CUDA within 4 GB VRAM (GTX 1650 Max-Q).
- [x] Live training telemetry dashboard with OLED Full Black theme and 1-Click Trainer.
- [ ] 8-ray egocentric wall Lidar implemented with C++ geometric intersection.
- [ ] 384-feature observation vector verified in C++, pybind11, and Python.
- [ ] Neural Inspector visualizes 8-ray Lidar activations and maze topology.
- [ ] V3-A (384-d) vs V3-B (76-d) ablation benchmark evaluated against held-out Agent Smith arenas.
