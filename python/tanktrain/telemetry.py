"""Real-time training telemetry, GPU performance monitoring, and state serialization."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import torch

# Try importing pynvml for zero-subprocess GPU metrics
try:
    import pynvml

    pynvml.nvmlInit()
    _PYNVML_AVAILABLE = True
except Exception:
    _PYNVML_AVAILABLE = False


@dataclass
class GpuMetrics:
    device_name: str = "Unknown"
    cuda_available: bool = False
    vram_allocated_mb: float = 0.0
    vram_reserved_mb: float = 0.0
    vram_total_mb: float = 0.0
    vram_percent: float = 0.0
    gpu_utilization_percent: float = 0.0
    temperature_c: float = 0.0
    power_w: float = 0.0


def collect_gpu_metrics(device_index: int = 0) -> GpuMetrics:
    metrics = GpuMetrics()
    if not torch.cuda.is_available():
        return metrics

    metrics.cuda_available = True
    metrics.device_name = torch.cuda.get_device_name(device_index)
    metrics.vram_allocated_mb = round(torch.cuda.memory_allocated(device_index) / (1024 * 1024), 2)
    metrics.vram_reserved_mb = round(torch.cuda.memory_reserved(device_index) / (1024 * 1024), 2)

    total_bytes = torch.cuda.get_device_properties(device_index).total_memory
    metrics.vram_total_mb = round(total_bytes / (1024 * 1024), 2)
    if metrics.vram_total_mb > 0:
        metrics.vram_percent = round((metrics.vram_allocated_mb / metrics.vram_total_mb) * 100, 1)

    if _PYNVML_AVAILABLE:
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(device_index)
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            metrics.gpu_utilization_percent = float(util.gpu)
            metrics.temperature_c = float(pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU))
            try:
                metrics.power_w = round(pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0, 1)
            except Exception:
                metrics.power_w = 0.0
        except Exception:
            pass

    return metrics


@dataclass
class NeuralActivationSnapshot:
    input_groups: dict[str, list[float]] = field(default_factory=dict)
    hidden_activations: list[dict[str, float]] = field(default_factory=list)
    action_probabilities: dict[str, list[float]] = field(default_factory=dict)
    predicted_value: float = 0.0


@dataclass
class TrainingProgress:
    status: str = "preparing"  # preparing, training, evaluating, paused, completed, error
    run_name: str = ""
    start_time: float = field(default_factory=time.time)
    elapsed_seconds: float = 0.0
    eta_seconds: float = 0.0
    current_update: int = 0
    total_updates: int = 0
    progress_percent: float = 0.0
    total_timesteps: int = 0
    steps_per_second: float = 0.0
    updates_per_second: float = 0.0
    mean_reward: float = 0.0
    max_reward: float = 0.0
    min_reward: float = 0.0
    win_rate: float = 0.0
    total_episodes: int = 0
    policy_loss: float = 0.0
    value_loss: float = 0.0
    entropy: float = 0.0
    approx_kl: float = 0.0
    clip_fraction: float = 0.0
    grad_norm: float = 0.0
    learning_rate: float = 0.0
    gpu: GpuMetrics = field(default_factory=GpuMetrics)
    neural: NeuralActivationSnapshot = field(default_factory=NeuralActivationSnapshot)
    latest_metrics: dict[str, Any] = field(default_factory=dict)


class TelemetryTracker:
    def __init__(self, run_name: str, total_updates: int, rollout_steps: int, num_envs: int, run_directory: Path) -> None:
        self.run_name = run_name
        self.total_updates = total_updates
        self.rollout_steps = rollout_steps
        self.num_envs = num_envs
        self.run_directory = Path(run_directory)
        self.start_time = time.time()
        self.last_update_time = self.start_time
        self.state_file = self.run_directory / "state.json"
        self.steps_per_update = rollout_steps * num_envs
        self.total_timesteps = 0

        self.progress = TrainingProgress(
            run_name=run_name,
            start_time=self.start_time,
            total_updates=total_updates,
            status="preparing",
            gpu=collect_gpu_metrics(),
        )
        self.save_state()

    def update(
        self,
        update: int,
        metrics: dict[str, Any],
        model: torch.nn.Module | None = None,
        sample_obs: torch.Tensor | None = None,
    ) -> TrainingProgress:
        now = time.time()
        duration_since_start = now - self.start_time
        step_duration = max(now - self.last_update_time, 1e-6)
        self.last_update_time = now

        self.total_timesteps = update * self.steps_per_update
        updates_done = update
        remaining_updates = max(self.total_updates - updates_done, 0)
        avg_update_duration = duration_since_start / max(updates_done, 1)
        eta_seconds = remaining_updates * avg_update_duration

        sps = self.steps_per_update / step_duration
        ups = 1.0 / step_duration

        self.progress.status = "training" if update < self.total_updates else "completed"
        self.progress.elapsed_seconds = round(duration_since_start, 1)
        self.progress.eta_seconds = round(eta_seconds, 1)
        self.progress.current_update = update
        self.progress.progress_percent = round((update / max(self.total_updates, 1)) * 100, 2)
        self.progress.total_timesteps = self.total_timesteps
        self.progress.steps_per_second = round(sps, 1)
        self.progress.updates_per_second = round(ups, 2)

        self.progress.mean_reward = float(metrics.get("mean_reward", 0.0))
        self.progress.max_reward = float(metrics.get("max_reward", 0.0))
        self.progress.min_reward = float(metrics.get("min_reward", 0.0))
        self.progress.win_rate = float(metrics.get("win_rate", 0.0))
        self.progress.total_episodes = int(metrics.get("episodes", 0))

        self.progress.policy_loss = float(metrics.get("policy_loss", 0.0))
        self.progress.value_loss = float(metrics.get("value_loss", 0.0))
        self.progress.entropy = float(metrics.get("entropy", 0.0))
        self.progress.approx_kl = float(metrics.get("approx_kl", 0.0))
        self.progress.clip_fraction = float(metrics.get("clip_fraction", 0.0))
        self.progress.grad_norm = float(metrics.get("grad_norm", 0.0))
        self.progress.learning_rate = float(metrics.get("learning_rate", 0.0))

        self.progress.gpu = collect_gpu_metrics()
        self.progress.latest_metrics = metrics

        # Inspect neural activations if sample observation is provided
        if model is not None and sample_obs is not None:
            self.progress.neural = self._inspect_network(model, sample_obs)

        self.save_state()
        return self.progress

    def set_status(self, status: str) -> None:
        self.progress.status = status
        self.save_state()

    def _inspect_network(self, model: torch.nn.Module, observation: torch.Tensor) -> NeuralActivationSnapshot:
        snapshot = NeuralActivationSnapshot()
        try:
            obs = observation[:1] if observation.ndim == 2 else observation.unsqueeze(0)
            obs_flat = obs.squeeze(0).detach().cpu().numpy().tolist()

            # Breakdown 376 inputs: 12 tank, 56 shells (8x7), 308 maze (77x4)
            snapshot.input_groups = {
                "tank_features": obs_flat[:12] if len(obs_flat) >= 12 else obs_flat,
                "shell_sensors": obs_flat[12:68] if len(obs_flat) >= 68 else [],
                "maze_raycasts": obs_flat[68:376] if len(obs_flat) >= 376 else [],
            }

            with torch.no_grad():
                distributions, value = model(obs)
                snapshot.predicted_value = round(float(value.squeeze().item()), 4)

                snapshot.action_probabilities = {
                    "movement": distributions[0].probs.squeeze(0).cpu().numpy().round(4).tolist(),
                    "rotation": distributions[1].probs.squeeze(0).cpu().numpy().round(4).tolist(),
                    "fire": distributions[2].probs.squeeze(0).cpu().numpy().round(4).tolist(),
                }

                # Extract hidden layer mean and max activations
                if hasattr(model, "backbone"):
                    current = obs
                    for i, layer in enumerate(model.backbone):
                        current = layer(current)
                        if isinstance(layer, torch.nn.Tanh) or isinstance(layer, torch.nn.ReLU):
                            act = current.squeeze(0).cpu().numpy()
                            snapshot.hidden_activations.append(
                                {
                                    "layer": f"hidden_{len(snapshot.hidden_activations) + 1}",
                                    "mean": round(float(act.mean()), 4),
                                    "max": round(float(act.max()), 4),
                                    "sparsity": round(float((act > 0).mean()), 4),
                                }
                            )
        except Exception:
            pass
        return snapshot

    def save_state(self) -> None:
        state_dict = asdict(self.progress)
        temp_file = self.state_file.with_suffix(".tmp")
        temp_file.write_text(json.dumps(state_dict, indent=2, sort_keys=True), encoding="utf-8")
        temp_file.replace(self.state_file)
