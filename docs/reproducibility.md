# Reproducibility

## Build environment

The client currently targets Linux with C++17, CMake, GTKmm 3, and the `ev` submodule.

```bash
sudo apt-get install libgtkmm-3.0-dev cmake build-essential
git clone --recurse-submodules https://github.com/dreyvinixz/TankTrouble-AITrain.git
cd TankTrouble-AITrain
cmake -S . -B build
cmake --build build
```

## Training experiments

Training code is not implemented yet. When it is added, every result should record:

- Git commit identifier and submodule revision.
- Environment configuration and random seed.
- Agent architecture, hyperparameters, and training budget.
- Evaluation opponents, number of episodes, and metrics.

Generated data, model checkpoints, videos, and logs belong in ignored directories such as `outputs/`, `runs/`, `checkpoints/`, and `logs/`. Version control should contain configurations and scripts needed to regenerate them, not the generated artefacts themselves.
