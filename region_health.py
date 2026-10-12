"""Meridian Labs region health tool (demo for the Agent Bricks CLI video).

Drop this file into agent/tools/ - the template auto-discovers every @tool in that folder.
Data is embedded so the tool works the same under `agentbricks dev` and after `agentbricks deploy`.
Verified as of 2026-10-05 with databricks-agentbricks 0.4.0.
"""

import csv
import io

from langchain_core.tools import tool

_DATA = """month,region,tier,active_accounts,churned_accounts,avg_first_response_hrs,csat
2026-07,NA,Free,2420,70,3.8,4.42
2026-07,NA,Pro,912,19,3.5,4.38
2026-07,NA,Enterprise,139,1,1.9,4.5
2026-07,Europe,Free,2040,67,4.6,4.41
2026-07,Europe,Pro,766,17,3.8,4.25
2026-07,Europe,Enterprise,122,1,2.2,4.3
2026-07,APAC,Free,1541,145,10.6,3.48
2026-07,APAC,Pro,530,33,9.8,3.67
2026-07,APAC,Enterprise,70,2,5.6,3.62
2026-07,LATAM,Free,917,38,5.4,4.32
2026-07,LATAM,Pro,303,7,3.8,4.24
2026-07,LATAM,Enterprise,34,1,2.3,4.23
2026-08,NA,Free,2419,75,3.9,4.41
2026-08,NA,Pro,887,19,3.3,4.53
2026-08,NA,Enterprise,137,1,1.9,4.46
2026-08,Europe,Free,2161,78,4.6,4.46
2026-08,Europe,Pro,796,18,3.4,4.26
2026-08,Europe,Enterprise,118,1,2.1,4.53
2026-08,APAC,Free,1533,144,11.9,3.57
2026-08,APAC,Pro,532,32,8.8,3.52
2026-08,APAC,Enterprise,70,2,5.8,3.72
2026-08,LATAM,Free,894,34,5.5,4.3
2026-08,LATAM,Pro,292,7,3.7,4.34
2026-08,LATAM,Enterprise,35,1,2.3,4.26
2026-09,NA,Free,2471,80,4.4,4.61
2026-09,NA,Pro,873,18,3.3,4.51
2026-09,NA,Enterprise,138,1,1.8,4.48
2026-09,Europe,Free,2094,80,4.8,4.33
2026-09,Europe,Pro,780,16,3.9,4.51
2026-09,Europe,Enterprise,118,1,2.3,4.3
2026-09,APAC,Free,1523,150,12.1,3.61
2026-09,APAC,Pro,504,30,8.3,3.73
2026-09,APAC,Enterprise,71,2,5.5,3.47
2026-09,LATAM,Free,920,40,4.6,4.3
2026-09,LATAM,Pro,292,8,4.2,4.19
2026-09,LATAM,Enterprise,34,1,2.4,4.41"""

_REGIONS = ("NA", "Europe", "APAC", "LATAM")


def _rows():
    return list(csv.DictReader(io.StringIO(_DATA)))


def _summarize(rows):
    active = sum(int(r["active_accounts"]) for r in rows)
    churned = sum(int(r["churned_accounts"]) for r in rows)
    resp = sum(float(r["avg_first_response_hrs"]) for r in rows) / len(rows)
    csat = sum(float(r["csat"]) for r in rows) / len(rows)
    return {
        "active_accounts": active,
        "churned_accounts": churned,
        "churn_rate_pct": round(100 * churned / active, 2),
        "avg_first_response_hrs": round(resp, 1),
        "avg_csat": round(csat, 2),
    }


def region_health_report(region: str = "all") -> dict:
    """Plain Python version of the tool, easy to unit test."""
    rows = _rows()
    region = (region or "all").strip()
    if region.lower() == "all":
        return {
            "period": "Q3 2026 (Jul-Sep)",
            "company": _summarize(rows),
            "by_region": {r: _summarize([x for x in rows if x["region"] == r]) for r in _REGIONS},
        }
    match = next((r for r in _REGIONS if r.lower() == region.lower()), None)
    if match is None:
        return {"error": f"Unknown region '{region}'. Use one of: {', '.join(_REGIONS)} or 'all'."}
    subset = [x for x in rows if x["region"] == match]
    return {
        "period": "Q3 2026 (Jul-Sep)",
        "region": match,
        "summary": _summarize(subset),
        "by_tier": {
            t: _summarize([x for x in subset if x["tier"] == t]) for t in ("Free", "Pro", "Enterprise")
        },
    }


@tool
def get_region_health(region: str = "all") -> dict:
    """Get Meridian Labs customer health for Q3 2026: churn rate, first response time and CSAT.

    Use region="all" to compare NA, Europe, APAC and LATAM side by side, or pass one region
    name to see its breakdown by tier (Free, Pro, Enterprise).
    """
    return region_health_report(region)
