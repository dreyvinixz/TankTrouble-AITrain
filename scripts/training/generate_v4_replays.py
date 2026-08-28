import json
from pathlib import Path
import torch

from tanktrain.model import ActorCritic
from tanktrain.environment import EnvironmentConfig
from tanktrain.evaluate import record_replay_episode

run_path = Path("runs/ppo_agent_smith_v4_temporal_20260828T193035Z")
ckpt_path = run_path / "checkpoints" / "policy_00300.pt"
replays_dir = run_path / "replays"
replays_dir.mkdir(exist_ok=True)

ckpt = torch.load(ckpt_path, map_location="cuda")
env_cfg = EnvironmentConfig(
    seed=17,
    ticks_per_action=3,
    max_decisions=400,
    win_reward=1.0,
    loss_reward=-1.0,
    timeout_reward=-0.20,
    survival_reward=0.0,
    frame_stack=4
)
model = ActorCritic(env_cfg.frame_stack * 384, [256, 256]).to("cuda")
model.load_state_dict(ckpt["model"])

best_data = None
for u, s in [(1, 101), (50, 202), (100, 303), (150, 404), (200, 505), (250, 606), (300, 707)]:
    data = record_replay_episode(model, env_cfg, seed=s, device=torch.device("cuda"), max_steps=400)
    data["update"] = u
    (replays_dir / f"replay_update_{u:05d}.json").write_text(json.dumps(data), encoding="utf-8")
    best_data = data

(replays_dir / "latest.json").write_text(json.dumps(best_data), encoding="utf-8")
(replays_dir / "best.json").write_text(json.dumps(best_data), encoding="utf-8")
print("Successfully generated", len(list(replays_dir.glob("*.json"))), "replays for V4 run!")
