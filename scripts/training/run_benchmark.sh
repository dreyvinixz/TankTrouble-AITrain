#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$ROOT/scripts/wsl_cuda_env.sh"
bash "$ROOT/scripts/training/build_native.sh"
python -m tanktrain.benchmark --config "${1:-config/training/benchmark_v1.yaml}"
