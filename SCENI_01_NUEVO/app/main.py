from __future__ import annotations

from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from itertools import product
import json
from typing import Dict, List
from urllib.parse import urlparse
from uuid import uuid4

ENGINE_VERSION = "sceni-core-0.3.0"

store = {
    "opportunities": {},
    "candidates": {},
    "snapshots": {},
    "designs_v2": [],
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def market_for_node(node: str) -> Dict[str, float | str]:
    seed = sum(ord(ch) for ch in node.upper())
    base = 42 + (seed % 28)
    vol = 18 + (seed % 17)
    peak = base * (1.7 + (seed % 10) / 20)
    return {
        "node": node.upper(),
        "avg_price_usd_mwh": round(base, 2),
        "volatility_pct": round(vol, 2),
        "peak_price_usd_mwh": round(peak, 2),
    }


def generate_candidates(opportunity: Dict) -> List[Dict]:
    grid_options = [0.35, 0.5, 0.7]
    solar_options = [0.5, 0.8, 1.1]
    bess_hours_options = [2, 4]
    gas_options = [0.15, 0.3]

    candidates = []
    for grid_share, solar_ratio, bess_hours, gas_ratio in product(grid_options, solar_options, bess_hours_options, gas_options):
        demand = opportunity["demand_mw"]
        grid_mw = min(opportunity["poi_limit_mw"], demand * grid_share)
        solar_mw = demand * solar_ratio
        bess_power_mw = demand * 0.35
        gas_mw = demand * gas_ratio

        candidates.append(
            {
                "id": str(uuid4()),
                "opportunity_id": opportunity["id"],
                "architecture": {
                    "grid_import_mw": round(grid_mw, 2),
                    "solar_capacity_mw": round(solar_mw, 2),
                    "bess_power_mw": round(bess_power_mw, 2),
                    "bess_energy_mwh": round(bess_power_mw * bess_hours, 2),
                    "gas_dispatchable_mw": round(gas_mw, 2),
                },
            }
        )
    return candidates


def evaluate_candidate(opportunity: Dict, candidate: Dict) -> Dict[str, float]:
    arch = candidate["architecture"]
    avg_demand_mwh = opportunity["demand_mw"] * opportunity["horizon_hours"]

    grid_supply = arch["grid_import_mw"] * opportunity["horizon_hours"]
    solar_supply = arch["solar_capacity_mw"] * opportunity["solar_capacity_factor"] * opportunity["horizon_hours"]
    bess_supply = arch["bess_energy_mwh"] * 0.92
    gas_supply = arch["gas_dispatchable_mw"] * (opportunity["horizon_hours"] * 0.5)

    served = min(avg_demand_mwh, grid_supply + solar_supply + bess_supply + gas_supply)
    unserved = max(0.0, avg_demand_mwh - served)
    firm_energy = (served / avg_demand_mwh) * 100

    capex = arch["solar_capacity_mw"] * 1.05 + arch["bess_power_mw"] * 0.78 + arch["gas_dispatchable_mw"] * 0.88
    market = market_for_node(opportunity["ercot_node"])
    margin_factor = max(1.05, (market["peak_price_usd_mwh"] / market["avg_price_usd_mwh"]) * 0.8)
    irr = max(-4.0, min(26.0, (firm_energy / 6.5) + (margin_factor * 3.2) - capex * 0.09))

    tech_count = sum(1 for key in ["solar_capacity_mw", "bess_power_mw", "gas_dispatchable_mw"] if arch[key] > 0)
    diversity = (tech_count / 3) * 100

    score = (
        firm_energy * 0.45
        + max(0, 100 - (unserved / avg_demand_mwh) * 180) * 0.3
        + (irr + 5) * 2.2 * 0.2
        + diversity * 0.05
    )

    return {
        "firm_energy_pct": round(firm_energy, 2),
        "unserved_mwh": round(unserved, 2),
        "irr_pct": round(irr, 2),
        "diversity_score": round(diversity, 2),
        "total_score": round(score, 2),
    }


def persist_snapshot(opportunity: Dict, candidate: Dict, results: Dict) -> Dict:
    snapshot = {
        "id": str(uuid4()),
        "opportunity_id": opportunity["id"],
        "candidate_id": candidate["id"],
        "created_at": now_iso(),
        "engine_version": ENGINE_VERSION,
        "assumptions": {
            "horizon_hours": opportunity["horizon_hours"],
            "solar_capacity_factor": opportunity["solar_capacity_factor"],
            "poi_limit_mw": opportunity["poi_limit_mw"],
        },
        "architecture": candidate["architecture"],
        "results": results,
    }
    store["snapshots"][snapshot["id"]] = snapshot
    return snapshot


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _parse_json(self):
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length == 0:
            return {}
        raw = self.rfile.read(content_length)
        return json.loads(raw.decode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/":
            self._send(
                200,
                {
                    "name": "SCENI",
                    "message": "Decision support system for critical energy infrastructure.",
                    "status": "ok",
                    "engine_version": ENGINE_VERSION,
                },
            )
            return

        if path == "/health":
            self._send(200, {"status": "healthy"})
            return

        if path == "/api/v1/opportunities":
            self._send(200, list(store["opportunities"].values()))
            return

        if path.startswith("/api/v1/market/ercot/"):
            node = path.split("/api/v1/market/ercot/")[-1]
            self._send(200, market_for_node(node))
            return

        if path.startswith("/api/v1/opportunities/") and path.endswith("/designs"):
            opportunity_id = path.split("/")[4]
            if opportunity_id not in store["opportunities"]:
                self._send(404, {"error": "Opportunity not found"})
                return
            rows = [d for d in store["designs_v2"] if store["snapshots"][d["snapshot_id"]]["opportunity_id"] == opportunity_id]
            self._send(200, rows)
            return

        if path.startswith("/api/v1/snapshots/"):
            snapshot_id = path.split("/api/v1/snapshots/")[-1]
            snapshot = store["snapshots"].get(snapshot_id)
            if not snapshot:
                self._send(404, {"error": "Snapshot not found"})
                return
            self._send(200, snapshot)
            return

        if path == "/docs":
            self._send(
                200,
                {
                    "available_endpoints": [
                        "GET /health",
                        "POST /api/v1/opportunities",
                        "POST /api/v1/opportunities/{id}/simulate",
                        "GET /api/v1/opportunities/{id}/designs",
                        "GET /api/v1/snapshots/{snapshot_id}",
                        "GET /api/v1/market/ercot/{node}",
                    ]
                },
            )
            return

        self._send(404, {"error": "Not found"})

    def do_POST(self):
        path = urlparse(self.path).path

        if path == "/api/v1/opportunities":
            try:
                payload = self._parse_json()
                required = ["name", "ercot_node", "demand_mw", "poi_limit_mw", "horizon_hours"]
                for field in required:
                    if field not in payload:
                        self._send(400, {"error": f"Missing field: {field}"})
                        return

                opportunity = {
                    "id": str(uuid4()),
                    "created_at": now_iso(),
                    "name": payload["name"],
                    "ercot_node": payload["ercot_node"],
                    "horizon_hours": int(payload.get("horizon_hours", 24)),
                    "demand_mw": float(payload["demand_mw"]),
                    "poi_limit_mw": float(payload["poi_limit_mw"]),
                    "solar_capacity_factor": float(payload.get("solar_capacity_factor", 0.28)),
                }
                store["opportunities"][opportunity["id"]] = opportunity
                self._send(200, opportunity)
                return
            except Exception as exc:
                self._send(400, {"error": str(exc)})
                return

        if path.startswith("/api/v1/opportunities/") and path.endswith("/simulate"):
            opportunity_id = path.split("/")[4]
            opportunity = store["opportunities"].get(opportunity_id)
            if not opportunity:
                self._send(404, {"error": "Opportunity not found"})
                return

            candidates = generate_candidates(opportunity)
            for candidate in candidates:
                store["candidates"][candidate["id"]] = candidate

            ranked = []
            for candidate in candidates:
                results = evaluate_candidate(opportunity, candidate)
                snapshot = persist_snapshot(opportunity, candidate, results)
                ranked.append(
                    {
                        "snapshot_id": snapshot["id"],
                        "candidate_id": candidate["id"],
                        "firm_energy_pct": results["firm_energy_pct"],
                        "unserved_mwh": results["unserved_mwh"],
                        "irr_pct": results["irr_pct"],
                        "diversity_score": results["diversity_score"],
                        "total_score": results["total_score"],
                        "rank": 0,
                    }
                )

            ranked.sort(key=lambda x: x["total_score"], reverse=True)
            for idx, row in enumerate(ranked, start=1):
                row["rank"] = idx

            store["designs_v2"] = [d for d in store["designs_v2"] if store["snapshots"][d["snapshot_id"]]["opportunity_id"] != opportunity_id]
            store["designs_v2"].extend(ranked)

            self._send(
                200,
                {
                    "opportunity": opportunity,
                    "candidate_count": len(candidates),
                    "recommended_design": ranked[0],
                    "designs": ranked,
                },
            )
            return

        self._send(404, {"error": "Not found"})


def main():
    server = HTTPServer(("0.0.0.0", 8000), Handler)
    print("SCENI backend en http://localhost:8000")
    server.serve_forever()


if __name__ == "__main__":
    main()
