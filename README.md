# TankTrouble AI Train

> An independent AI-training prototype built on the TankTrouble game-client foundation.

TankTrouble AI Train is an original, independently maintained C++17 prototype by **dreyvinixz**. Its purpose is to turn the TankTrouble game loop into a reproducible environment for training and evaluating tank-control agents. The graphical client and gameplay baseline were imported from [JustDoIt0910/TankTrouble](https://github.com/JustDoIt0910/TankTrouble); that work remains clearly credited throughout this repository.

## Project identity and attribution

This is **not** an official TankTrouble project and is not affiliated with the original author. It is a derivative research and development prototype with its own roadmap, experiments, training code, documentation, and future AI agents.

| Area | Attribution |
| --- | --- |
| Original game-client foundation, core gameplay, GUI, and baseline Agent Smith AI | [JustDoIt0910/TankTrouble](https://github.com/JustDoIt0910/TankTrouble), copyright 2023 Zhao Rui. |
| AI-training environment, agent integrations, experiments, evaluation tooling, and project direction | TankTrouble AI Train contributors, starting with [dreyvinixz](https://github.com/dreyvinixz), copyright 2026. |

Please cite both this project and the original TankTrouble repository when using or building on this work. Machine-readable citation metadata is available in [CITATION.cff](CITATION.cff), and detailed notices are in [NOTICE.md](NOTICE.md).

## Current capabilities

- Local single-player matches against **Agent Smith**, the built-in rule-based tank AI.
- Online lobby and 2-, 3-, or 4-player rooms, provided that a compatible TankTrouble server is running.
- Random maze generation, tank movement, shell collisions, and ricochets.
- A GTKmm 3 graphical interface, now fully presented in English.

## Project layout

| Path | Purpose |
| --- | --- |
| `.github/` | Issue templates, pull-request checklist, and continuous integration. |
| `docs/` | Architecture, reproducibility guidance, and the public roadmap. |
| `src/app/` | Application entry point, application window, and GTKmm interface. |
| `src/game/` | Game domain, map, tanks, shells, controllers, events, and network protocol. |
| `src/core/` | Shared mathematical and identity primitives. |
| `src/ai/baselines/agent_smith/` | Attributed rule-based baseline opponent. |
| `src/training/` | Reserved for project-owned environment, agents, evaluation, and experiments. |
| `tests/` | Reserved for deterministic game and training-environment regression tests. |
| `third_party/ev/` | External event-driven networking submodule. |
| `res/` | Runtime assets used by the GTKmm client. |

The codebase is organized around TankTrouble AI Train's application, game, AI, and future-training boundaries. The imported code remains attributed, while new training work has its own dedicated namespace in the project tree. See the [architecture guide](docs/architecture.md).

## Build on Linux

The original client targets Linux and depends on GTKmm 3.

```bash
sudo apt-get install libgtkmm-3.0-dev cmake build-essential
git clone --recurse-submodules https://github.com/dreyvinixz/TankTrouble-AITrain.git
cd TankTrouble-AITrain
cmake -S . -B build
cmake --build build
./build/TankTroubleAITrain
```

If the repository has already been cloned without the submodule, initialize it with:

```bash
git submodule update --init --recursive
```

## Controls

Use the arrow keys to move and rotate the tank. Press `Space` to fire.

## Online mode

The online client connects to the server address currently hard-coded in `Window.cc`. Its protocol is compatible with the original [TankTroubleServer](https://github.com/JustDoIt0910/TankTroubleServer) project, but the original public server may not be available. Local single-player mode works without it.

## AI-training roadmap

The existing game loop and `smithAI/` opponent provide a useful baseline. Our next development stage is to expose an environment interface with observations, valid actions, rewards, episode reset, and deterministic seeds, then attach a trainable agent without coupling training code to the GTK interface.

Planned project-owned work:

- A headless, deterministic training environment.
- Observation, action, reward, and episode APIs.
- Trainable reinforcement-learning agents and reproducible experiments.
- Evaluation against Agent Smith and other baselines.

See the complete [public roadmap](docs/roadmap.md), [architecture guide](docs/architecture.md), and [reproducibility guide](docs/reproducibility.md).

## Contributing

Contributions, bug reports, and design proposals are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md), follow the [Code of Conduct](CODE_OF_CONDUCT.md), and use the GitHub issue templates for actionable reports.

## Security

Please report potential vulnerabilities according to [SECURITY.md](SECURITY.md). Do not include secrets, private credentials, or security-sensitive proof-of-concept details in public issues.

## Changelog

Notable public changes are tracked in [CHANGELOG.md](CHANGELOG.md).

## License

This project is released under the [MIT License](LICENSE). Copyright and attribution for the imported TankTrouble code are retained; the TankTrouble AI Train additions are also released under MIT.
