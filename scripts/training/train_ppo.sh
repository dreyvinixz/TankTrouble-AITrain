#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$ROOT/scripts/wsl_cuda_env.sh"
python -m tanktrain.train --config "${1:-config/training/ppo_v1.yaml}"
