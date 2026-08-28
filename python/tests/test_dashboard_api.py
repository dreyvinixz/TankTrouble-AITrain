"""Unit tests for the telemetry module, replay decoder, and dashboard API endpoints."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import numpy as np

from tanktrain.evaluate import decode_replay_frame, extract_maze_walls
from tanktrain.telemetry import TelemetryTracker, collect_gpu_metrics


class DashboardTelemetryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_gpu_metrics_collection(self) -> None:
        gpu = collect_gpu_metrics()
        self.assertIsInstance(gpu.device_name, str)
        self.assertIsInstance(gpu.vram_allocated_mb, float)
        self.assertIsInstance(gpu.vram_reserved_mb, float)

    def test_telemetry_tracker_progress(self) -> None:
        tracker = TelemetryTracker(
            run_name="test_run",
            total_updates=10,
            rollout_steps=64,
            num_envs=4,
            run_directory=self.test_dir,
        )
        self.assertTrue(tracker.state_file.exists())

        metrics = {
            "mean_reward": 1.5,
            "max_reward": 3.0,
            "min_reward": -0.5,
            "win_rate": 0.75,
            "policy_loss": 0.02,
            "value_loss": 0.15,
            "entropy": 1.8,
            "approx_kl": 0.005,
            "clip_fraction": 0.1,
            "grad_norm": 0.4,
            "learning_rate": 0.0003,
            "episodes": 12,
        }

        progress = tracker.update(update=1, metrics=metrics)
        self.assertEqual(progress.current_update, 1)
        self.assertEqual(progress.total_timesteps, 256)
        self.assertEqual(progress.mean_reward, 1.5)
        self.assertEqual(progress.win_rate, 0.75)

        saved_state = json.loads(tracker.state_file.read_text(encoding="utf-8"))
        self.assertEqual(saved_state["current_update"], 1)
        self.assertEqual(saved_state["status"], "training")
        self.assertEqual(saved_state["total_updates"], 10)

    def test_replay_frame_and_maze_decoding(self) -> None:
        # Create a mock 376-element observation
        mock_obs = np.zeros(376, dtype=np.float32)
        # Player tank at (100, 150), angle 90, ammo 5
        mock_obs[0] = 100.0 / 660.0
        mock_obs[1] = 150.0 / 420.0
        mock_obs[2] = 90.0 / 360.0
        mock_obs[3] = 1.0  # 5 ammo

        # Opponent tank at (500, 300), angle 180, ammo 3
        mock_obs[4] = 500.0 / 660.0
        mock_obs[5] = 300.0 / 420.0
        mock_obs[6] = 180.0 / 360.0
        mock_obs[7] = 0.6  # 3 ammo

        # 1 active shell
        mock_obs[12] = 1.0  # active
        mock_obs[13] = 200.0 / 660.0
        mock_obs[14] = 220.0 / 420.0
        mock_obs[15] = 45.0 / 360.0
        mock_obs[16] = 0.0  # player shell
        mock_obs[17] = 0.5  # ttl

        frame = decode_replay_frame(mock_obs, action=[1, 0, 1], reward=0.1, value=0.85)
        self.assertAlmostEqual(frame["player"]["x"], 100.0, delta=1.0)
        self.assertAlmostEqual(frame["player"]["y"], 150.0, delta=1.0)
        self.assertEqual(frame["player"]["ammo"], 5)
        self.assertAlmostEqual(frame["opponent"]["x"], 500.0, delta=1.0)
        self.assertEqual(len(frame["shells"]), 1)
        self.assertAlmostEqual(frame["shells"][0]["x"], 200.0, delta=1.0)

        walls = extract_maze_walls(mock_obs)
        self.assertGreaterEqual(len(walls), 4)  # At least 4 outer bounding walls


if __name__ == "__main__":
    unittest.main()
