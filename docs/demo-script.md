# Demo Script & Walkthrough

This document serves as a step-by-step guide to executing and presenting the platform demo. It demonstrates exactly how the system fulfills the core requirements for Planning, Retrieval, Verification, Action, and Trace Review.

---

## 1. Running the Demo

To trigger the automated demonstration, run the demo script from inside the `agentops` directory:

```bash
cd agentops
./demo.sh
```

*(Alternatively, run `make serve` to trigger the exact same workflow visually via the Web UI at `http://localhost:8000`).*

Below is a breakdown of exactly what happens under the hood as the execution trace runs.

---

## 2. Planning Phase
* **What happens**: The incident (`checkout-api` experiencing high latency and 5xx errors) first hits the **Planner Agent**. Instead of relying on open-ended LLM chatting, the Planner strictly decomposes the raw alert into a structured, typed Pydantic task (`InvestigationTask`).
* **Observable Output**: You will see `[planner] -> INVESTIGATING`.
* **Behind the scenes**: The agent identifies the target service (`checkout-api`) and formulates a specific, scoped investigation objective rather than guessing what to do next.

---

## 3. Retrieval Phase
* **What happens**: Next, the workflow transitions to the **Investigator Agent**.
* **Observable Output**: You will see `[investigator] -> SYNTHESIZING_EVIDENCE`.
* **Behind the scenes**: The Investigator uses hybrid search (FTS5 Lexical + semantic retrieval) to query the runbook database using the Planner's exact objective. It retrieves the specific runbook for `checkout-api` (`rb-checkout-5xx`) and extracts actionable citations and confidence-scored evidence (e.g., *"When checkout-api experiences >5% 5xx errors... recommended action: scale checkout-api replicas by 50%"*).

---

## 4. Verification (Safety Boundary)
* **What happens**: Based on the retrieved evidence, the **I&O Agent** proposes an infrastructure action (`simulate_scale` to 50 replicas). However, the LLM is physically incapable of executing this action directly. The proposal must pass through the deterministic **Safety Verifier**.
* **Observable Output**: You will see `[verifier] -> VERIFYING_SAFETY` followed by `Safety Decision: ALLOW` (or `REQUIRE_APPROVAL` depending on autonomy tier).
* **Behind the scenes**: The Verifier calculates the blast radius using a NetworkX dependency graph and cross-references hardcoded autonomy and invariant rules (e.g., hard ceiling on maximum replicas). Because the Verifier is pure deterministic Python policy (never an LLM), it guarantees the system fails closed and remains 100% safe for production.

---

## 5. Action Phase
* **What happens**: Because the deterministic policy passed, the workflow transitions to the Execution phase.
* **Observable Output**: You will see `[execute] -> COMPLETED` and `Execution: Simulated scale of checkout-api to 50 replicas successful.`
* **Behind the scenes**: The validated action is routed through the **Tool Gateway**, which acts as an interceptor for simulated actions with idempotency keys, preventing unmonitored infrastructure mutations while proving the end-to-end integration works.

---

## 6. Trace Review (Auditability & Replay)
* **What happens**: For production compliance, every single step, envelope message, and safety decision was asynchronously recorded to an append-only SQLite event log.
* **How to verify**: Notice the Run ID from the demo output (e.g., `run-2ab4f006`). Run the audit replay:

```bash
uv run agentops trace-show <run-id>
```

* **Outcome**: This produces the complete, sequential audit trail of all 6 events (`IncidentReceived`, `InvestigationTask`, `EvidenceBundle`, `RemediationProposal`, `SafetyDecision`, `ExecutionResult`), proving that the platform maintains a 100% reproducible, auditable record of what the AI did and why the deterministic policy approved it.
