# CUDA Training on WSL2

TankTrouble AI Train runs its first PPO baseline on Linux under WSL2. The
headless C++ arena is CPU-based by design in v1; PyTorch policy inference,
rollouts, advantages, losses, and optimizer updates are CUDA-only. A missing
GPU is a configuration error, never a reason to fall back to CPU training.

## Hardware baseline

The current machine exposes an NVIDIA GTX 1650 Max-Q with 4 GB VRAM to WSL2.
The default settings in `config/training/ppo_v1.yaml` use a 2×256 MLP, 32
arenas, 128-step rollouts, and 512-sample GPU minibatches to fit that budget.

## First-time setup

For training performance, clone or work from a Linux-native path such as
`~/projects/TankTrouble-AITrain`, not a Windows-mounted path.

```bash
sudo apt-get install build-essential cmake pkg-config libgtkmm-3.0-dev
git submodule update --init --recursive
bash scripts/training/bootstrap_wsl.sh
source scripts/wsl_cuda_env.sh
bash scripts/training/verify_cuda.sh
bash scripts/training/build_native.sh
```

The bootstrap script creates `.venv-wsl` with Python 3.12 and installs the
CUDA PyTorch wheel, NumPy, PyYAML, and pybind11. It does not install NVIDIA
drivers. `nvidia-smi` must already work inside WSL2.

## Training and evaluation

```bash
bash scripts/training/smoke_ppo.sh
bash scripts/training/train_ppo.sh config/training/ppo_v1.yaml
bash scripts/training/evaluate_ppo.sh runs/<run>/policy_02000.pt
```

Each run writes metadata, metrics, and checkpoints below `runs/`. Evaluation
writes the most recent report under `outputs/evaluation/`. These locations are
ignored by Git and must be regenerated from versioned configuration.

## Native module checks

After building the bridge, run:

```bash
PYTHONPATH="$PWD/python:$PWD/build" python -m unittest python/tests/test_vector_environment.py
```

The test covers shape, finite-reward, terminal/truncation, and deterministic
seed contracts.
