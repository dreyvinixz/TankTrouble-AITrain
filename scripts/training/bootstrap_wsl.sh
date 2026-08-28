#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

# WSL commonly mounts /tmp as a small tmpfs. CUDA wheels need several GB while
# unpacking, so keep pip's temporary files on the Linux filesystem instead.
export TMPDIR="${TMPDIR:-$HOME/.cache/tanktrain-tmp}"
mkdir -p "$TMPDIR"

for command in cmake g++ pkg-config; do
  if ! command -v "$command" >/dev/null 2>&1; then
    echo "Missing $command. Install build prerequisites:" >&2
    echo "  sudo apt-get install build-essential cmake pkg-config libgtkmm-3.0-dev" >&2
    exit 1
  fi
done
if ! pkg-config --exists gtkmm-3.0; then
  echo "Missing GTKmm 3 development files. Install libgtkmm-3.0-dev." >&2
  exit 1
fi

if command -v uv >/dev/null 2>&1; then
  uv venv --allow-existing --seed --python 3.12 .venv-wsl
elif command -v python3.12 >/dev/null 2>&1; then
  python3.12 -m venv .venv-wsl
else
  echo "Install uv or Python 3.12 before creating the training environment." >&2
  exit 1
fi
source .venv-wsl/bin/activate
if ! python -m pip --version >/dev/null 2>&1; then
  python -m ensurepip --upgrade
fi
python -m pip install --upgrade pip
python -m pip install --index-url https://download.pytorch.org/whl/cu126 torch
python -m pip install -r python/requirements-cuda.txt
python -m pip install -e python
echo "Environment created. Next: source scripts/wsl_cuda_env.sh && scripts/training/verify_cuda.sh"
