"""Runtime and reproducibility helpers for CUDA-only training."""

from __future__ import annotations

import json
import random
import subprocess
from pathlib import Path
from typing import Any

import torch
import yaml


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def require_cuda() -> torch.device:
    if not torch.cuda.is_available():
        raise RuntimeError(
            "TankTrouble AI Train requires CUDA. Refusing to train on CPU; "
            "source scripts/wsl_cuda_env.sh and verify the WSL GPU environment."
        )
    return torch.device("cuda")


def seed_everything(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def load_yaml(path: str | Path) -> dict[str, Any]:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = repository_root() / candidate
    with candidate.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def git_revision() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repository_root(), text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")
