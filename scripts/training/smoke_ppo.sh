#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
bash "$ROOT/scripts/training/verify_cuda.sh"
bash "$ROOT/scripts/training/build_native.sh"
bash "$ROOT/scripts/training/train_ppo.sh" config/training/ppo_smoke.yaml
