# TankTrouble AI Train

An English-language C++17 TankTrouble client used as the graphical-game foundation for future tank-AI training experiments.

This repository was imported from [JustDoIt0910/TankTrouble](https://github.com/JustDoIt0910/TankTrouble). It preserves the original MIT license and retains the original gameplay and networking code as the starting point for this project.

## Current capabilities

- Local single-player matches against **Agent Smith**, the built-in rule-based tank AI.
- Online lobby and 2-, 3-, or 4-player rooms, provided that a compatible TankTrouble server is running.
- Random maze generation, tank movement, shell collisions, and ricochets.
- A GTKmm 3 graphical interface, now fully presented in English.

## Project layout

| Path | Purpose |
| --- | --- |
| `view/` | GTKmm screens and reusable GUI components. |
| `controller/` | Local game loop and online client controller. |
| `smithAI/` | The current opponent AI: evasion, A* pathfinding, targeting, and firing. |
| `event/` | Player-control events. |
| `protocol/` | Client/server message codec. |
| `util/` | Vectors, geometry, collision detection, and IDs. |
| `ev/` | Git submodule containing the event-driven networking library. |

## Build on Linux

The original client targets Linux and depends on GTKmm 3.

```bash
sudo apt-get install libgtkmm-3.0-dev cmake build-essential
git clone --recurse-submodules https://github.com/dreyvinixz/TankTrouble-AITrain.git
cd TankTrouble-AITrain
cmake -S . -B build
cmake --build build
./build/TankTrouble
```

If the repository has already been cloned without the submodule, initialize it with:

```bash
git submodule update --init --recursive
```

## Controls

Use the arrow keys to move and rotate the tank. Press `Space` to fire.

## Online mode

The online client connects to the server address currently hard-coded in `Window.cc`. Its protocol is compatible with the original [TankTroubleServer](https://github.com/JustDoIt0910/TankTroubleServer) project, but the original public server may not be available. Local single-player mode works without it.

## AI-training direction

The existing game loop and `smithAI/` opponent provide a useful baseline. The next development stage is to expose an environment interface with observations, valid actions, rewards, episode reset, and deterministic seeds, then attach a trainable agent without coupling training code to the GTK interface.

## License

This project is released under the [MIT License](LICENSE). Copyright attribution for the imported code is retained.
