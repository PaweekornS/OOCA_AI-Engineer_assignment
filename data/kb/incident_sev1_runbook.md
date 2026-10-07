# Engineering & Support Runbook: Sev-1 Outages & Regional Incidents

* **Document ID:** RUN-OPS-500-ASIA  
* **Owner:** Site Reliability Engineering (SRE) & Incident Management  
* **Last Updated:** September 2024  
* **Target Audience:** Frontline Support, Incident Commanders, DevOps On-Call  

---

## 1. Severity Classification
* **Sev-1 (Critical Outage):** Core service completely inaccessible, customer operations halted, active multi-tenant HTTP 500 errors, or Enterprise customer facing revenue/demo risk.
* **Target Response SLA:** Enterprise Platinum tier accounts (20+ seats) carry a contractually guaranteed **15-minute response SLA**.

## 2. Infrastructure Lag & The Status Page Discrepancy Rule
Our public status dashboard (`status.company.com`) relies on automated synthetic HTTP health probes running from centralized US-East ping monitors.

### ⚠️ The Status Page Discrepancy Rule:
* **Synthetic Probe Delay:** Synthetic health monitors typically experience a **15 to 30-minute lag** before detecting localized edge node or regional CDN failures (specifically in the Asia-Pacific / Thailand region).
* **Ground Truth Rule:** If an Enterprise customer reports:
  1. Complete system inaccessibility with **HTTP 500 Internal Server Error**
  2. Verified across **multiple workstations** and **multiple distinct browsers** (e.g., Chrome, Safari, Firefox)
  3. Confirmed by multiple team members/colleagues
* **Action:** **This customer evidence directly supersedes a "Green / Operational" status page.** Support agents must **NEVER** reply stating "Everything is operating normally on our status page."

## 3. Incident Escalation & Communication Protocol
1. **Immediate Escalation:** Escalate the ticket immediately to **DevOps / On-Call Incident Commander** under **Critical (Sev-1)** urgency.
2. **Customer Acknowledgment:**
   * Send an immediate polite acknowledgment mirroring the customer's native language.
   * For **Thai Enterprise clients**, use formal, professional business Thai with polite particles (`ครับ/ค่ะ`).
   * Explicitly confirm that our engineering team is actively investigating regional edge routing in the **Asia region**.
   * Reassure the client that their report has been paged directly to senior infrastructure engineers.
