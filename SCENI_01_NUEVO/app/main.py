from __future__ import annotations

from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from itertools import product
import json
import os
from pathlib import Path
import sqlite3
from typing import Dict, List, Tuple
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import urlopen
from uuid import uuid4

ENGINE_VERSION = "sceni-core-0.5.0"
DB_PATH = os.getenv("SCENI_DB_PATH", str(Path(__file__).resolve().parents[1] / "data" / "sceni.db"))


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def db_conn() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with db_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS opportunities (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                name TEXT NOT NULL,
                ercot_node TEXT NOT NULL,
                horizon_hours INTEGER NOT NULL,
                demand_mw REAL NOT NULL,
                poi_limit_mw REAL NOT NULL,
                solar_capacity_factor REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS snapshots (
                id TEXT PRIMARY KEY,
                opportunity_id TEXT NOT NULL,
                candidate_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                engine_version TEXT NOT NULL,
                assumptions_json TEXT NOT NULL,
                architecture_json TEXT NOT NULL,
                results_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS designs_v2 (
                snapshot_id TEXT PRIMARY KEY,
                opportunity_id TEXT NOT NULL,
                candidate_id TEXT NOT NULL,
                firm_energy_pct REAL NOT NULL,
                unserved_mwh REAL NOT NULL,
                irr_pct REAL NOT NULL,
                diversity_score REAL NOT NULL,
                total_score REAL NOT NULL,
                rank_pos INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS data_sources (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                source_type TEXT NOT NULL,
                base_url TEXT NOT NULL,
                config_json TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_sync_at TEXT
            );

            CREATE TABLE IF NOT EXISTS source_observations (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                observed_at TEXT NOT NULL,
                metric_key TEXT,
                metric_value REAL,
                payload_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS grid_constraints (
                id TEXT PRIMARY KEY,
                node TEXT NOT NULL,
                constraint_type TEXT NOT NULL,
                limit_mw REAL,
                status TEXT NOT NULL,
                source TEXT NOT NULL,
                observed_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS market_prices (
                id TEXT PRIMARY KEY,
                node TEXT NOT NULL,
                price_usd_mwh REAL NOT NULL,
                volatility_pct REAL,
                source TEXT NOT NULL,
                observed_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS weather_samples (
                id TEXT PRIMARY KEY,
                node TEXT NOT NULL,
                temperature_c REAL,
                wind_speed_ms REAL,
                cloud_cover_pct REAL,
                source TEXT NOT NULL,
                observed_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS ingestion_runs (
                id TEXT PRIMARY KEY,
                run_type TEXT NOT NULL,
                status TEXT NOT NULL,
                details_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )


def market_for_node(node: str) -> Dict[str, float | str]:
    latest = latest_market_price(node)
    if latest:
        return {
            "node": node.upper(),
            "avg_price_usd_mwh": round(float(latest["price_usd_mwh"]), 2),
            "volatility_pct": round(float(latest["volatility_pct"] or 20.0), 2),
            "peak_price_usd_mwh": round(float(latest["price_usd_mwh"]) * 1.85, 2),
        }

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


def get_opportunity(opportunity_id: str) -> Dict | None:
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM opportunities WHERE id = ?", (opportunity_id,)).fetchone()
    return dict(row) if row else None


def list_opportunities() -> List[Dict]:
    with db_conn() as conn:
        rows = conn.execute("SELECT * FROM opportunities ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


def create_opportunity(payload: Dict) -> Dict:
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
    with db_conn() as conn:
        conn.execute(
            """
            INSERT INTO opportunities (id, created_at, name, ercot_node, horizon_hours, demand_mw, poi_limit_mw, solar_capacity_factor)
            VALUES (:id, :created_at, :name, :ercot_node, :horizon_hours, :demand_mw, :poi_limit_mw, :solar_capacity_factor)
            """,
            opportunity,
        )
    return opportunity


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
    with db_conn() as conn:
        conn.execute(
            """
            INSERT INTO snapshots (id, opportunity_id, candidate_id, created_at, engine_version, assumptions_json, architecture_json, results_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                snapshot["id"],
                snapshot["opportunity_id"],
                snapshot["candidate_id"],
                snapshot["created_at"],
                snapshot["engine_version"],
                json.dumps(snapshot["assumptions"]),
                json.dumps(snapshot["architecture"]),
                json.dumps(snapshot["results"]),
            ),
        )
    return snapshot


def run_simulation(opportunity_id: str) -> Dict:
    opportunity = get_opportunity(opportunity_id)
    if not opportunity:
        return {"error": "Opportunity not found", "status": 404}

    candidates = generate_candidates(opportunity)
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

    with db_conn() as conn:
        conn.execute("DELETE FROM designs_v2 WHERE opportunity_id = ?", (opportunity_id,))
        conn.executemany(
            """
            INSERT INTO designs_v2 (snapshot_id, opportunity_id, candidate_id, firm_energy_pct, unserved_mwh, irr_pct, diversity_score, total_score, rank_pos)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    d["snapshot_id"],
                    opportunity_id,
                    d["candidate_id"],
                    d["firm_energy_pct"],
                    d["unserved_mwh"],
                    d["irr_pct"],
                    d["diversity_score"],
                    d["total_score"],
                    d["rank"],
                )
                for d in ranked
            ],
        )

    return {
        "opportunity": opportunity,
        "candidate_count": len(candidates),
        "recommended_design": ranked[0],
        "designs": ranked,
    }


def list_designs(opportunity_id: str) -> List[Dict] | None:
    if not get_opportunity(opportunity_id):
        return None
    with db_conn() as conn:
        rows = conn.execute(
            """
            SELECT snapshot_id, candidate_id, firm_energy_pct, unserved_mwh, irr_pct, diversity_score, total_score, rank_pos
            FROM designs_v2
            WHERE opportunity_id = ?
            ORDER BY rank_pos ASC
            """,
            (opportunity_id,),
        ).fetchall()
    return [
        {
            "snapshot_id": r["snapshot_id"],
            "candidate_id": r["candidate_id"],
            "firm_energy_pct": r["firm_energy_pct"],
            "unserved_mwh": r["unserved_mwh"],
            "irr_pct": r["irr_pct"],
            "diversity_score": r["diversity_score"],
            "total_score": r["total_score"],
            "rank": r["rank_pos"],
        }
        for r in rows
    ]


def get_snapshot(snapshot_id: str) -> Dict | None:
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM snapshots WHERE id = ?", (snapshot_id,)).fetchone()
    if not row:
        return None
    return {
        "id": row["id"],
        "opportunity_id": row["opportunity_id"],
        "candidate_id": row["candidate_id"],
        "created_at": row["created_at"],
        "engine_version": row["engine_version"],
        "assumptions": json.loads(row["assumptions_json"]),
        "architecture": json.loads(row["architecture_json"]),
        "results": json.loads(row["results_json"]),
    }


def create_data_source(payload: Dict) -> Dict:
    row = {
        "id": str(uuid4()),
        "name": payload["name"],
        "source_type": payload["source_type"],
        "base_url": payload["base_url"],
        "config_json": json.dumps(payload.get("config", {})),
        "status": "created",
        "created_at": now_iso(),
        "last_sync_at": None,
    }
    with db_conn() as conn:
        conn.execute(
            """
            INSERT INTO data_sources (id, name, source_type, base_url, config_json, status, created_at, last_sync_at)
            VALUES (:id, :name, :source_type, :base_url, :config_json, :status, :created_at, :last_sync_at)
            """,
            row,
        )
    row["config"] = json.loads(row["config_json"])
    del row["config_json"]
    return row


def latest_market_price(node: str) -> Dict | None:
    with db_conn() as conn:
        row = conn.execute(
            """
            SELECT node, price_usd_mwh, volatility_pct, observed_at
            FROM market_prices
            WHERE UPPER(node) = UPPER(?)
            ORDER BY observed_at DESC
            LIMIT 1
            """,
            (node,),
        ).fetchone()
    return dict(row) if row else None


def list_grid_constraints(node: str | None = None, limit: int = 100) -> List[Dict]:
    with db_conn() as conn:
        if node:
            rows = conn.execute(
                """
                SELECT * FROM grid_constraints
                WHERE UPPER(node) = UPPER(?)
                ORDER BY observed_at DESC
                LIMIT ?
                """,
                (node, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM grid_constraints ORDER BY observed_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
    return [dict(r) for r in rows]


def list_market_prices(node: str | None = None, limit: int = 100) -> List[Dict]:
    with db_conn() as conn:
        if node:
            rows = conn.execute(
                """
                SELECT * FROM market_prices
                WHERE UPPER(node) = UPPER(?)
                ORDER BY observed_at DESC
                LIMIT ?
                """,
                (node, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM market_prices ORDER BY observed_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
    return [dict(r) for r in rows]


def list_weather_samples(node: str | None = None, limit: int = 100) -> List[Dict]:
    with db_conn() as conn:
        if node:
            rows = conn.execute(
                """
                SELECT * FROM weather_samples
                WHERE UPPER(node) = UPPER(?)
                ORDER BY observed_at DESC
                LIMIT ?
                """,
                (node, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM weather_samples ORDER BY observed_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
    return [dict(r) for r in rows]


def run_demo_ingestion(node: str = "HB_HOUSTON") -> Dict:
    now = now_iso()
    upper_node = node.upper()
    seed = sum(ord(ch) for ch in upper_node)
    price = 48 + (seed % 20)
    vol = 22 + (seed % 12)
    temp = 27 + (seed % 6)
    wind = 5 + (seed % 4)
    cloud = 35 + (seed % 30)

    constraints = [
        {
            "id": str(uuid4()),
            "node": upper_node,
            "constraint_type": "POI_IMPORT_LIMIT",
            "limit_mw": 45 + (seed % 8),
            "status": "active",
            "source": "ercot_open_data_demo",
            "observed_at": now,
        },
        {
            "id": str(uuid4()),
            "node": upper_node,
            "constraint_type": "N-1_SECURITY_MARGIN",
            "limit_mw": 38 + (seed % 7),
            "status": "active",
            "source": "ercot_open_data_demo",
            "observed_at": now,
        },
    ]

    market_rows = [
        {
            "id": str(uuid4()),
            "node": upper_node,
            "price_usd_mwh": round(price, 2),
            "volatility_pct": round(vol, 2),
            "source": "ercot_open_data_demo",
            "observed_at": now,
        }
    ]

    weather_rows = [
        {
            "id": str(uuid4()),
            "node": upper_node,
            "temperature_c": round(temp, 2),
            "wind_speed_ms": round(wind, 2),
            "cloud_cover_pct": round(cloud, 2),
            "source": "open_meteo_demo",
            "observed_at": now,
        }
    ]

    run_id = str(uuid4())
    with db_conn() as conn:
        conn.executemany(
            """
            INSERT INTO grid_constraints (id, node, constraint_type, limit_mw, status, source, observed_at)
            VALUES (:id, :node, :constraint_type, :limit_mw, :status, :source, :observed_at)
            """,
            constraints,
        )
        conn.executemany(
            """
            INSERT INTO market_prices (id, node, price_usd_mwh, volatility_pct, source, observed_at)
            VALUES (:id, :node, :price_usd_mwh, :volatility_pct, :source, :observed_at)
            """,
            market_rows,
        )
        conn.executemany(
            """
            INSERT INTO weather_samples (id, node, temperature_c, wind_speed_ms, cloud_cover_pct, source, observed_at)
            VALUES (:id, :node, :temperature_c, :wind_speed_ms, :cloud_cover_pct, :source, :observed_at)
            """,
            weather_rows,
        )
        conn.execute(
            """
            INSERT INTO ingestion_runs (id, run_type, status, details_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                run_id,
                "bootstrap_demo",
                "ok",
                json.dumps({"node": upper_node, "constraints": len(constraints), "prices": len(market_rows), "weather": len(weather_rows)}),
                now,
            ),
        )

    return {
        "run_id": run_id,
        "node": upper_node,
        "ingested": {
            "grid_constraints": len(constraints),
            "market_prices": len(market_rows),
            "weather_samples": len(weather_rows),
        },
    }


def list_data_sources() -> List[Dict]:
    with db_conn() as conn:
        rows = conn.execute("SELECT * FROM data_sources ORDER BY created_at DESC").fetchall()
    out = []
    for r in rows:
        item = dict(r)
        item["config"] = json.loads(item["config_json"])
        del item["config_json"]
        out.append(item)
    return out


def get_data_source(source_id: str) -> Dict | None:
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM data_sources WHERE id = ?", (source_id,)).fetchone()
    if not row:
        return None
    data = dict(row)
    data["config"] = json.loads(data["config_json"])
    del data["config_json"]
    return data


def fetch_json(url: str, timeout_s: int = 12) -> Dict:
    with urlopen(url, timeout=timeout_s) as response:
        body = response.read().decode("utf-8")
        return json.loads(body)


def sync_source(source: Dict) -> Tuple[str, List[Dict]]:
    source_type = source["source_type"]
    config = source["config"]
    observations: List[Dict] = []

    if source_type == "weather_openmeteo":
        lat = float(config.get("lat", 29.7604))
        lon = float(config.get("lon", -95.3698))
        url = f"{source['base_url']}?{urlencode({'latitude': lat, 'longitude': lon, 'current': 'temperature_2m,wind_speed_10m,cloud_cover'})}"
        payload = fetch_json(url)
        current = payload.get("current", {})
        observations.extend(
            [
                {"metric_key": "temperature_2m", "metric_value": current.get("temperature_2m"), "payload": payload},
                {"metric_key": "wind_speed_10m", "metric_value": current.get("wind_speed_10m"), "payload": payload},
                {"metric_key": "cloud_cover", "metric_value": current.get("cloud_cover"), "payload": payload},
            ]
        )
        return "synced", observations

    if source_type == "ercot_open_data":
        api_key = config.get("eia_api_key", os.getenv("EIA_API_KEY", "DEMO_KEY"))
        params = {
            "api_key": api_key,
            "frequency": "hourly",
            "data[0]": "value",
            "facets[respondent][]": "ERCO",
            "sort[0][column]": "period",
            "sort[0][direction]": "desc",
            "offset": 0,
            "length": 3,
        }
        url = f"{source['base_url']}?{urlencode(params)}"
        payload = fetch_json(url)
        data = payload.get("response", {}).get("data", [])
        for item in data:
            observations.append(
                {
                    "metric_key": "ercot_open_value",
                    "metric_value": float(item.get("value", 0) or 0),
                    "payload": item,
                }
            )
        return "synced", observations

    return "unsupported_source_type", observations


def persist_observations(source_id: str, observations: List[Dict]) -> None:
    if not observations:
        return
    with db_conn() as conn:
        conn.executemany(
            """
            INSERT INTO source_observations (id, source_id, observed_at, metric_key, metric_value, payload_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    str(uuid4()),
                    source_id,
                    now_iso(),
                    obs.get("metric_key"),
                    obs.get("metric_value"),
                    json.dumps(obs.get("payload", {})),
                )
                for obs in observations
            ],
        )


def list_observations(source_id: str | None = None, limit: int = 50) -> List[Dict]:
    with db_conn() as conn:
        if source_id:
            rows = conn.execute(
                """
                SELECT * FROM source_observations
                WHERE source_id = ?
                ORDER BY observed_at DESC
                LIMIT ?
                """,
                (source_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM source_observations ORDER BY observed_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
    out = []
    for r in rows:
        row = dict(r)
        row["payload"] = json.loads(row["payload_json"])
        del row["payload_json"]
        out.append(row)
    return out


def storage_status() -> Dict:
    with db_conn() as conn:
        opportunities = conn.execute("SELECT COUNT(*) c FROM opportunities").fetchone()["c"]
        snapshots = conn.execute("SELECT COUNT(*) c FROM snapshots").fetchone()["c"]
        designs = conn.execute("SELECT COUNT(*) c FROM designs_v2").fetchone()["c"]
        sources = conn.execute("SELECT COUNT(*) c FROM data_sources").fetchone()["c"]
        observations = conn.execute("SELECT COUNT(*) c FROM source_observations").fetchone()["c"]
        constraints = conn.execute("SELECT COUNT(*) c FROM grid_constraints").fetchone()["c"]
        prices = conn.execute("SELECT COUNT(*) c FROM market_prices").fetchone()["c"]
        weather = conn.execute("SELECT COUNT(*) c FROM weather_samples").fetchone()["c"]
    return {
        "db_path": DB_PATH,
        "opportunities": opportunities,
        "snapshots": snapshots,
        "designs_v2": designs,
        "data_sources": sources,
        "source_observations": observations,
        "grid_constraints": constraints,
        "market_prices": prices,
        "weather_samples": weather,
        "engine_version": ENGINE_VERSION,
        "cloud_ready": True,
    }


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
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/":
            self._send(200, {"name": "SCENI", "status": "ok", "engine_version": ENGINE_VERSION})
            return
        if path == "/health":
            self._send(200, {"status": "healthy"})
            return
        if path == "/api/v1/storage/status":
            self._send(200, storage_status())
            return
        if path == "/api/v1/opportunities":
            self._send(200, list_opportunities())
            return
        if path == "/api/v1/data-sources":
            self._send(200, list_data_sources())
            return
        if path == "/api/v1/observations":
            source_id = query.get("source_id", [None])[0]
            limit = int(query.get("limit", ["50"])[0])
            self._send(200, list_observations(source_id=source_id, limit=limit))
            return
        if path == "/api/v1/network/constraints":
            node = query.get("node", [None])[0]
            limit = int(query.get("limit", ["100"])[0])
            self._send(200, list_grid_constraints(node=node, limit=limit))
            return
        if path == "/api/v1/market/prices":
            node = query.get("node", [None])[0]
            limit = int(query.get("limit", ["100"])[0])
            self._send(200, list_market_prices(node=node, limit=limit))
            return
        if path == "/api/v1/weather":
            node = query.get("node", [None])[0]
            limit = int(query.get("limit", ["100"])[0])
            self._send(200, list_weather_samples(node=node, limit=limit))
            return
        if path.startswith("/api/v1/market/ercot/"):
            node = path.split("/api/v1/market/ercot/")[-1]
            self._send(200, market_for_node(node))
            return
        if path.startswith("/api/v1/opportunities/") and path.endswith("/designs"):
            opportunity_id = path.split("/")[4]
            rows = list_designs(opportunity_id)
            if rows is None:
                self._send(404, {"error": "Opportunity not found"})
                return
            self._send(200, rows)
            return
        if path.startswith("/api/v1/snapshots/"):
            snapshot_id = path.split("/api/v1/snapshots/")[-1]
            snapshot = get_snapshot(snapshot_id)
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
                        "GET /api/v1/storage/status",
                        "POST /api/v1/opportunities",
                        "POST /api/v1/opportunities/{id}/simulate",
                        "GET /api/v1/opportunities/{id}/designs",
                        "GET /api/v1/snapshots/{snapshot_id}",
                        "GET /api/v1/market/ercot/{node}",
                        "GET /api/v1/data-sources",
                        "POST /api/v1/data-sources",
                        "POST /api/v1/data-sources/{id}/sync",
                        "GET /api/v1/observations?source_id=<id>",
                        "GET /api/v1/network/constraints?node=HB_HOUSTON",
                        "GET /api/v1/market/prices?node=HB_HOUSTON",
                        "GET /api/v1/weather?node=HB_HOUSTON",
                        "POST /api/v1/ingestion/bootstrap-demo",
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
                self._send(200, create_opportunity(payload))
                return
            except Exception as exc:
                self._send(400, {"error": str(exc)})
                return

        if path.startswith("/api/v1/opportunities/") and path.endswith("/simulate"):
            opportunity_id = path.split("/")[4]
            result = run_simulation(opportunity_id)
            if result.get("status") == 404:
                self._send(404, {"error": result["error"]})
                return
            self._send(200, result)
            return

        if path == "/api/v1/data-sources":
            try:
                payload = self._parse_json()
                required = ["name", "source_type", "base_url"]
                for field in required:
                    if field not in payload:
                        self._send(400, {"error": f"Missing field: {field}"})
                        return
                self._send(200, create_data_source(payload))
                return
            except Exception as exc:
                self._send(400, {"error": str(exc)})
                return

        if path.startswith("/api/v1/data-sources/") and path.endswith("/sync"):
            source_id = path.split("/")[4]
            source = get_data_source(source_id)
            if not source:
                self._send(404, {"error": "Data source not found"})
                return

            try:
                status, observations = sync_source(source)
                persist_observations(source_id, observations)
                with db_conn() as conn:
                    conn.execute(
                        "UPDATE data_sources SET status = ?, last_sync_at = ? WHERE id = ?",
                        (status, now_iso(), source_id),
                    )
                self._send(
                    200,
                    {
                        "source_id": source_id,
                        "status": status,
                        "ingested": len(observations),
                        "preview": observations[:2],
                    },
                )
                return
            except Exception as exc:
                with db_conn() as conn:
                    conn.execute(
                        "UPDATE data_sources SET status = ?, last_sync_at = ? WHERE id = ?",
                        (f"error: {exc}", now_iso(), source_id),
                    )
                self._send(502, {"error": f"Source sync failed: {exc}"})
                return

        if path == "/api/v1/ingestion/bootstrap-demo":
            try:
                payload = self._parse_json()
                node = payload.get("node", "HB_HOUSTON")
                self._send(200, run_demo_ingestion(node=node))
                return
            except Exception as exc:
                self._send(400, {"error": str(exc)})
                return

        self._send(404, {"error": "Not found"})


def main():
    init_db()
    server = HTTPServer(("0.0.0.0", 8000), Handler)
    print(f"SCENI backend en http://localhost:8000 | DB: {DB_PATH}")
    server.serve_forever()


if __name__ == "__main__":
    main()
