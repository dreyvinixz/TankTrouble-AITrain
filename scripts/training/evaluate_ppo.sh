#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$ROOT/scripts/wsl_cuda_env.sh"
python -m tanktrain.evaluate --checkpoint "${1:?Pass a checkpoint path}" --config "${2:-config/training/evaluation_v1.yaml}"
