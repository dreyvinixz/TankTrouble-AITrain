"""Print last 5 lines of metrics.jsonl in a readable format."""
import json
import sys

metrics_file = sys.argv[1]
lines = open(metrics_file, encoding="utf-8").read().strip().split("\n")

for line in lines[-5:]:
    try:
        d = json.loads(line)
        u  = d.get("update", "?")
        r  = d.get("mean_reward", 0)
        w  = d.get("win_rate", 0)
        p  = d.get("policy_loss", 0)
        v  = d.get("value_loss", 0)
        wr = d.get("win_rate", 0)
        ep = d.get("episodes", 0)
        print(f"  Update {str(u):>3}: rew={r:+.3f}  wr={w:.0%}  ep={int(ep):>3}  pi={p:+.5f}  V={v:.5f}")
    except Exception:
        pass
