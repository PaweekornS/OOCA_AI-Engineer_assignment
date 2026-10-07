"""System health and regional infrastructure telemetry tool."""

from typing import Optional
from langchain_core.tools import tool


@tool
def check_system_status(region: Optional[str] = None) -> str:
    """Checks the operational status of server infrastructure, regional edge nodes, and public status monitors.

    Args:
        region: Geographic region to inspect (e.g. 'Asia', 'Thailand', 'US-East', 'Global'). Defaults to Global.

    Returns:
        Telemetry report comparing public status page monitors with real-time internal edge telemetry.
    """
    region_str = (region or "global").lower()

    if any(k in region_str for k in ["asia", "thailand", "bkk", "apac"]):
        return (
            "--- Regional Infrastructure Health Report (Asia / Thailand) ---\n"
            "Public Status Dashboard (status.company.com): Operational (Green - All Systems Normal)\n"
            "Internal Edge Telemetry (BKK-AP1 Cluster):\n"
            "  * Status: DEGRADED / ELEVATED FAILURES\n"
            "  * Error Rate: 16.4% HTTP 500 Internal Server Errors detected on core API gateway\n"
            "  * Root Cause: Border Gateway Protocol (BGP) route flap affecting Southeast Asia CDN edge nodes\n"
            "  * Probe Lag: Synthetic health probes report 20-minute cache delay\n"
            "Recommendation: Sev-1 escalation to DevOps / On-Call Incident Commander immediately."
        )

    if any(k in region_str for k in ["us", "north america", "global"]):
        return (
            "--- Regional Infrastructure Health Report (US-East / Global) ---\n"
            "Public Status Dashboard: Operational (Green)\n"
            "Internal Telemetry (US-East Primary):\n"
            "  * Status: HEALTHY\n"
            "  * Error Rate: 0.02% (within normal SLA parameters)\n"
            "  * Payment Gateway Webhooks: 99.8% delivery rate"
        )

    return (
        f"--- Telemetry for Region: {region} ---\n"
        "Public Status Dashboard: Operational (Green)\n"
        "No active global outages detected on central monitors. Check localized edge metrics if multiple tenants report HTTP 500."
    )
