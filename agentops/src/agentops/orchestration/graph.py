from typing import Literal

from langgraph.graph import END, StateGraph

from agentops.agents.investigator import InvestigatorAgent
from agentops.agents.io_agent import IOAgent
from agentops.agents.planner import PlannerAgent
from agentops.domain.messages import ExecutionResult, RemediationProposal
from agentops.domain.state import WorkflowState
from agentops.knowledge_graph.graph import KnowledgeGraph
from agentops.observability.tracer import OTelTracer
from agentops.policies.verifier import DeterministicVerifier
from agentops.retrieval.hybrid import HybridRetriever
from agentops.tools.gateway import ToolGateway


def build_graph(data_dir: str = "examples/knowledge"):
    workflow = StateGraph(WorkflowState)

    # Initialize static agents
    retriever = HybridRetriever(f"{data_dir}/runbooks.json")
    kg = KnowledgeGraph(f"{data_dir}/dependencies.json")

    investigator = InvestigatorAgent(retriever)
    io_agent = IOAgent(kg)

    def receive_incident(state: WorkflowState) -> dict:
        OTelTracer.record_span(
            state["run_id"], state["trace_id"], "IncidentReceived", state["incident"].model_dump()
        )
        return {"status": "VALIDATING_INPUT"}

    def planner_node(state: WorkflowState) -> dict:
        res = PlannerAgent.plan(state)
        if "investigation_task" in res:
            OTelTracer.record_span(
                state["run_id"], state["trace_id"], "InvestigationTask", res["investigation_task"]
            )
        return res

    def investigator_node(state: WorkflowState) -> dict:
        res = investigator.investigate(state)
        if "evidence_bundle" in res:
            OTelTracer.record_span(
                state["run_id"], state["trace_id"], "EvidenceBundle", res["evidence_bundle"]
            )
        return res

    def io_node(state: WorkflowState) -> dict:
        res = io_agent.propose(state)
        if "remediation_proposal" in res:
            OTelTracer.record_span(
                state["run_id"],
                state["trace_id"],
                "RemediationProposal",
                res["remediation_proposal"],
            )
        return res

    def verifier_node(state: WorkflowState) -> dict:
        proposal_dict = state.get("remediation_proposal") or {}
        proposal = RemediationProposal.model_validate(proposal_dict)
        decision = DeterministicVerifier.verify(proposal, state["incident"].requested_autonomy_tier)
        decision_dict = decision.model_dump()
        OTelTracer.record_span(state["run_id"], state["trace_id"], "SafetyDecision", decision_dict)
        return {"safety_decision": decision_dict, "status": "VERIFYING_SAFETY"}

    def route_after_verification(
        state: WorkflowState,
    ) -> Literal["WAITING_FOR_APPROVAL", "EXECUTING", "DENIED"]:
        safety_dec = state.get("safety_decision") or {}
        decision = safety_dec.get("decision", "DENY")
        if decision == "ALLOW":
            return "EXECUTING"
        elif decision == "REQUIRE_APPROVAL":
            return "WAITING_FOR_APPROVAL"
        else:
            return "DENIED"

    def execution_node(state: WorkflowState) -> dict:
        proposal = state.get("remediation_proposal") or {}
        action_type = proposal.get("action_type")
        params = proposal.get("parameters") or {}
        service = str(proposal.get("service", ""))
        idempotency_key = str(proposal.get("idempotency_key", ""))
        tenant_id = str(proposal.get("tenant_id", ""))
        environment = str(proposal.get("environment", ""))
        message_id = str(proposal.get("message_id", ""))

        if action_type == "simulate_scale":
            res = ToolGateway.simulate_scale(
                service=service,
                replicas=int(params.get("replicas", 0)),
                idempotency_key=idempotency_key,
                tenant_id=tenant_id,
            )
        else:
            res = {"success": False, "output": "Unknown action", "retryable": False}

        result = ExecutionResult(
            run_id=state["run_id"],
            trace_id=state["trace_id"],
            correlation_id=message_id,
            sender="Gateway",
            recipient="Orchestrator",
            tenant_id=tenant_id,
            environment=environment,
            success=bool(res["success"]),
            output=str(res["output"]),
        )
        result_dict = result.model_dump()
        OTelTracer.record_span(state["run_id"], state["trace_id"], "ExecutionResult", result_dict)
        return {"execution_result": result_dict, "status": "COMPLETED"}

    def waiting_node(state: WorkflowState) -> dict:
        OTelTracer.record_span(
            state["run_id"],
            state["trace_id"],
            "WaitingForApproval",
            {"status": "WAITING_FOR_APPROVAL"},
        )
        return {"status": "WAITING_FOR_APPROVAL"}

    def denied_node(state: WorkflowState) -> dict:
        OTelTracer.record_span(
            state["run_id"], state["trace_id"], "ExecutionDenied", {"status": "DENIED"}
        )
        return {"status": "DENIED"}

    workflow.add_node("receive", receive_incident)
    workflow.add_node("planner", planner_node)
    workflow.add_node("investigator", investigator_node)
    workflow.add_node("io_agent", io_node)
    workflow.add_node("verifier", verifier_node)
    workflow.add_node("execute", execution_node)

    workflow.add_node("waiting", waiting_node)
    workflow.add_node("denied", denied_node)

    workflow.set_entry_point("receive")
    workflow.add_edge("receive", "planner")
    workflow.add_edge("planner", "investigator")
    workflow.add_edge("investigator", "io_agent")
    workflow.add_edge("io_agent", "verifier")

    workflow.add_conditional_edges(
        "verifier",
        route_after_verification,
        {"EXECUTING": "execute", "WAITING_FOR_APPROVAL": "waiting", "DENIED": "denied"},
    )

    workflow.add_edge("execute", END)
    workflow.add_edge("waiting", END)
    workflow.add_edge("denied", END)

    return workflow.compile()
