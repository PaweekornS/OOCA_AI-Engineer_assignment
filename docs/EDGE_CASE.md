
# Architectural Considerations & Production Edge Cases

### Support Ticket Triage Agent (OOCA Engineering Homework)

This document outlines key technical and architectural nuances intentionally unstated in the baseline problem statement. Factoring in these edge cases distinguishes a naive text-classifier from a robust, production-grade AI Agent.

---

## 1. SLA & Tier-Based Prioritization (Beyond FIFO Queuing)

* **The Problem:**
  Standard ticket intake treats tickets on a First-Come, First-Served (FIFO) basis. Treating a Free user's dark-mode inquiry before an Enterprise client's system-down outage violates contractual Service Level Agreements (SLAs).
* **Specific Edge Cases in Test Set:**
  - **Ticket 2:** Enterprise tier, 45 seats, facing a revenue-blocking outage with an upcoming demo. Missing this SLA can trigger contractual penalties or client churn.
  - **Ticket 1:** Free user, but actively attempting to convert to Pro with multiple failed charges. While technically "Free", the financial and chargeback risk demands expedited handling over idle tickets.
* **Proposed Solution:**
  Implement a dynamic composite urgency scoring matrix inside the System Prompt and routing rules:
  $$
  \text{Effective Urgency} = f(\text{Technical Severity}, \text{Customer Tier Multiplier}, \text{Financial/Churn Risk})
  $$

  - `Enterprise` incidents receive an automatic baseline boost to `critical` or `high`.
  - Intent-to-convert users with billing friction bypass standard community/delayed queues.

---

## 2. Action Boundaries & Autonomous Agent Authority

* **The Problem:**
  Allowing an autonomous LLM agent to finalize sensitive actions (such as authorizing refunds or declaring regional outages resolved) creates high business and liability risks.
* **Specific Edge Cases in Test Set:**
  - **Ticket 1:** Customer was charged 3 times ($29.99 x 3) without receiving access. If the LLM generates an `auto-respond` promising *"Your $89.97 refund has been processed"*, it commits the company to financial transactions it cannot verify.
* **Proposed Solution:**
  - **Hard Guardrails:** Enforce explicit non-commitment boundaries in system instructions. AI is strictly forbidden from guaranteeing monetary compensation, refunds, or system recovery times.
  - **Dual Action Pattern:** In severe scenarios, `auto-respond` must act only as an immediate customer acknowledgment (e.g., *"We acknowledge this critical incident and have paged our On-Call Engineer"*), while the operational action is routed to `escalate_to_human` or `route_to_specialist`.

---

## 3. Discrepancy Between Customer Evidence & External Dashboards

* **The Problem:**
  Internal or external status indicators (e.g., status monitors, health-check APIs) often experience lag (15–30 minutes) before synthetic monitors register regional CDN or edge failures.
* **Specific Edge Cases in Test Set:**
  - **Ticket 2:** Customer states `status.company.com` shows "all systems operational", but all users across Chrome, Safari, and Firefox encounter HTTP 500 errors. If the agent queries a status tool and naively trusts the "Green/Healthy" output, it might classify the ticket as a local client configuration error.
* **Proposed Solution:**
  - Incorporate a **Heuristic Override Rule**: Multi-user, multi-browser reports of HTTP 500 from Enterprise tenants supersede healthy dashboard status indicators.
  - Tool interpretation logic must treat dashboard data as a historical indicator, not absolute truth, escalating unexpected client-reported outages as potential zero-day incidents.

---

## 4. Multi-Turn Thread Progression & Sentiment Trajectory

* **The Problem:**
  Treating each ticket message in isolation loses the cumulative customer context, and calculating sentiment from only the latest message misses the duration the customer has waited without support.
* **Specific Edge Cases in Test Set:**
  - **Ticket 1:** Messages progress chronologically across 3 hours from polite inquiry -> confusion -> frustration -> dispute threats.
  - **Ticket 3:** Transitions from general feature inquiry -> troubleshooting settings -> reporting a potential OS sync bug -> suggesting a feature enhancement.
* **Proposed Solution:**
  - **Thread-Level Context Injection:** Ingest messages as an ordered dialogue array containing relative timestamps and deltas.
  - **Frustration Velocity Calculation:** Track whether customer sentiment is deteriorating due to lack of response. Escalating anger over multiple unattended hours increases urgency regardless of the base issue type.

---

## 5. Infinite Execution Loops & Retrieval Fallbacks

* **The Problem:**
  In a ReAct / LangGraph agent loop, if the Knowledge Base query returns empty results or ambiguous hits, the LLM may hallucinate repeated alternative search terms indefinitely, causing high latency and API cost runaway.
* **Proposed Solution:**
  - **Graph Recursion Limit:** Cap agent execution transitions (e.g., `recursion_limit=5`).
  - **Tool Call Threshold:** If `lookup_knowledge_base` is invoked 2 times without finding confidence-backed matches, the graph transitions directly to a fallback node routing the ticket to human triage (`route_to_specialist` or `escalate_to_human`).

---

## 6. Data Privacy & PII Handling (Healthcare & Financial Context)

* **The Problem:**
  Customer inquiries often contain sensitive identifiers (credit card fragments, account credentials, or in OOCA's context, protected personal/health disclosures). Passing raw PII directly to LLM providers creates compliance exposure (PDPA / GDPR / HIPAA).
* **Specific Edge Cases in Test Set:**
  - **Ticket 1:** Discussion of credit card attempts, transaction amounts, and potential bank disputes.
* **Proposed Solution:**
  - Implement a pre-processing sanitization layer before feeding raw ticket bodies into the LangGraph state.
  - Regex or rule-based token masking for credit card patterns, phone numbers, and transactional account IDs.

---

## 7. Cross-Lingual & Cultural Nuance (Thai vs. English)

* **The Problem:**
  Language-agnostic models can default to replying in English regardless of the input language, or output overly robotic direct translations that fail local enterprise business etiquette.
* **Specific Edge Cases in Test Set:**
  - **Ticket 2:** Entirely in Thai, containing urgent business expressions (e.g., *"ลูกค้าโวยเข้ามาเยอะมาก"*, *"deal นี้อาจจะหลุด"*).
* **Proposed Solution:**
  - Require the final response generation node to detect the input language and mirror it in the `draft_response`.
  - For Thai Enterprise communications, enforce polite formal particles (ครับ/ค่ะ), professional tone, and clear acknowledgment of operational urgency.
