#!/usr/bin/env bash
# Source from WSL2 before CUDA PPO commands.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$ROOT/.venv-wsl"

if [[ ! -d "$VENV" ]]; then
  echo "Missing $VENV. Create it with Python 3.12 before training." >&2
  return 1 2>/dev/null || exit 1
fi

export PATH="/usr/local/cuda/bin:${PATH}"
export LD_LIBRARY_PATH="/usr/lib/wsl/lib:/usr/local/cuda/targets/x86_64-linux/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
export PYTHONPATH="$ROOT/python:$ROOT/build${PYTHONPATH:+:${PYTHONPATH}}"
export TANKTRAIN_DEVICE="cuda"

source "$VENV/bin/activate"
