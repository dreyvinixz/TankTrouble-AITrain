"""FastAPI and WebSocket server for real-time training telemetry, metrics, and replays."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .runtime import repository_root

app = FastAPI(title="TankTrouble AI Train Dashboard API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_runs_dir() -> Path:
    runs_dir = repository_root() / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    return runs_dir


@app.get("/api/health")
async def health_check() -> dict[str, Any]:
    return {"status": "ok", "app": "TankTrouble AI Train Dashboard"}


@app.get("/api/runs")
async def list_runs() -> list[dict[str, Any]]:
    runs_dir = get_runs_dir()
    runs_list = []

    for run_path in sorted(runs_dir.iterdir(), reverse=True):
        if not run_path.is_dir():
            continue

        meta_file = run_path / "metadata.json"
        state_file = run_path / "state.json"
        metrics_file = run_path / "metrics.jsonl"

        metadata: dict[str, Any] = {}
        if meta_file.exists():
            try:
                metadata = json.loads(meta_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        state: dict[str, Any] = {}
        if state_file.exists():
            try:
                state = json.loads(state_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        metrics_count = 0
        if metrics_file.exists():
            try:
                with metrics_file.open("r", encoding="utf-8") as fp:
                    metrics_count = sum(1 for _ in fp)
            except Exception:
                pass

        runs_list.append(
            {
                "run_id": run_path.name,
                "run_name": metadata.get("training_config", {}).get("run_name", run_path.name),
                "status": state.get("status", "unknown"),
                "device": metadata.get("device", "unknown"),
                "gpu": metadata.get("gpu", "unknown"),
                "current_update": state.get("current_update", 0),
                "total_updates": state.get("total_updates", 0),
                "mean_reward": state.get("mean_reward", 0.0),
                "win_rate": state.get("win_rate", 0.0),
                "elapsed_seconds": state.get("elapsed_seconds", 0.0),
                "metrics_count": metrics_count,
                "created_at": metadata.get("created_at", run_path.name.split("_")[-1] if "_" in run_path.name else ""),
            }
        )

    return runs_list


@app.get("/api/runs/{run_id}/metadata")
async def get_run_metadata(run_id: str) -> dict[str, Any]:
    run_path = get_runs_dir() / run_id
    meta_file = run_path / "metadata.json"
    if not meta_file.exists():
        raise HTTPException(status_code=404, detail=f"Metadata for run {run_id} not found")
    return json.loads(meta_file.read_text(encoding="utf-8"))


@app.get("/api/runs/{run_id}/state")
async def get_run_state(run_id: str) -> dict[str, Any]:
    run_path = get_runs_dir() / run_id
    state_file = run_path / "state.json"
    if not state_file.exists():
        return {"status": "not_found", "run_id": run_id}
    return json.loads(state_file.read_text(encoding="utf-8"))


@app.get("/api/runs/{run_id}/metrics")
async def get_run_metrics(run_id: str, limit: int = 1000) -> list[dict[str, Any]]:
    run_path = get_runs_dir() / run_id
    metrics_file = run_path / "metrics.jsonl"
    if not metrics_file.exists():
        return []

    lines = []
    with metrics_file.open("r", encoding="utf-8") as fp:
        for line in fp:
            line_str = line.strip()
            if line_str:
                try:
                    lines.append(json.loads(line_str))
                except Exception:
                    continue

    return lines[-limit:] if limit > 0 else lines


@app.get("/api/runs/{run_id}/replays")
async def list_run_replays(run_id: str) -> list[dict[str, Any]]:
    run_path = get_runs_dir() / run_id
    replays_dir = run_path / "replays"
    if not replays_dir.exists():
        return []

    replays = []
    for replay_file in sorted(replays_dir.glob("*.json")):
        if replay_file.name == "latest.json":
            continue
        try:
            data = json.loads(replay_file.read_text(encoding="utf-8"))
            replays.append(
                {
                    "replay_id": replay_file.name,
                    "seed": data.get("seed", 0),
                    "total_frames": data.get("total_frames", 0),
                    "total_reward": data.get("total_reward", 0.0),
                    "winner": data.get("winner", "unknown"),
                }
            )
        except Exception:
            pass

    return replays


@app.get("/api/runs/{run_id}/replays/{replay_id}")
async def get_run_replay(run_id: str, replay_id: str) -> dict[str, Any]:
    run_path = get_runs_dir() / run_id
    replay_file = run_path / "replays" / replay_id
    if not replay_file.exists():
        if not replay_id.endswith(".json"):
            replay_file = run_path / "replays" / f"{replay_id}.json"
    if not replay_file.exists():
        raise HTTPException(status_code=404, detail=f"Replay {replay_id} not found in run {run_id}")

    return json.loads(replay_file.read_text(encoding="utf-8"))


@app.get("/api/runs/{run_id}/checkpoints")
async def list_run_checkpoints(run_id: str) -> list[str]:
    run_path = get_runs_dir() / run_id
    ckpts_dir = run_path / "checkpoints"
    if not ckpts_dir.exists():
        return [f.name for f in sorted(run_path.glob("policy_*.pt"))]
    return [f.name for f in sorted(ckpts_dir.glob("*.pt"))]


@app.websocket("/ws/live/{run_id}")
async def websocket_live_telemetry(websocket: WebSocket, run_id: str) -> None:
    await websocket.accept()
    run_path = get_runs_dir() / run_id
    state_file = run_path / "state.json"
    last_mtime: float = 0.0

    try:
        while True:
            if state_file.exists():
                try:
                    mtime = state_file.stat().st_mtime
                    if mtime != last_mtime:
                        last_mtime = mtime
                        state_data = json.loads(state_file.read_text(encoding="utf-8"))
                        await websocket.send_json({"type": "telemetry", "data": state_data})
                except Exception:
                    pass
            await asyncio.sleep(0.5)
    except (WebSocketDisconnect, asyncio.CancelledError):
        pass


# Serve static web dashboard if dist folder exists
frontend_dist = repository_root() / "dashboard" / "dist"
if frontend_dist.exists() and (frontend_dist / "index.html").exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static_frontend")


def main() -> None:
    import uvicorn

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    print(f"Starting TankTrouble Dashboard API on http://{args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
