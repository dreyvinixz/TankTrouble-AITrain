#!/usr/bin/env bash
# watch_train.sh — Monitora o treinamento PPO em tempo real
# Uso: bash scripts/training/watch_train.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

RUNS_DIR="$ROOT/runs"
LOGS_FILE="$ROOT/train.log"

# Encontra a run mais recente
latest_run() {
  ls -dt "$RUNS_DIR"/ppo_live_demo_* 2>/dev/null | head -1
}

echo "=========================================="
echo "  TankTrouble AI Train — Monitor PPO"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

# Aguarda a run aparecer
while [ -z "$(latest_run)" ]; do
  echo "  Aguardando início do treinamento..."
  sleep 2
done

RUN=$(latest_run)
METRICS="$RUN/metrics.jsonl"
STATE="$RUN/state.json"

echo "  Run: $(basename "$RUN")"
echo "------------------------------------------"

tail -n 0 -F "$METRICS" 2>/dev/null | while IFS= read -r line; do
  # Extrai campos principais com python inline
  python3 -c "
import json, sys
d = json.loads('''$line''')
upd  = d.get('update', '?')
tot  = d.get('total_updates', '?') or '?'
eps  = d.get('episodes', 0)
rw   = d.get('mean_reward', 0)
mx   = d.get('max_reward', 0)
wr   = d.get('win_rate', 0)
pl   = d.get('policy_loss', 0)
vl   = d.get('value_loss', 0)
ent  = d.get('entropy', 0)
kl   = d.get('approx_kl', 0)
gn   = d.get('grad_norm', 0)
print(f'  [Update {upd:>3}] ep={int(eps):>3} | rew={rw:+.3f} max={mx:+.3f} wr={wr:.0%} | π={pl:+.4f} V={vl:.4f} H={ent:.3f} KL={kl:.4f} gn={gn:.3f}')
" 2>/dev/null || echo "  $line"
done
