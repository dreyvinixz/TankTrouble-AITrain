#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$ROOT/scripts/wsl_cuda_env.sh"
cmake -S "$ROOT" -B "$ROOT/build" -DTANKTRAIN_BUILD_PYTHON_BINDINGS=ON -Dpybind11_DIR="$(python -m pybind11 --cmakedir)" -DCMAKE_BUILD_TYPE=Release
cmake --build "$ROOT/build" --target tanktrain_env --parallel
