#!/usr/bin/env python3
import json
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"


def req(path, method="GET", payload=None):
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    r = urllib.request.Request(f"{BASE}{path}", data=data, method=method, headers=headers)
    with urllib.request.urlopen(r, timeout=20) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body)


def main():
    out = {"checks": []}

    health = req("/health")
    out["checks"].append({"name": "health", "ok": health.get("status") == "healthy"})

    bootstrap = req("/api/v1/ingestion/bootstrap-demo", method="POST", payload={"node": "HB_HOUSTON"})
    out["checks"].append({"name": "bootstrap-demo", "ok": bootstrap.get("ingested", {}).get("market_prices", 0) >= 1})

    opportunity = req(
        "/api/v1/opportunities",
        method="POST",
        payload={
            "name": "Readiness Opportunity",
            "ercot_node": "HB_HOUSTON",
            "demand_mw": 80,
            "poi_limit_mw": 45,
            "horizon_hours": 168,
        },
    )
    sim = req(f"/api/v1/opportunities/{opportunity['id']}/simulate", method="POST")
    out["checks"].append({"name": "simulate", "ok": sim.get("candidate_count", 0) > 0})

    value = req("/api/v1/value/summary")
    out["checks"].append({"name": "value-summary", "ok": value.get("status") == "ok" and value.get("designs_evaluated", 0) > 0})

    quality = req("/api/v1/data-quality/status")
    out["checks"].append({"name": "data-quality", "ok": "grid_constraints" in quality})

    out["ok"] = all(item["ok"] for item in out["checks"])
    print(json.dumps(out, indent=2))
    if not out["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    try:
        main()
    except urllib.error.URLError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        raise SystemExit(2)
