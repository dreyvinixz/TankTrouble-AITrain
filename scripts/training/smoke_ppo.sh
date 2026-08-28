#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
"$ROOT/scripts/training/verify_cuda.sh"
"$ROOT/scripts/training/build_native.sh"
"$ROOT/scripts/training/train_ppo.sh" config/training/ppo_smoke.yaml
