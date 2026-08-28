import json
from pathlib import Path

run_v2 = Path("runs/ppo_agent_smith_v2_20260828T184451Z")
run_v3 = Path("runs/ppo_agent_smith_v3_20260828T190945Z")

v2_lines = [json.loads(l) for l in (run_v2 / "metrics.jsonl").read_text().splitlines() if l.strip()]
v3_lines = [json.loads(l) for l in (run_v3 / "metrics.jsonl").read_text().splitlines() if l.strip()]

print("=================================================================")
print("           COMPARAÇÃO EXPERIMENTAL: ARENA V2 vs ARENA V3         ")
print("=================================================================")
print(f"Métrica                          | Arena V2 (Sem Lidar) | Arena V3 (8-Ray Lidar)")
print(f"---------------------------------|----------------------|-----------------------")
print(f"Vetor de Entrada                 | 376 features         | 384 features (+8 Lidar)")
print(f"Recompensa Inicial (Update 1)    | {v2_lines[0]['mean_reward']:<20} | {v3_lines[0]['mean_reward']:<20}")
print(f"Recompensa Final (Update 300)    | {v2_lines[-1]['mean_reward']:<20} | {v3_lines[-1]['mean_reward']:<20}")
print(f"Taxa de Vitória Inicial          | {v2_lines[0]['win_rate']*100:.2f}%                | {v3_lines[0]['win_rate']*100:.2f}%")
print(f"Taxa de Vitória Final            | {v2_lines[-1]['win_rate']*100:.2f}%                | {v3_lines[-1]['win_rate']*100:.2f}%")
print(f"Total de Partidas Disputadas     | {v2_lines[-1]['episodes']:<20} | {v3_lines[-1]['episodes']:<20}")
print(f"Value Loss Final (Erro Crítico)  | {v2_lines[-1]['value_loss']:<20} | {v3_lines[-1]['value_loss']:<20}")
print(f"Policy Loss Final                | {v2_lines[-1]['policy_loss']:<20} | {v3_lines[-1]['policy_loss']:<20}")
print(f"Entropia Final                   | {v2_lines[-1]['entropy']:<20} | {v3_lines[-1]['entropy']:<20}")
print("=================================================================")
