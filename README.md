[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-2C3E50?style=flat-square&logo=python&logoColor=white)](https://github.com/langchain-ai/langgraph)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Package Manager: uv](https://img.shields.io/badge/package%20manager-uv-DE5D83?style=flat-square)](https://github.com/astral-sh/uv)
[![Tests: Pytest](https://img.shields.io/badge/tests-pytest-0A9EDC?style=flat-square&logo=pytest&logoColor=white)](https://docs.pytest.org/)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)

# Intel-Graph: Autonomous Multi-Agent Lead Intelligence Engine

A production-grade, stateful microservice that automates B2B outbound research and qualification pipelines. Built with **LangGraph**, **FastAPI**, and **Pydantic**, the system ingests corporate domains, extracts core product offerings via asynchronous scraping pipelines, dynamically evaluates criteria fit against a target Ideal Customer Profile (ICP), and structures context-aware cold outreach data.

## Key Architectural Frameworks

* **Stateful Orchestration:** Utilizes a cyclic LangGraph runtime graph to maintain workflow state context across autonomous node actions.
* **Deterministic Routing:** Uses runtime conditional edge routing to cleanly drop mismatched consumer (B2C) targets early, saving computational cycles and token expenditure.
* **Structured Data Boundaries:** Enforces strict JSON schemas using Pydantic parameters natively mapped to LLM tool extraction targets (`with_structured_output`).
* **Clean Scrape Isolation:** Implements custom `BeautifulSoup` document object pipelines to strip out script bloat and navigation text, processing lean text chunks below 6,000 characters.

---

## Project Blueprint

```text
intel-graph/
├── pyproject.toml              # Modern UV workspace dependencies configuration
├── README.md                   # Technical operational documentation
├── tests/                      # Automated test coverage suite
│   ├── __init__.py
│   ├── test_scraper.py         # Mocked HTTP response cleaning test logic
│   └── test_workflow.py        # Isolated LangGraph state edge routing verification
└── src/
    └── intel_graph/            # Core encapsulated codebase modules
        ├── __init__.py         # Package public API boundary definitions
        ├── state.py            # Pydantic schemas and graph state structures
        ├── nodes.py            # Execution steps (Research, Qualify, Copywrite)
        ├── app.py              # Compiled state machine orchestration logic
        └── server.py           # REST API exposure layer via FastAPI

```

---

## Prerequisites & Installation

This project leverages the modern **uv** package and environment manager for lightning-fast execution and deterministic virtual environment locking.

1. Clone this repository locally:
```bash
git clone https://github.com/AtulDeshpande09/intel-graph
cd intel-graph

```


2. Synchronize the local package virtual environment dependencies:
```bash
uv sync

```


3. Expose your inference endpoint access token to your active shell context:
```bash
export GROQ_API_KEY="your-actual-groq-api-key"

```

---

## Running the Streamlit Frontend

We have built a sleek, user-friendly frontend using Streamlit to make interacting with the multi-agent graph incredibly intuitive. 

To run the Streamlit UI locally alongside your running FastAPI server:

```bash
# Install Streamlit if you haven't already
uv add streamlit

# Spin up the frontend
uv run streamlit run src/intel_graph/app_ui.py --server.port 8501

```

Open `http://localhost:8501` in your browser to access the dashboard.

---

##  Running with Docker (Recommended)

The entire microservice stack (FastAPI backend + Streamlit frontend) is fully containerized. You can build and run the entire ecosystem with a single command without needing to set up Python dependencies locally.

### Prerequisites

Make sure you have your Groq API key set in your environment:

```bash
export GROQ_API_KEY="your-groq-api-key"

```

### Local Development Setup

Run the multi-container application locally:

```bash
# Build and start both services
docker compose up --build

```

* **FastAPI Backend Swagger Docs:** `http://localhost:8000/docs`
* **Streamlit Frontend Dashboard:** `http://localhost:8501`

---

##  Pulling Directly from Docker Hub

The production image for this project is public and hosted on Docker Hub. You can pull and run it instantly without even cloning this repository:

```bash
# Pull the latest image
docker pull atuldeshpande09/intel-graph:latest

# Run the container (make sure to pass your API key)
docker run -p 8501:8501 -e GROQ_API_KEY="your-groq-api-key" your_username/intel-graph:latest

```

---

## Executing the Microservice API

Start the asynchronous REST application server on your local machine using Uvicorn:

```bash
uv run uvicorn src.intel_graph.server:server --reload --port 8000

```

Once running, the fully documented interactive Swagger UI interface becomes available at `http://127.0.0.1:8000/docs`.

### REST API Integration Contract

**Endpoint:** `POST /api/research`

**Payload Schema:**

```json
{
  "domain": "stripe.com"
}

```

**Response Payload Structure (Qualified Output):**

```json
{
  "status": "Qualified & Drafted",
  "domain": "stripe.com",
  "logs": [
    "[System] Initiating data acquisition for: stripe.com",
    "[System] Data acquisition complete. Processing text via structured LLM schema.",
    "[Research Agent] Successfully isolated data payload for Stripe.",
    "[System] Initiating ICP qualification for Stripe...",
    "[Qualification Agent] Lead status: PASSED. Reason: B2B infrastructure software...",
    "[System] Drafting context-aware outreach sequence for Stripe...",
    "[Copywriter Agent] Completed outreach payload structure for Stripe."
  ],
  "intel": {
    "company_name": "Stripe",
    "core_product": "Financial infrastructure and payment processing APIs.",
    "target_audience": "B2B enterprise, developers, internet businesses.",
    "value_proposition": "Accept payments, send payouts, and manage businesses online.",
    "estimated_tech_stack": ["AWS", "SaaS", "APIs"]
  },
  "qualification": {
    "is_fit": true,
    "confidence_score": 0.98,
    "justification": "Matches exact B2B profile; sells technology directly to enterprise entities."
  },
  "outreach": {
    "subject_line": "Scaling financial workflows for Stripe pipelines",
    "email_body": "...",
    "personalized_hook": "Integrating live payment APIs natively for business scaling metrics."
  }
}

```

---

## Verification & Automated Test Suite

The workflow includes robust test coverage ensuring data cleaning integrity and graph edge resilience using `pytest` and `pytest-mock`. The test layer intercepts network requests, checking HTML cleanup logic and state management flows safely without executing expensive external live connections.

To execute the test pipeline verification framework, invoke the test runner with the source folder bound to the Python path configuration directly:

```bash
GROQ_API_KEY="mock-key" PYTHONPATH=src uv run pytest -v

```
