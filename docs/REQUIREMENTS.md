# Software Requirements Specification (SRS): Support Ticket Triage Agent

## 1. Project Overview & Context

- **Role & Scope:** AI Support Ticket Triage Agent designed to classify, analyze, retrieve context, and decide the next operational action for inbound customer tickets.
- **Model Requirement:** OpenAI GPT model family. The test evaluator will supply their own API key via environment variables; do not hardcode credentials.
- **Interface:** Terminal / CLI runner or lightweight API (No web or chat UI required).
- **Core Evaluation Dimensions:** Evaluated on Readability, Maintainability, Extensibility, and Logic.

---

## 2. Core Functional Requirements

The agent processes multi-turn conversation threads alongside customer account profiles to deliver 5 primary capabilities:

1. **Urgency Classification:** Categorize ticket priority into four standard levels: `critical`, `high`, `medium`, or `low`.
2. **Information Extraction:** Extract key structured entities:
   - **Product/Feature:** The specific product or functional module involved.
   - **Issue Type:** The technical or domain category (e.g., billing/payment, system outage, bug report, feature request).
   - **Customer Sentiment:** Customer emotional state inferred from conversational tone and escalation progression.
3. **Knowledge Base Retrieval:** Perform knowledge lookups against mock internal docs/FAQs to surface relevant troubleshooting guidelines or policies.
4. **Next Action Determination:** Select the operational next step from three paths:
   - `auto-respond`: Formulate an automated resolution response directly to the user.
   - `route_to_specialist`: Direct the ticket to dedicated domain teams (e.g., Billing Operations, Product Team).
   - `escalate_to_human`: Hand off immediately to on-call engineers, incident commanders, or senior human staff.
5. **Tool Usage:** Leverage at least 2 functional tools during triage (e.g., searching the knowledge base, retrieving customer account records).

---

## 3. Workflow & Orchestration Architecture

- **Framework:** LangGraph state machine orchestrating a cyclic ReAct/Tool-calling loop.
- **Node Lifecycle:**
  1. **Ingestion & Reasoning (`call_agent`):** Ingests the customer profile and message history, evaluating whether external tools are needed to verify facts or fetch policies.
  2. **Tool Execution (`run_tools`):** Executes requested tools dynamically and returns tool outputs back to the graph state.
  3. **Triage Finalization (`finalize_triage`):** Synthesizes collected context, classifies urgency and metadata, decides the next action, and outputs the structured decision.
- **Safety & Control Flow:**
  - Graph recursion limits to prevent infinite execution loops during unresolvable lookups.
  - Fallback transitions routing directly to human escalation if tools fail or return inconclusive data.

---

## 4. Required Tools Specification

System must implement at least two mock tools:

1. **`lookup_knowledge_base`:** Searches internal documentation, policies, and known issue registries covering:
   - Bank authorization holds vs. settled charges and refund SLAs.
   - HTTP 500 incident protocols and status page synchronization delays.
   - macOS dark mode system syncing limitations and feature backlogs.
2. **`check_customer_history`:** Queries mock customer database records to retrieve active subscription tier, SLA commitments, billing status, or historical ticket volumes.

---

## 5. Mock Test Scenarios

### Scenario 1: Billing & Payment Dispute

- **Customer Context:** Free plan (attempted upgrade to Pro), 4-month tenure, first support contact.
- **Message Progression:**
  - Message 1 (3h ago): Payment failure notification while attempting to upgrade to Pro.
  - Message 2 (2h ago): Retried with another card; two pending charges visible but account remains on Free plan.
  - Message 3 (1h ago): Three separate charges of $29.99 posted without refund or Pro access.
  - Message 4 (just now): Demands immediate fix before a presentation in 2 hours; threatens bank chargeback disputes by end of day.
- **Expected Outcome:** High/Critical urgency due to chargeback threat and presentation deadline; route to Billing Specialist or escalate to human; strictly avoid autonomous financial promises.

### Scenario 2: Enterprise Outage & Revenue Impact

- **Customer Context:** Enterprise tier, Thailand region, 45 seats, 8-month tenure, first critical issue.
- **Message Progression (Thai):**
  - Message 1 (2h ago): System inaccessible with HTTP 500 error.
  - Message 2 (1.5h ago): Confirmed across multiple machines and browsers (Chrome, Safari, Firefox); colleagues also blocked.
  - Message 3 (45m ago): Inbound customer complaints rising; major afternoon client demo at risk of deal cancellation.
  - Message 4 (just now): Status page reports all systems operational, but service remains down; asks to check Asia region.
- **Expected Outcome:** Critical urgency; Sev-1 escalation to DevOps / On-call Incident Team; draft bilingual/Thai acknowledgment matching enterprise tone; prioritize customer reality over lagging status page.

### Scenario 3: Feature Inquiry & Usability Bug

- **Customer Context:** Pro plan, 5-month tenure, daily active user, zero prior tickets.
- **Message Progression:**
  - Message 1 (2d ago): Casual inquiry about Dark Mode availability ("No rush").
  - Message 2 (1d ago): Located Appearance settings, but only sees "Light" and "System Default" options.
  - Message 3 (1d ago, +3h): Switched to "System Default" with Mac in dark mode, but the application remains light.
  - Message 4 (today): Inquires about auto-scheduled dark mode (e.g., 6 PM switch) as an idea.
- **Expected Outcome:** Low urgency; auto-respond with KB troubleshooting for macOS sync known issue and log scheduled dark mode as a product feature request.

---

## 6. Deliverables Checklist

- [ ] **Executable Source Code:** LangGraph-driven application capable of processing all provided sample tickets.
- [ ] **System Prompts:** Clear prompt definitions incorporating domain rules, tier prioritization, and safety guardrails.
- [ ] **Tool Implementations:** Python implementations for knowledge lookup and customer records with mock backend data.
- [ ] **README.md:** Complete setup guide including virtual environment setup, package installation, environment variables, and execution commands.
- [ ] **writeup.md (Max 1 Page):**
  - Architecture rationale and trade-offs.
  - Failure modes and mitigation mechanisms.
  - Production evaluation and observability strategy.
