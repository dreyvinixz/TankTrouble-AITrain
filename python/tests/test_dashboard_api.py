"""Unit tests for the telemetry module, real contract observation decoder, and FastAPI endpoints."""

from __future__ import annotations

import json
import math
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from fastapi.testclient import TestClient

from tanktrain.dashboard_server import app
from tanktrain.evaluate import (
    ARENA_HEIGHT,
    ARENA_WIDTH,
    COLS,
    ROWS,
    decode_replay_frame,
    extract_maze_walls,
)
from tanktrain.telemetry import TelemetryTracker, collect_gpu_metrics


class DashboardTelemetryAndApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.test_dir = Path(tempfile.mkdtemp())
        self.client = TestClient(app)

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_gpu_metrics_collection(self) -> None:
        gpu = collect_gpu_metrics()
        self.assertIsInstance(gpu.device_name, str)
        self.assertIsInstance(gpu.vram_allocated_mb, float)
        self.assertIsInstance(gpu.vram_reserved_mb, float)
        self.assertIsInstance(gpu.cuda_available, bool)

    def test_telemetry_tracker_progress(self) -> None:
        tracker = TelemetryTracker(
            run_name="test_run",
            total_updates=10,
            rollout_steps=64,
            num_envs=4,
            run_directory=self.test_dir,
        )
        self.assertTrue(tracker.state_file.exists())

        raw_metrics = {
            "completed_episodes": 4,
            "completed_reward": 1.8,
            "win_rate": 0.75,
            "policy_loss": 0.02,
            "value_loss": 0.15,
            "entropy": 1.8,
            "approx_kl": 0.005,
            "clip_fraction": 0.1,
            "grad_norm": 0.4,
            "learning_rate": 0.0003,
        }

        progress = tracker.update(update=1, metrics=raw_metrics)
        self.assertEqual(progress.current_update, 1)
        self.assertEqual(progress.total_timesteps, 256)
        self.assertAlmostEqual(progress.mean_reward, 1.8, delta=0.01)
        self.assertAlmostEqual(progress.win_rate, 0.75, delta=0.01)
        self.assertEqual(progress.total_episodes, 4)

        saved_state = json.loads(tracker.state_file.read_text(encoding="utf-8"))
        self.assertEqual(saved_state["current_update"], 1)
        self.assertEqual(saved_state["status"], "training")
        self.assertEqual(saved_state["total_updates"], 10)
        self.assertAlmostEqual(saved_state["mean_reward"], 1.8, delta=0.01)

    def test_observation_decoding_exact_contract(self) -> None:
        # Build 376-element observation matching exact TankArena.cc contract
        obs = np.zeros(376, dtype=np.float32)

        # Player Tank: (x=132, y=210, angle=90 deg -> sin=1, cos=0, ammo=4/5=0.8, alive=1.0)
        player_rad = math.radians(90.0)
        obs[0] = 132.0 / ARENA_WIDTH
        obs[1] = 210.0 / ARENA_HEIGHT
        obs[2] = math.sin(player_rad)
        obs[3] = math.cos(player_rad)
        obs[4] = 4.0 / 5.0  # 4 ammo
        obs[5] = 1.0        # alive

        # Opponent Tank: (x=528, y=300, angle=180 deg -> sin=0, cos=-1, ammo=3/5=0.6, alive=1.0)
        opponent_rad = math.radians(180.0)
        obs[6] = 528.0 / ARENA_WIDTH
        obs[7] = 300.0 / ARENA_HEIGHT
        obs[8] = math.sin(opponent_rad)
        obs[9] = math.cos(opponent_rad)
        obs[10] = 3.0 / 5.0  # 3 ammo
        obs[11] = 1.0        # alive

        # Shell 0: (active=1.0, shell_x=200, shell_y=250, angle=45 deg, owner=player (1.0), ttl=120/180)
        shell_rad = math.radians(45.0)
        base = 12
        obs[base + 0] = (200.0 - 132.0) / ARENA_WIDTH  # (shell.x - player.x) / width
        obs[base + 1] = (250.0 - 210.0) / ARENA_HEIGHT # (shell.y - player.y) / height
        obs[base + 2] = math.sin(shell_rad)
        obs[base + 3] = math.cos(shell_rad)
        obs[base + 4] = 1.0   # player owner (0)
        obs[base + 5] = 120.0 / 180.0
        obs[base + 6] = 1.0   # active

        # Maze walls: cell (0, 0) has blocked north and east
        obs[68 + 0 * 4 + 0] = 1.0  # North
        obs[68 + 0 * 4 + 1] = 1.0  # East

        frame = decode_replay_frame(obs, action=[1, 2, 0], reward=0.05, value=0.72, step_idx=1)

        self.assertAlmostEqual(frame["player"]["x"], 132.0, delta=0.5)
        self.assertAlmostEqual(frame["player"]["y"], 210.0, delta=0.5)
        self.assertAlmostEqual(frame["player"]["angle"], 90.0, delta=1.0)
        self.assertEqual(frame["player"]["ammo"], 4)
        self.assertTrue(frame["player"]["alive"])

        self.assertAlmostEqual(frame["opponent"]["x"], 528.0, delta=0.5)
        self.assertAlmostEqual(frame["opponent"]["y"], 300.0, delta=0.5)
        self.assertAlmostEqual(frame["opponent"]["angle"], 180.0, delta=1.0)
        self.assertEqual(frame["opponent"]["ammo"], 3)
        self.assertTrue(frame["opponent"]["alive"])

        self.assertEqual(len(frame["shells"]), 1)
        self.assertAlmostEqual(frame["shells"][0]["x"], 200.0, delta=0.5)
        self.assertAlmostEqual(frame["shells"][0]["y"], 250.0, delta=0.5)
        self.assertAlmostEqual(frame["shells"][0]["angle"], 45.0, delta=1.0)
        self.assertEqual(frame["shells"][0]["owner"], 0)
        self.assertEqual(frame["shells"][0]["ttl"], 120)

        walls = extract_maze_walls(obs)
        self.assertGreaterEqual(len(walls), 4)

    def test_fastapi_rest_endpoints(self) -> None:
        # Create a mock run directory structure
        mock_run = self.test_dir / "run_test_20260828"
        mock_run.mkdir(parents=True)
        (mock_run / "replays").mkdir()
        (mock_run / "checkpoints").mkdir()

        (mock_run / "metadata.json").write_text(
            json.dumps({"training_config": {"run_name": "run_test"}, "device": "cuda"}),
            encoding="utf-8",
        )
        (mock_run / "state.json").write_text(
            json.dumps({"status": "training", "current_update": 5, "total_updates": 10, "mean_reward": 1.2}),
            encoding="utf-8",
        )
        (mock_run / "metrics.jsonl").write_text(
            '{"update": 1, "mean_reward": 0.5}\n{"update": 2, "mean_reward": 1.2}\n',
            encoding="utf-8",
        )
        (mock_run / "replays" / "replay_update_00001.json").write_text(
            json.dumps({"seed": 77, "total_frames": 100, "total_reward": 1.5, "winner": "player", "walls": [], "frames": []}),
            encoding="utf-8",
        )

        with patch("tanktrain.dashboard_server.get_runs_dir", return_value=self.test_dir):
            # 1. Health check
            res_health = self.client.get("/api/health")
            self.assertEqual(res_health.status_code, 200)
            self.assertEqual(res_health.json()["status"], "ok")

            # 2. List runs
            res_runs = self.client.get("/api/runs")
            self.assertEqual(res_runs.status_code, 200)
            runs = res_runs.json()
            self.assertEqual(len(runs), 1)
            self.assertEqual(runs[0]["run_id"], "run_test_20260828")
            self.assertEqual(runs[0]["current_update"], 5)

            # 3. Get run state
            res_state = self.client.get("/api/runs/run_test_20260828/state")
            self.assertEqual(res_state.status_code, 200)
            self.assertEqual(res_state.json()["current_update"], 5)

            # 4. Get run metrics
            res_metrics = self.client.get("/api/runs/run_test_20260828/metrics")
            self.assertEqual(res_metrics.status_code, 200)
            self.assertEqual(len(res_metrics.json()), 2)

            # 5. List replays
            res_replays = self.client.get("/api/runs/run_test_20260828/replays")
            self.assertEqual(res_replays.status_code, 200)
            self.assertEqual(len(res_replays.json()), 1)

            # 6. Get replay content
            res_rep = self.client.get("/api/runs/run_test_20260828/replays/replay_update_00001.json")
            self.assertEqual(res_rep.status_code, 200)
            self.assertEqual(res_rep.json()["winner"], "player")


if __name__ == "__main__":
    unittest.main()
