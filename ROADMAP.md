# TankTrouble AI Train Roadmap

Status: active  
Last update: 2026-08-28  
Training target: CUDA PPO & Neuroevolution on Linux/WSL2  

---

## 🎯 Goal

Build a reproducible, high-throughput CUDA-first reinforcement learning and neuroevolution benchmark in which autonomous tank agents master spatial navigation, tactical evasion, ballistic aiming, and ricochet trajectories against the deterministic baseline (Agent Smith), genetic populations, and self-play opponents.

The GTKmm client remains a human-facing visualizer; training and benchmarking run headlessly at thousands of steps per second on GPU.

---

## 🧭 Project Phases Overview

| Phase | Status | Objective |
| :--- | :---: | :--- |
| **0. Project foundation** | **DONE** | Import, attribute, translate, and reorganize the game foundation. |
| **1. CUDA bootstrap** | **DONE** | Reproducible WSL2 Python environment, CUDA verification, and GPU-only guardrails. |
| **2. Headless arena & Perf** | **DONE** | Deterministic reset/step simulation, seeded maze generation, actions, observations, rewards, and CTest suite. |
| **3. Python bridge** | **DONE** | pybind11 vector-environment module (`tanktrain_env`) with NumPy batch I/O and contract tests. |
| **4. CUDA PPO baseline (V1)** | **DONE** | PyTorch PPO policy, CUDA rollout/update path, checkpoints, and metrics logging. |
| **4.1 Arena V2 (Realistic Physics)** | **DONE** | Symmetric friendly fire / self-hit, continuous Smith AI (170px range, 30 ticks cooldown), draw=0.0, timeout=-0.20, survival=0.0. |
| **4.2 Arena V3 (Egocentric Lidar)** | **DONE** | 8-ray relative Lidar sensors (384-d obs), explicit `TerminationCause` enums, 4-frame temporal stacking (1536-d). |
| **4.3 Arena V4 (Unified Intelligence Benchmark)** | **IN PROGRESS** | Perspective-neutral arena, collision-aware 16-ray Lidar, Genetic baseline, BFS waypoint guidance, Behavior Cloning, and dual-ranking protocol. |
| **5. Benchmark protocol** | **BACKLOG** | Multi-seed benchmark runs, 500 held-out test seeds, paired bootstrap 95% CI, and tournament reports. |
| **6. Live Dashboard & Visualizer** | **DONE (v1.0)** | Real-time WebSocket telemetry, OLED Full Black UI, 1-Click Trainer, neural activations inspector, and 2D arena visualizer (60 FPS LERP in backlog). |
| **7. Arena V5 (Self-Play & Population Elo)** | **BACKLOG** | Native CUDA vectorized stepping, opponent pool, self-play, population-based training, and true Elo leaderboard. |

---

# 🚀 Arena V4: Unified Egocentric Intelligence Benchmark

## 1. Core Mission & Philosophy

> **Arena V4 transforms the project from single-agent model training into a rigorous, unified Reinforcement Learning and Neuroevolution benchmark.**

It eliminates experimental confounding factors:
1. **Fair Algorithm Comparison:** PPO Tabula Rasa vs Genetic Tabula Rasa are evaluated under identical perceptions, rewards, action masks, and environment step budgets.
2. **System-Level Showdown:** Genetic Champion vs Educated PPO (BC + Curriculum) vs Agent Smith.
3. **No Hidden Privileged Information:** BFS navigation is an explicit, isolated ablation variable (`V4-Local` vs `V4-Guided`), never quietly mixed into raw perception.
4. **Zero Survival Reward Hacking:** Navigation progress is rewarded via Potential-Based Geodesic Shaping $\Phi(s)$, preventing stationary camping.

```text
                         TANK ARENA V4
                              │
                 Perspective-Neutral Observation API
                              │
        ┌─────────────────────┴─────────────────────┐
        │                                           │
     GENETIC                                      PPO
  Neuroevolution                         ┌───────────┴───────────┐
  Tabula Rasa                            │                       │
                                        PPO                 BC → PPO
                                     Tabula Rasa           Educated PPO
        │                                │                       │
        └────────────────────┬───────────┴───────────────────────┘
                             │
                       BENCHMARK V4
                             │
        Genetic vs PPO vs BC-PPO vs Agent Smith Showdown
```

---

## 2. Detailed Technical Specifications

### Phase 0 — Version Freezing & Metadata Integrity
* Retain `environment_v1/v2/v3.yaml` and `ppo_v1/v2/v3.yaml` as immutable baselines.
* Create dedicated `config/training/environment_v4.yaml`, `config/training/ppo_v4.yaml`, and `config/training/genetic_v4.yaml`.
* Embed explicit metadata in all saved checkpoints:
  ```json
  {
    "arena_version": 4,
    "observation_schema": "egocentric_v4",
    "git_commit": "...",
    "training_seed": 42
  }
  ```
* Incompatible checkpoints fail fast with descriptive validation errors.

---

### Phase 1 — Dual-Controller Independent Arena (PPO vs Genetic / PPO vs PPO)
Decouple `TankArena::step()` from hardcoded Agent Smith:
```cpp
enum class OpponentMode : uint8_t
{
    AgentSmith = 0,
    Passive = 1,
    Random = 2,
    External = 3
};

// Backward compatible single-agent step
StepResult step(const TankAction& playerAction);

// Full symmetric multi-agent step
std::pair<StepResult, StepResult> step(const TankAction& playerAction, const TankAction& opponentAction);
```

---

### Phase 2 — Perspective-Neutral Observation Schema
Observations are invariant to tank role (Tank 0 vs Tank 1):
```cpp
std::vector<float> observationFor(int observerOwner) const;
```
* `self`: The observing tank (position, angle, ammo, velocity).
* `enemy`: The opponent tank from `self`'s point of view.
* `shell_owner`: `+1.0` for own shells, `-1.0` for enemy shells.
* Any agent (PPO or Genetic) can control either tank slot with zero model changes.

---

### Phase 3 — Collision-Aware 16-Ray Lidar Sensor
Instead of raycasts from a zero-width point, compute the **Minkowski Sum** of maze walls inflated by tank radius ($Wall \oplus R_{tank}$). Each ray measures the exact clearance distance the tank center can travel before physical collision occurs.

**16-Ray Asymmetric Angular Layout (Front-Focused Resolution):**
```text
           -55° -35° -20° -10°  0°  +10° +20° +35° +55°
                     \          |          /
                      \         |         /
                            [ TANK ]
                      /         |         \
                     /          |          \
                 -160° -120°  -80° 180° +80° +120° +160°
```
* Frontal arc: $0^\circ, \pm 10^\circ, \pm 20^\circ, \pm 35^\circ, \pm 55^\circ$
* Lateral & Rear arc: $\pm 80^\circ, \pm 120^\circ, \pm 160^\circ, 180^\circ$
* Max distance: $180\text{px}$ (3 cells), normalized to $[0.0, 1.0]$.

---

### Phase 4 — Egocentric Opponent Perception
Replaces raw Cartesian global coordinates with actionable polar relative features:
* `enemy_distance`: Normalized distance to opponent ($\le 1.0$).
* `enemy_bearing_sin`, `enemy_bearing_cos`: Relative angle towards enemy center.
* `enemy_heading_relative_sin`, `enemy_heading_relative_cos`: Enemy orientation relative to own heading.
* `enemy_ammo`: Opponent available shells ($0..5 / 5.0$).
* `enemy_line_of_sight`: Boolean flag ($1.0 / 0.0$) if an unobstructed line of sight exists.
* `enemy_in_direct_fire_range`: Boolean flag ($1.0 / 0.0$) if distance $\le 170\text{px}$ and LOS exists.

---

### Phase 5 — Egocentric Projectile Perception
For the closest 8 shells ordered by Euclidean proximity:
* `distance`: Relative distance from tank center.
* `bearing_sin`, `bearing_cos`: Relative bearing angle.
* `trajectory_relative_sin`, `trajectory_relative_cos`: Movement vector relative to tank heading.
* `owner`: `+1.0` (friendly / self) vs `-1.0` (hostile / opponent).
* `ttl`: Time to live ($0..180 / 180.0$).
* `active`: Active shell indicator ($1.0 / 0.0$).

---

### Phase 6 — Optional BFS Waypoint Guidance (Ablation Benchmark)
To measure the exact value of explicit graph planning vs pure reactive perception:
* **V4-Local (Standard):** 16 Lidar rays + Egocentric Enemy + Egocentric Shells (no BFS hints).
* **V4-Guided (With Waypoint):** Adds:
  * `waypoint_bearing_sin`, `waypoint_bearing_cos`: Relative angle to next optimal maze corridor cell.
  * `waypoint_distance`: Distance to center of next waypoint cell.
  * `geodesic_distance_to_enemy`: Shortest topological path length in cells.

---

### Phase 7 & 8 — Action Masking & Progressive Ricochet Unlocking
* **Mask 1 (Ammo Conservation):** If `ammo == 0`, action `FIRE` is masked out (probability forced to 0).
* **Mask 2 (Direct Combat Scaffolding):** During early training stages, `FIRE` is allowed only when `enemy_line_of_sight == true` and `enemy_distance <= direct_fire_range`. Angular aiming remains an unmasked learned motor skill.
* **Stage 6 (Ricochet Mastery):** LOS fire mask is removed (`require_los_to_fire: false`), unlocking indirect ricochet trick-shots.

---

### Phase 9 — Potential-Based Geodesic Reward Shaping
To guide navigation without inducing passive camping or reward hacking:
$$\Phi(s) = -\frac{d_{geo}(self, enemy)}{d_{max}}$$
$$F(s, s') = \beta \cdot \left[ \gamma \Phi(s') - \Phi(s) \right], \quad \beta \in [0.05, 0.10]$$
* Moving 1 cell closer to opponent $\implies$ positive shaping bonus ($+0.05$).
* Moving away $\implies$ small negative feedback.
* Stationary camping $\implies 0.0$ bonus.

---

### Phase 10 to 12 — Genetic Tank Baseline (Neuroevolution)
* **Architecture:** Compact MLP (`Obs -> 64 -> 64 -> Actions`) with MultiDiscrete heads.
* **Population:** $N = 256$ (or $512$), Elite fraction $= 5\%$.
* **Selection:** Top $5\%$ elites preserved directly; remaining slots filled via tournament selection ($k=4$).
* **Mutation:** Additive Gaussian noise $\epsilon \sim \mathcal{N}(0, \sigma^2)$ with generation decay ($\sigma_{0} = 0.10 \to \sigma_{end} = 0.02$).
* **Common Random Numbers (CRN):** All 256 genomes within a generation play the exact same batch of arena seeds to ensure zero variance from maze difficulty luck.
* **Fair Fitness:** Evaluated on the exact same cumulative reward function ($R_{terminal} + R_{potential}$) as PPO.

---

### Phase 13 to 16 — PPO Tabula Rasa vs Behavior Cloning (BC-PPO)
* **PPO Tabula Rasa:** Trains from scratch on identical environment configurations.
* **Expert Demonstrations:** Generated via C++ BFS navigation controller across 50,000 states (partitioned strictly by unique maze seeds).
* **Supervised Pretraining:** Cross-entropy loss on demonstration actions for movement and rotation.
* **Curriculum Fine-Tuning:** PPO continues training from the BC checkpoint with PPO policy loss.

---

### Phase 17 — 7-Stage Curriculum Protocol

```text
[Stage 0: BC Pretrain]   --> BFS expert imitation (motor navigation)
           ↓
[Stage 1: Reach Target]  --> Smith static, no firing. Objective: reach opponent cell.
           ↓
[Stage 2: Active Chase]  --> Smith navigates without firing. PPO chases opponent.
           ↓
[Stage 3: Direct Combat Easy]   --> Smith cooldown 120 ticks, LOS fire mask ON.
           ↓
[Stage 4: Direct Combat Med]    --> Smith cooldown 60 ticks, LOS fire mask ON.
           ↓
[Stage 5: Direct Combat Full]   --> Full Agent Smith (cooldown 30 ticks), LOS fire mask ON.
           ↓
[Stage 6: Ricochet Mastery]     --> Full Arena, LOS fire mask OFF (Indirect trickshots).
```

---

### Phase 18 to 20 — Advanced Navigation & Combat Telemetry

#### Navigation Metrics
* $\text{Path Efficiency} = \frac{\text{Shortest Path Length}}{\text{Actual Traveled Path Length}} \in [0.0, 1.0]$
* $\text{Wall Bumps per 100 Decisions} = \frac{\text{Wall Collisions}}{\text{Decisions}} \times 100$
* $\text{Stationary Ratio} = \frac{\text{Decisions with Zero Displacement}}{\text{Total Decisions}}$
* $\text{Geodesic Progress} = d_{geo}(start) - d_{geo}(end)$
* $\text{Unique Cells Visited} / 77$

#### Combat Metrics
* $\text{Accuracy} = \frac{\text{Shots Hit Enemy}}{\text{Total Shots Fired}}$
* $\text{Direct Kills} \text{ vs } \text{Ricochet Kills}$
* $\text{Ricochet Mastery Rate} = \frac{\text{Ricochet Kills}}{\text{Total Kills}}$
* $\text{Self-Hit Rate} = \frac{\text{Suicides}}{\text{Completed Episodes}}$
* $\text{Timeouts} = \frac{\text{Truncated Episodes}}{\text{Completed Episodes}}$

---

### Phase 21 — Dual-Ranking Evaluation Protocol

#### Benchmark A: Fair Optimizer Comparison
| Protocol Variable | Genetic Tabula Rasa | PPO Tabula Rasa |
| :--- | :---: | :---: |
| **Observation Schema** | V4-Local (16-Ray) | V4-Local (16-Ray) |
| **Reward Function** | $R_{term} + R_{potential}$ | $R_{term} + R_{potential}$ |
| **Environment Budget** | 10,000,000 steps | 10,000,000 steps |
| **Evaluation Seeds** | 500 fixed test seeds | 500 fixed test seeds |
| **Question Answered** | *Which optimization algorithm is superior under tabula rasa conditions?* |

#### Benchmark B: Best System Showdown
| Participant | Paradigm | Training Method |
| :--- | :--- | :--- |
| **Genetic Champion** | Evolutionary | Selection + Gaussian Mutation |
| **Educated PPO** | Hybrid RL | Behavior Cloning $\to$ 7-Stage Curriculum |
| **Agent Smith** | Algorithmic | C++ BFS Pathfinding + Heuristic Dodge |
| **Question Answered** | *Which holistic design pipeline produces the ultimate combat tank?* |

---

### Phase 22 — Ablation Study Matrix

| ID | Agent | Sensors | BFS Waypoint | BC Pretraining | Experimental Question |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **A** | PPO | 16-Ray Lidar | ❌ | ❌ | Reactive baseline |
| **B** | PPO | 16-Ray Lidar | ✅ | ❌ | Impact of topological waypoint |
| **C** | PPO | 16-Ray Lidar | ✅ | ✅ | Impact of expert demonstration |
| **D** | Genetic | 16-Ray Lidar | ❌ | ❌ | Genetic reactive baseline |
| **E** | Genetic | 16-Ray Lidar | ✅ | ❌ | Genetic guided baseline |

---

### Phase 26 — Dashboard V4 Real-Time Visualizer
* **Sensor Radar View:** Interactive HUD rendering all 16 Lidar clearance rays, color-coded line-of-sight vector (Green = Free shot, Red = Blocked by wall), and target waypoint.
* **Combat & Navigation HUD:** Live tracking of Path Efficiency, Accuracy %, Ricochet Kills, and Wall Bumps.
* **Dual-Agent Matchup Mode:** Side-by-side telemetry for PPO vs Genetic showdowns.

---

## 🏆 Arena V4 Quality & Completion Gates

- [ ] **Gate 1 (Perspective Neutrality):** `observationFor(0)` and `observationFor(1)` produce symmetric inputs verified by unit tests.
- [ ] **Gate 2 (Dual Controller):** `OpponentMode::External` runs 2 separate policies simultaneously in C++ and Python.
- [ ] **Gate 3 (Collision Lidar):** 16-ray Minkowski Lidar passes geometric clearance test suite.
- [ ] **Gate 4 (Navigation Mastery):** Trained agents achieve $\text{Wall Bumps} < 10 / 100\text{ steps}$ and $\text{Stationary Ratio} < 20\%$.
- [ ] **Gate 5 (Genetic Benchmark):** Genetic population demonstrates monotonic fitness convergence over 100 generations on Common Random Numbers.
- [ ] **Gate 6 (Statistically Significant Showdown):** Final evaluation computed over 500 held-out test seeds with 95% bootstrap confidence intervals.

---

## 🛠️ Ordered 18-Step Implementation Plan

```text
 1. refactor(arena): perspective-neutral observationFor(observerOwner) API
 2. feat(arena): add OpponentMode::External and dual-agent step()
 3. feat(lidar): implement 16-ray collision-aware Minkowski sum clearance
 4. feat(perception): implement egocentric opponent features (distance, bearing, LOS)
 5. feat(perception): implement egocentric projectile features (trajectory vector, owner)
 6. feat(navigation): add optional BFS waypoint and geodesic distance features
 7. feat(policy): implement discrete action masking (ammo mask & LOS direct fire mask)
 8. feat(reward): implement potential-based geodesic distance shaping
 9. feat(metrics): implement path efficiency, wall bumps, and combat telemetry
10. feat(ppo): train V4 PPO Tabula Rasa baseline
11. feat(genetic): implement CUDA/PyTorch neuroevolution population trainer
12. feat(benchmark): run Benchmark A (PPO Tabula Rasa vs Genetic Tabula Rasa)
13. feat(expert): extract C++ BFS demonstration recorder
14. feat(dataset): generate 50k-state maze demonstration dataset
15. feat(imitation): implement Behavior Cloning supervised pretraining
16. feat(curriculum): execute 7-stage PPO fine-tuning curriculum
17. feat(showdown): execute Benchmark B tournament (Genetic vs PPO vs Smith)
18. feat(dashboard): deploy Sensor Radar View and dual-agent live stream
```

---

## 🔮 Horizon: Arena V5 (Self-Play & Population Elo)
* **Opponent Pool:** Historic checkpoint preservation for round-robin evaluation.
* **Self-Play Training:** PPO co-training against previous checkpoint versions.
* **Population Elo Rating:** True matchmaking rating calculating skill progression over millions of game steps.
