import json
from pathlib import Path

run_dir = Path("runs/ppo_agent_smith_v2_20260828T184451Z")
metrics_file = run_dir / "metrics.jsonl"
lines = [json.loads(line) for line in metrics_file.read_text().splitlines() if line.strip()]

metadata = json.loads((run_dir / "metadata.json").read_text())

print("=== AUDITORIA DO TREINAMENTO PPO V2 ===")
print("Run ID:", run_dir.name)
print("GPU:", metadata.get("gpu"))
print("CUDA:", metadata.get("cuda"))
print("Total Updates:", len(lines))
total_steps = len(lines) * 128 * 32
print("Total Steps Simulados:", f"{total_steps:,}")
print("Total Episódios Simulados:", lines[-1]["episodes"])

rewards = [l["mean_reward"] for l in lines]
entropies = [l["entropy"] for l in lines]
value_losses = [l["value_loss"] for l in lines]
policy_losses = [l["policy_loss"] for l in lines]
kls = [l["approx_kl"] for l in lines]
clip_fractions = [l["clip_fraction"] for l in lines]

print("\n--- CURVA DE RECOMPENSA ---")
print("Recompensa Inicial (Update 1):", lines[0]["mean_reward"])
print("Recompensa Média Final (Update 300):", lines[-1]["mean_reward"])
print("Melhor Recompensa de Episódio:", max(l["max_reward"] for l in lines))
print("Pior Recompensa de Episódio:", min(l["min_reward"] for l in lines))

print("\n--- ESTABILIDADE DO OTIMIZADOR ---")
print("Value Loss Inicial / Final:", lines[0]["value_loss"], "/", lines[-1]["value_loss"])
print("Policy Loss Final:", lines[-1]["policy_loss"])
print("Entropia Inicial / Final:", lines[0]["entropy"], "/", lines[-1]["entropy"])
print("Approx KL Médio:", sum(kls)/len(kls))
print("Clip Fraction Médio:", sum(clip_fractions)/len(clip_fractions))

replays = list((run_dir / "replays").glob("*.json"))
print("\n--- DESFECHO DOS REPLAYS GRAVADOS ---")
print("Total de Replays Amostrados:", len(replays))
outcomes = {}
lengths = []
for r in replays:
    data = json.loads(r.read_text())
    w = data.get("winner", "unknown")
    outcomes[w] = outcomes.get(w, 0) + 1
    lengths.append(data.get("total_frames", 0))

print("Distribuição de Resultados:", outcomes)
if lengths:
    print("Duração Média das Partidas (frames):", sum(lengths)/len(lengths))
