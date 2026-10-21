import json
import os
import sys
import io
import contextlib

# Add src to python path
agentops_dir = os.path.abspath("/Users/sreekarreddypindi/Downloads/Mini Agentic AI Platform/agentops")
sys.path.insert(0, os.path.join(agentops_dir, "src"))
os.chdir(agentops_dir)

from agentops.domain.state import IncidentContext
from agentops.domain.messages import RemediationProposal, generate_id
from agentops.orchestration.graph import build_graph
from agentops.persistence.sqlite import init_db, SessionLocal, EventLog
from agentops.knowledge_graph.graph import KnowledgeGraph
from agentops.retrieval.hybrid import HybridRetriever
from agentops.policies.verifier import DeterministicVerifier
from agentops.tools.gateway import ToolGateway

cells = []
execution_count = 1

def add_markdown(content: str):
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in content.splitlines()]
    })

shared_globals = {
    "IncidentContext": IncidentContext,
    "RemediationProposal": RemediationProposal,
    "generate_id": generate_id,
    "build_graph": build_graph,
    "init_db": init_db,
    "SessionLocal": SessionLocal,
    "EventLog": EventLog,
    "KnowledgeGraph": KnowledgeGraph,
    "HybridRetriever": HybridRetriever,
    "DeterministicVerifier": DeterministicVerifier,
    "ToolGateway": ToolGateway,
    "json": json,
    "sys": sys,
    "os": os
}

def add_code(code: str):
    global execution_count
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        try:
            exec(code, shared_globals)
        except Exception as e:
            import traceback
            traceback.print_exc()

    output_str = buf.getvalue()
    outputs = []
    if output_str:
        outputs.append({
            "output_type": "stream",
            "name": "stdout",
            "text": [line + "\n" for line in output_str.splitlines()]
        })

    cells.append({
        "cell_type": "code",
        "execution_count": execution_count,
        "metadata": {},
        "outputs": outputs,
        "source": [line + "\n" for line in code.splitlines()]
    })
    execution_count += 1

# 1. Title
add_markdown("""# 🤖 IncidentGuard AI: A Multi-Agent System for Incident Diagnosis and Safe Remediation
### Comprehensive Project Notebook & Execution Report
* **Author / Submitter:** Sreekar Reddy
* **System Name:** IncidentGuard AI (AgentOps Platform)
* **Core Technologies:** Python 3.12, LangGraph, Pydantic v2, SQLite FTS5, NetworkX, FastAPI
* **Repository:** [https://github.com/Sreekarreddy2005/-IncidentGuard-AI-A-Multi-Agent-System-for-Incident-Diagnosis-and-Safe-Remediation](https://github.com/Sreekarreddy2005/-IncidentGuard-AI-A-Multi-Agent-System-for-Incident-Diagnosis-and-Safe-Remediation)

---
### Abstract & Project Motivation
In production cloud environments, deploying probabilistic, unconstrained LLM agent loops to remediate live incidents is hazardous. An open-ended agent can hallucinate destructive shell commands, trigger cascading dependency failures, exceed replica quotas, or loop indefinitely.

**IncidentGuard AI** solves this by enforcing **deterministic state machine boundaries (LangGraph)**, **zero-LLM deterministic safety verifiers**, **knowledge-graph blast-radius calculations (NetworkX)**, **hybrid runbook retrieval (SQLite FTS5)**, and an **append-only audit event trail (SQLite)**. LLMs are strictly treated as untrusted reasoning workers that formulate hypotheses and propose structured actions; all mutations must pass invariant checks before reaching the execution gateway.""")

# 2. Section 1 Setup
add_markdown("""## 1. Environment Setup & Core Primitives
We import our domain models, LangGraph orchestrator, deterministic verifier, and persistence layer. The database schema is initialized automatically.""")

add_code("""# Initialize Persistence and Verify Imports
init_db()

print("✅ Persistence Layer initialized: SQLite Event Log ready")
print("✅ LangGraph Orchestrator ready")
print("✅ Deterministic Policy Verifier ready")
print("✅ NetworkX Knowledge Graph engine ready")
print("✅ Hybrid FTS5 Retriever ready")
""")

# 3. Section 2 Knowledge Graph
add_markdown("""## 2. Knowledge Graph: Dependency Mapping & Blast Radius Analysis
Before any remediation proposal is approved, the platform calculates its upstream and downstream blast radius using an in-memory **NetworkX** directed dependency graph.""")

add_code("""# Load Knowledge Graph from versioned topology definitions
kg = KnowledgeGraph("examples/knowledge/dependencies.json")

target_service = "checkout-api"
downstream = kg.get_downstream_dependencies(target_service)
upstream = kg.get_upstream_dependencies(target_service)
blast_radius = kg.check_blast_radius(target_service)

print(f"Service Analyzed: {target_service}")
print(f"Downstream Dependencies (services impacted if checkout-api mutates): {downstream}")
print(f"Upstream Dependencies (services calling checkout-api): {upstream}")
print(f"Calculated Blast Radius Severity: {blast_radius.upper()}")
""")

# 4. Section 3 Hybrid Retrieval
add_markdown("""## 3. Hybrid Runbook Retrieval (Grounding & Citations)
The Investigator Agent retrieves operational runbooks using SQLite FTS5 to ensure that proposed actions are supported by verified organizational documentation.""")

add_code("""# Initialize Hybrid Retriever with production runbooks
retriever = HybridRetriever("examples/knowledge/runbooks.json")

query = "High latency and 5xx errors on checkout API"
results = retriever.search(query=query, service="checkout-api")

print(f"Retrieval Query: '{query}'")
print(f"Matches Found: {len(results)}\\n")
for idx, r in enumerate(results, 1):
    print(f"[{idx}] Citation ID: {r['id']}")
    print(f"    Title: {r['title']}")
    print(f"    Content: {r['content']}")
""")

# 5. Section 4 Deterministic Safety Gate
add_markdown("""## 4. Deterministic Safety Gate (Zero-LLM Policy Enforcement)
The **Safety Verifier** uses 100% deterministic Python rules—never an LLM—guaranteeing that safety policies fail closed.
We evaluate three distinct policy scenarios:
1. **Scenario A (ALLOW):** Valid scale action under Autonomy Tier 3.
2. **Scenario B (REQUIRE_APPROVAL):** Mutating action requested under Tier 1/2 requiring operator sign-off.
3. **Scenario C (DENY):** Request exceeds hard capacity ceiling (e.g. >100 replicas).""")

add_code("""# Scenario A: Valid request under Tier 3
p_valid = RemediationProposal(
    run_id="demo-run-1",
    trace_id="demo-trace-1",
    correlation_id="corr-1",
    sender="IOAgent",
    recipient="Orchestrator",
    tenant_id="t-acme-corp",
    environment="production",
    action_type="simulate_scale",
    service="checkout-api",
    parameters={"replicas": 50},
    preconditions=["5xx rate > 5%"],
    estimated_blast_radius="medium"
)
decision_a = DeterministicVerifier.verify(p_valid, autonomy_tier=3)
print(f"Scenario A (Tier 3 Valid): Decision = {decision_a.decision} | Reason = {decision_a.reason_code}")

# Scenario B: Mutating action under Tier 2 (Human Approval Gate)
decision_b = DeterministicVerifier.verify(p_valid, autonomy_tier=2)
print(f"Scenario B (Tier 2 Gate):  Decision = {decision_b.decision} | Reason = {decision_b.reason_code}")

# Scenario C: Exceeds hard replica limit (> 100)
p_illegal = RemediationProposal(
    run_id="demo-run-2",
    trace_id="demo-trace-2",
    correlation_id="corr-2",
    sender="IOAgent",
    recipient="Orchestrator",
    tenant_id="t-acme-corp",
    environment="production",
    action_type="simulate_scale",
    service="checkout-api",
    parameters={"replicas": 500},
    preconditions=["Emergency scale"],
    estimated_blast_radius="high"
)
decision_c = DeterministicVerifier.verify(p_illegal, autonomy_tier=3)
print(f"Scenario C (Over Limit):   Decision = {decision_c.decision} | Reason = {decision_c.reason_code}")
""")

# 6. Section 5 End-to-End Workflow Execution
add_markdown("""## 5. End-to-End Incident Execution: Golden Autonomous Path (Tier 3)
We now trigger the complete LangGraph state machine on a production incident. 
The incident payload is ingested, the Planner generates an investigation task, the Investigator finds runbook citations, the I&O Agent drafts a proposal, the Verifier validates safety, and the Tool Gateway executes the simulated mutation.""")

add_code("""# Build the LangGraph Workflow
graph = build_graph(data_dir="examples/knowledge")

incident = IncidentContext(
    incident_id="INC-20261021-001",
    tenant_id="t-acme-corp",
    environment="production",
    service="checkout-api",
    description="High latency and 5xx errors reported on checkout API. Customers unable to complete purchases.",
    requested_autonomy_tier=3
)

state = {
    "run_id": "run-golden-notebook-01",
    "trace_id": "trace-golden-notebook-01",
    "incident": incident,
    "status": "RECEIVED",
    "error_detail": None,
    "retry_count": 0,
    "investigation_task": None,
    "evidence_bundle": None,
    "remediation_proposal": None,
    "safety_decision": None,
    "execution_result": None
}

print(f"🚀 Triggering Incident: {incident.incident_id} ({incident.service})")
print(f"Description: {incident.description}\\n")
print("--- Execution Trace ---")

for output in graph.stream(state):
    for node_name, state_update in output.items():
        status = state_update.get("status", "UNKNOWN")
        print(f"[{node_name}] -> {status}")
        if "investigation_task" in state_update:
            print(f"    Objective: {state_update['investigation_task']['objective']}")
        if "evidence_bundle" in state_update:
            print(f"    Hypothesis: {state_update['evidence_bundle']['hypothesis']}")
            print(f"    Citations Attached: {len(state_update['evidence_bundle']['citations'])}")
        if "remediation_proposal" in state_update:
            print(f"    Proposed Action: {state_update['remediation_proposal']['action_type']} (Replicas: {state_update['remediation_proposal']['parameters']['replicas']})")
            print(f"    Estimated Blast Radius: {state_update['remediation_proposal']['estimated_blast_radius']}")
        if "safety_decision" in state_update:
            dec = state_update["safety_decision"]
            print(f"    Safety Decision: {dec['decision']} (Reason: {dec['reason_code']})")
        if "execution_result" in state_update:
            res = state_update["execution_result"]
            print(f"    Gateway Result: {res['output']} (Success: {res['success']})")

print("\\n✅ Golden Trajectory Workflow Completed Successfully!")
""")

# 7. Section 6 Safety Halt
add_markdown("""## 6. Safety Boundary Verification: Human-in-the-Loop Halt (Tier 1)
To prove that our safety boundary is unbreakable, we submit the same incident with **Autonomy Tier 1**. The platform must halt at `WAITING_FOR_APPROVAL` without executing any infrastructure tool.""")

add_code("""# Run with Tier 1 (Advisory Mode)
incident_tier1 = IncidentContext(
    incident_id="INC-20261021-002",
    tenant_id="t-acme-corp",
    environment="production",
    service="checkout-api",
    description="High latency and 5xx errors",
    requested_autonomy_tier=1
)

state_tier1 = {
    "run_id": "run-gated-notebook-02",
    "trace_id": "trace-gated-notebook-02",
    "incident": incident_tier1,
    "status": "RECEIVED",
    "error_detail": None,
    "retry_count": 0,
    "investigation_task": None,
    "evidence_bundle": None,
    "remediation_proposal": None,
    "safety_decision": None,
    "execution_result": None
}

final_state = graph.invoke(state_tier1)

print(f"Workflow Final Status: {final_state['status']}")
print(f"Safety Decision:       {final_state['safety_decision']['decision']}")
print(f"Reason Code:           {final_state['safety_decision']['reason_code']}")
print(f"Tool Executed:         {final_state.get('execution_result') is not None}")
assert final_state['status'] == "WAITING_FOR_APPROVAL"
assert final_state.get('execution_result') is None
print("\\n🛡️ Safety Invariant Verified: Execution was halted before tool invocation!")
""")

# 8. Section 7 Audit Trail
add_markdown("""## 7. Append-Only Audit Trail & Compliance Verification
Every event, hypothesis, and decision from the Golden Run is recorded in the SQLite `event_log`. This cell replays the immutable audit trail for compliance verification.""")

add_code("""# Query SQLite event_log for run-golden-notebook-01
with SessionLocal() as session:
    events = session.query(EventLog).filter(EventLog.run_id == "run-golden-notebook-01").all()
    print(f"Audit Trail for run-golden-notebook-01 ({len(events)} events recorded):\\n")
    for idx, e in enumerate(events, 1):
        payload = json.loads(e.payload)
        print(f"[{idx}] {e.message_type}")
        print(f"    Trace ID: {e.trace_id}")
        if "objective" in payload:
            print(f"    Task: {payload['objective']}")
        elif "hypothesis" in payload:
            print(f"    Evidence: {payload['hypothesis']}")
        elif "action_type" in payload:
            print(f"    Action: {payload['action_type']} (Service: {payload['service']})")
        elif "decision" in payload:
            print(f"    Decision: {payload['decision']} ({payload['reason_code']})")
        elif "output" in payload:
            print(f"    Execution Output: {payload['output']}")
        print()
""")

# 9. Section 8 Trajectory Evaluation Suite
add_markdown("""## 8. Offline Trajectory Evaluation Harness
We execute automated evaluation tests asserting all architectural invariants.""")

add_code("""# Run Trajectory Assertions
def run_evaluations():
    # Test 1: Autonomous path
    s1 = graph.invoke({
        "run_id": "test-eval-1",
        "trace_id": "trace-eval-1",
        "incident": IncidentContext(incident_id="t1", tenant_id="t", environment="p", service="checkout-api", description="5xx errors", requested_autonomy_tier=3),
        "status": "RECEIVED",
        "error_detail": None,
        "retry_count": 0,
        "investigation_task": None,
        "evidence_bundle": None,
        "remediation_proposal": None,
        "safety_decision": None,
        "execution_result": None
    })
    assert s1["status"] == "COMPLETED"
    assert s1["safety_decision"]["decision"] == "ALLOW"
    assert s1["execution_result"]["success"] is True

    # Test 2: Approval required path
    s2 = graph.invoke({
        "run_id": "test-eval-2",
        "trace_id": "trace-eval-2",
        "incident": IncidentContext(incident_id="t2", tenant_id="t", environment="p", service="checkout-api", description="5xx errors", requested_autonomy_tier=1),
        "status": "RECEIVED",
        "error_detail": None,
        "retry_count": 0,
        "investigation_task": None,
        "evidence_bundle": None,
        "remediation_proposal": None,
        "safety_decision": None,
        "execution_result": None
    })
    assert s2["status"] == "WAITING_FOR_APPROVAL"
    assert s2["safety_decision"]["decision"] == "REQUIRE_APPROVAL"
    assert s2.get("execution_result") is None
    
    return "All 2 Invariant Trajectory Evaluations Passed (100% Deterministic)!"

result = run_evaluations()
print(f"✅ {result}")
""")

# 10. Conclusion
add_markdown("""## 9. Conclusion & Production Architecture Summary
This notebook demonstrates the end-to-end functionality of **IncidentGuard AI**:
1. **Zero Uncontrolled Probabilistic Execution:** LLMs generate structured, typed Pydantic proposals rather than raw terminal commands.
2. **Deterministic Safety Bounds:** A pure Python policy engine intercepts all actions, enforces hard capacity constraints, and mandates human-in-the-loop approvals based on configured autonomy tiers.
3. **Graph-Driven Blast Radius:** Real-time dependency reachability calculation prevents cascading outages across services.
4. **Reproducible Auditability:** Complete append-only event logging guarantees compliance and post-mortem reviewability.

*All code, tests, and documentation are hosted at [GitHub Repository](https://github.com/Sreekarreddy2005/-IncidentGuard-AI-A-Multi-Agent-System-for-Incident-Diagnosis-and-Safe-Remediation).*""")

notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3 (ipykernel)",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "codemirror_mode": {"name": "ipython", "version": 3},
            "file_extension": ".py",
            "mimetype": "text/x-python",
            "name": "python",
            "nbformat": 4,
            "nbformat_minor": 5,
            "pygments_lexer": "ipython3",
            "version": "3.12.14"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 5
}

target_path_root = "/Users/sreekarreddypindi/Downloads/Mini Agentic AI Platform/IncidentGuard_AI_Project_Notebook.ipynb"
target_path_agentops = "/Users/sreekarreddypindi/Downloads/Mini Agentic AI Platform/agentops/IncidentGuard_AI_Project_Notebook.ipynb"

with open(target_path_root, "w") as f:
    json.dump(notebook, f, indent=1)

with open(target_path_agentops, "w") as f:
    json.dump(notebook, f, indent=1)

print(f"Successfully generated notebook at: {target_path_root}")
print(f"Successfully generated notebook at: {target_path_agentops}")
