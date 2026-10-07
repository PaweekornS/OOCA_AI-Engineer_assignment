# Support Ticket Triage Agent (OOCA AI Engineer Test)

An autonomous AI agent designed to triage incoming customer support tickets, classify urgency, retrieve internal documentation/system telemetry, and determine operational routing actions using **LangGraph**, **OpenAI GPT**, **Pydantic v2**, and **Rich**.

---

## 🚀 Key Features

* **Cyclic ReAct State Machine (LangGraph):** Decouples iterative tool calling from structured output generation with hard loop limits (`max_tool_calls = 3`).
* **Multi-Turn Thread Analysis:** Analyzes chronological conversation history, customer sentiment trajectory, and customer SLA tier.
* **Deterministic Guardrails & PDPA Compliance:**
  * Regex PII scrubber masks card numbers, CVVs, and emails before sending to LLM.
  * Zero-financial-commitment policy prohibits promising refunds or instant card reversals.
  * Discrepancy override prioritizes customer-reported HTTP 500 errors over lagging status pages.
  * Cross-lingual mirroring generates polite, formal Thai responses (`ครับ/ค่ะ`) for Thai tickets.
* **Realistic Unstructured Knowledge Base (`data/kb/`):** Real-world markdown policies with deliberate knowledge gaps for unreleased features.
* **Rich Terminal UI:** Formatted inspection cards, timeline tables, and decision summaries.

---

## 📋 Prerequisites & Installation

### 1. Clone & Set up Virtual Environment

```powershell
# Navigate to project directory
cd c:\Users\punso\Downloads\OOCA_AI-Eng-test

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy the example environment configuration:

```powershell
copy .env.example .env
```

Open `.env` and provide your OpenAI API Key:
```ini
OPENAI_API_KEY=sk-proj-your-api-key-here
OPENAI_MODEL_NAME=gpt-4o-mini
OPENAI_TEMPERATURE=0.0
MAX_TOOL_CALLS=3
```

*(Alternatively, you can export `OPENAI_API_KEY` in your terminal shell).*

---

## 💻 Running the Application

### 1. Run All Benchmark Scenarios (Default)
Runs Scenarios 1 (Billing Dispute), 2 (Enterprise Outage), and 3 (Dark Mode Bug / Feature):
```powershell
python main.py
```

### 2. Run a Specific Scenario
```powershell
# Run Scenario 1 (Billing & Duplicate Charges)
python main.py --ticket 1

# Run Scenario 2 (Enterprise Outage & Asia Region 500)
python main.py --ticket 2

# Run Scenario 3 (macOS Appearance Theme Sync Bug & Feature Request)
python main.py --ticket 3
```

### 3. Machine-Readable JSON Output
```powershell
python main.py --all --json
```

### 4. Run as Production FastAPI Backend Server
Start the high-performance HTTP server with interactive Swagger OpenAPI documentation:

```powershell
# Option A: Via project CLI runner
python main.py --serve --port 8000

# Option B: Via Uvicorn directly
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
```

Once running, access the interactive API docs at:
* **Interactive Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **ReDoc Documentation:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
* **Health Check Probe:** `GET http://127.0.0.1:8000/health`
* **Triage Stored Ticket by ID:** `POST http://127.0.0.1:8000/api/v1/triage` (Accepts `{ "ticket_id": "TICKET-001" }`)
* **Real-time Live Chat Triage:** `POST http://127.0.0.1:8000/api/v1/triage/realtime` (Accepts `{ "message": "...", "ticket_id": "TICKET-001" }`)
* **Tenant-Safe Audit Trail:** `GET http://127.0.0.1:8000/api/v1/audit/logs/{ticket_id}` (Enforces ticket isolation, prevents cross-tenant data leak)




---

## 🧪 Running Automated Tests

Run the test suite verifying tools, knowledge gaps, PII sanitization, and graph transitions:

```powershell
pytest tests/ -v
```

---

## 📂 Project Structure

```text
OOCA_AI-Eng-test/
├── docs/
│   ├── REQUIREMENTS.md         # Problem specifications
│   ├── EDGE_CASE.md            # Production edge cases & architectural nuances
│   ├── SYSTEM_DESIGN.md        # Technical architecture & LangGraph specification
│   └── AGENTIC_DESIGN.md       # Comparative analysis & enterprise scaling roadmap
├── writeup.md                  # 1-Page architecture & evaluation summary
├── README.md                   # This document
├── requirements.txt            # Python dependencies
├── .env.example                # Configuration template
├── main.py                     # Rich CLI runner entrypoint
├── data/
│   ├── sample_tickets.json     # 3 Canonical test tickets (12 messages)
│   └── kb/                     # Internal markdown knowledge base
│       ├── billing_refund_policy.md
│       ├── incident_sev1_runbook.md
│       ├── macos_desktop_known_issues.md
│       └── account_security_faq.md
├── src/
│   ├── api/
│   │   ├── __init__.py         # FastAPI application package
│   │   ├── app.py              # Endpoints, middleware & lifecycles
│   │   └── schemas.py          # Request & Response Pydantic DTOs
│   ├── config.py               # Pydantic settings & environment configuration
│   ├── state.py                # LangGraph TriageState schema
│   ├── models/
│   │   ├── domain.py           # Inbound ticket & message schemas
│   │   └── triage.py           # TriageDecision & classification enums
│   ├── tools/
│   │   ├── base.py             # Tool bundle registry (get_triage_tools)
│   │   ├── knowledge_tools.py  # Hybrid Search KB lookup engine (BM25 + Dense Embeddings + RRF)
│   │   ├── system_tools.py     # Regional health & infrastructure telemetry tool
│   │   ├── billing_tools.py    # Payment gateway (Stripe) ledger & auth-hold inspector
│   │   └── ticket_tools.py     # CRM historical tickets & SLA commitment inspector
│   ├── prompts/
│   │   ├── system_prompt.py    # Master ReAct instructions & guardrails
│   │   └── extraction_prompt.py# Structured output synthesis prompt
│   ├── graph/
│   │   ├── nodes.py            # LangGraph node implementations
│   │   ├── edges.py            # Conditional routing logic
│   │   └── workflow.py         # Compiled StateGraph definition
│   └── utils/
│       ├── formatting.py       # Rich terminal UI components
│       ├── audit_logger.py     # Structured audit trail (logs/triage_audit.jsonl)
│       ├── response_templates.py # Guardrailed response templates
│       └── pii_sanitizer.py    # PDPA/GDPR PII masking utility
└── tests/
    ├── test_api.py             # FastAPI integration & validation tests
    ├── test_audit_logger.py    # Structured audit logging unit tests
    ├── test_tools.py           # KB lookup & system status unit tests
    ├── test_guardrails.py      # PII scrubbing & financial promise policy tests
    └── test_triage.py          # State machine transitions & compilation tests
```

