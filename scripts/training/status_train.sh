#!/usr/bin/env bash
# status_train.sh — Snapshot para colar ao assistente
# Uso: bash scripts/training/status_train.sh
# Gera: train_status.log na raiz do projeto
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RUNS_DIR="$ROOT/runs"
LOG="$ROOT/train_status.log"

latest_run() {
  # Encontra a pasta de run mais recente que tenha state.json
  find "$RUNS_DIR" -maxdepth 2 -name "state.json" -printf '%T@ %h\n' 2>/dev/null \
    | sort -rn | head -1 | awk '{print $2}' || true
}

RUN="$(latest_run)"
if [ -z "$RUN" ]; then
  echo "[status_train] Nenhuma run encontrada em $RUNS_DIR"
  exit 0
fi

STATE="$RUN/state.json"
METRICS="$RUN/metrics.jsonl"

output() {
  echo "======================================"
  echo " SNAPSHOT — $(date '+%Y-%m-%d %H:%M:%S')"
  echo "======================================"
  echo " Run: $(basename "$RUN")"
  echo ""

  if [ -f "$STATE" ]; then
    python3 "$ROOT/scripts/training/parse_state.py" "$STATE"
  else
    echo " (state.json ainda nao existe — aguarde inicio)"
  fi

  echo ""
  echo " -- Ultimas 5 metricas --"
  if [ -f "$METRICS" ] && [ -s "$METRICS" ]; then
    python3 "$ROOT/scripts/training/tail_metrics.py" "$METRICS"
  else
    echo "  (sem metricas ainda — treinamento iniciando)"
  fi

  echo ""
  echo " Replays:"
  REP_DIR="$RUN/replays"
  if [ -d "$REP_DIR" ]; then
    count=0
    for f in "$REP_DIR"/*.json; do
      [ -f "$f" ] || continue
      python3 -c "
import json, os, sys
try:
    d = json.load(open(sys.argv[1]))
    fn = os.path.basename(sys.argv[1])
    print(f'  {fn}: {d.get(\"total_frames\",0)} frames | rew={d.get(\"total_reward\",0):+.3f} | {d.get(\"winner\",\"?\")}')
except Exception as e:
    print(f'  {os.path.basename(sys.argv[1])}: erro ({e})')
" "$f" 2>/dev/null || true
      count=$((count+1))
      [ $count -ge 10 ] && break
    done
    [ $count -eq 0 ] && echo "  (sem replays ainda)"
  else
    echo "  (sem replays ainda)"
  fi
  echo "======================================"
}

output | tee "$LOG"
echo ""
echo ">> Log salvo em: $LOG"
echo ">> Cole o conteudo acima para o assistente acompanhar."
