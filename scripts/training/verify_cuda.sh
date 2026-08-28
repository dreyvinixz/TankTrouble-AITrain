#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$ROOT/scripts/wsl_cuda_env.sh"
python - <<'PY'
import torch
if not torch.cuda.is_available():
    raise SystemExit("CUDA is required: PyTorch did not detect a GPU.")
print(f"CUDA OK: {torch.cuda.get_device_name(0)} | {torch.version.cuda}")
PY
