# Trade-offs & Production Hardening

Building a safe agentic platform in a 3-day timebox required several intentional simplifications. Here is a breakdown of what was simplified for this prototype, and how it would be hardened for a true production environment.

---

## 1. Simplifications Made for the Prototype

### A. The FakeModelGateway (LLM Mocking)
* **What we did**: Implemented a `FakeModelGateway` that returns deterministic Pydantic objects based on the input schema.
* **Why**:
  1. To guarantee deterministic evaluation in CI without requiring the evaluator to supply OpenAI / Gemini API keys.
  2. To stay within the timebox while still proving the structural integrity of the LangGraph state machine.
* **Trade-off**: The system doesn't dynamically reason over unseen incidents. It proves the plumbing and safety bounds, but not the open-ended reasoning of the agent.

### B. SQLite for Trace Persistence & Retrieval
* **What we did**: Used a local `agentops.db` file for both the append-only event log (tracing) and the FTS5 hybrid search (runbooks).
* **Why**: Zero-infrastructure setup. Reviewers can clone and run it instantly without Docker containers or remote services.
* **Trade-off**: SQLite is not scalable for distributed microservices tracing or billion-vector embeddings.

### C. NetworkX for Blast Radius Graph
* **What we did**: Used a local NetworkX graph loaded from a JSON file (`dependencies.json`) to calculate upstream/downstream dependencies.
* **Why**: It cleanly simulates graph traversal for blast-radius calculations without needing a remote graph database.
* **Trade-off**: NetworkX runs in-memory. Large enterprise dependency graphs would consume substantial memory in a standard container.

---

## 2. Hardening for Production

If this were moving to production, here is exactly how to harden the system:

### A. Real LLM Integration & Evals
* Swap the `FakeModelGateway` for `langchain-openai` or Anthropic/Gemini SDKs with strict JSON mode.
* Implement LLM-as-a-Judge evaluations using tools like LangSmith or Braintrust to evaluate the quality of the Planner and Investigator agents over a dataset of 500+ historical incidents.
* Add retry logic with exponential backoff for rate limits and malformed JSON schemas.

### B. Distributed Tracing & Observability
* Replace the SQLite `event_log` with an enterprise observability backend.
* Emit native OpenTelemetry (OTel) spans for every agent thought, tool call, and state transition.
* Send traces to Datadog, Honeycomb, or Jaeger so human operators can visualize the exact timeline of the agent's thought process during a live incident.

### C. Enterprise Retrieval (Vector DB)
* Replace SQLite FTS5 with a dedicated Vector Database like Qdrant, Pinecone, or Milvus.
* Set up a pipeline to automatically ingest and embed newly published runbooks, Confluence docs, and PagerDuty post-mortems so the Investigator Agent always has real-time context.

### D. Human-in-the-Loop (HITL) via Slack/Teams
* Currently, Tier 1/2 actions halt at `WAITING_FOR_APPROVAL` in the state machine.
* In production, this state transition must trigger an interactive Slack/Teams message to the on-call engineer:
  > *"AgentOps proposes scaling checkout-api to 50 replicas. Blast radius: Low. [Approve] [Deny] [Modify]"*
* The LangGraph process would safely suspend (via LangGraph checkpoints/Postgres) until the human clicks the webhook button.
