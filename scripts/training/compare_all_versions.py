import json
from pathlib import Path

run_v2 = Path("runs/ppo_agent_smith_v2_20260828T184451Z")
run_v3 = Path("runs/ppo_agent_smith_v3_20260828T190945Z")
run_v4 = Path("runs/ppo_agent_smith_v4_temporal_20260828T193035Z")

v2_lines = [json.loads(l) for l in (run_v2 / "metrics.jsonl").read_text().splitlines() if l.strip()]
v3_lines = [json.loads(l) for l in (run_v3 / "metrics.jsonl").read_text().splitlines() if l.strip()]
v4_lines = [json.loads(l) for l in (run_v4 / "metrics.jsonl").read_text().splitlines() if l.strip()]

print("==========================================================================================")
print("             BENCHMARK COMPARATIVO TRIPLO: ARENA V2 vs ARENA V3 vs ARENA V4               ")
print("==========================================================================================")
print(f"Métrica                          | Arena V2 (Sem Lidar) | Arena V3 (Lidar 8R)  | Arena V4 (Lidar + Memória)")
print(f"---------------------------------|----------------------|----------------------|---------------------------")
print(f"Vetor de Observação              | 376 features         | 384 features         | 1536 features (4x stack)")
print(f"Recompensa Inicial (Update 1)    | {v2_lines[0]['mean_reward']:<20} | {v3_lines[0]['mean_reward']:<20} | {v4_lines[0]['mean_reward']:<20}")
print(f"Recompensa Final (Update 300)    | {v2_lines[-1]['mean_reward']:<20} | {v3_lines[-1]['mean_reward']:<20} | {v4_lines[-1]['mean_reward']:<20}")
print(f"Total de Partidas / Episódios    | {v2_lines[-1]['episodes']:<20} | {v3_lines[-1]['episodes']:<20} | {v4_lines[-1]['episodes']:<20}")
print(f"Value Loss Final (Erro Crítico)  | {v2_lines[-1]['value_loss']:<20} | {v3_lines[-1]['value_loss']:<20} | {v4_lines[-1]['value_loss']:<20}")
print(f"Policy Loss Final                | {v2_lines[-1]['policy_loss']:<20} | {v3_lines[-1]['policy_loss']:<20} | {v4_lines[-1]['policy_loss']:<20}")
print(f"Entropia Final                   | {v2_lines[-1]['entropy']:<20} | {v3_lines[-1]['entropy']:<20} | {v4_lines[-1]['entropy']:<20}")
print("==========================================================================================")
