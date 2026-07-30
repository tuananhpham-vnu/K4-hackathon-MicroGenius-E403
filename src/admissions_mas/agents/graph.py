"""LangGraph implementation of the admissions MAS workflow.

The graph keeps the framework orchestration separate from the concrete
retrieval and validation services in ``admissions_mas.services.workflow``.
"""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from ..domain.models import Evidence
from ..prompts.template_registry import prompt_messages
from ..prompts.xml_prompt import XmlPrompt
from ..retrieval.web_search import WebSearchService
from ..services.workflow import AdmissionsWorkflow
from .harness import AgentHarness, ToolSpec


class MASState(TypedDict, total=False):
    request_id: str
    query: str
    context: dict[str, Any]
    history: list[dict[str, str]]
    profile: dict[str, Any]
    orchestration: dict[str, Any]
    analysis: dict[str, Any]
    evidence: list[dict[str, Any]]
    validation: dict[str, Any]
    response: str
    prompt_xml: str
    system_prompt: str
    user_prompt: str
    retry_count: int
    human_required: bool
    harness_plan: dict[str, Any]
    guardrail_result: dict[str, Any]


class LangGraphAdmissionsMAS:
    """Reusable, stateful MAS graph with source-aware evidence handling."""

    def __init__(self, workflow: AdmissionsWorkflow, harness: AgentHarness | None = None):
        self.workflow = workflow
        self.harness = harness or AgentHarness()
        self.web_search = WebSearchService(self.workflow.kb)
        self.harness.register_tool(ToolSpec("knowledge_base.search", "Search approved local knowledge base", True), self.workflow.kb.search)
        self.harness.register_tool(ToolSpec("web.search", "Discover current web sources", True), self.web_search.search)
        self.harness.register_tool(ToolSpec("source_registry.lookup", "Resolve source metadata", True), lambda source_id: self.workflow.kb.sources.get(source_id))
        self.graph = self._build_graph()

    def _harness_context(self, agent: str, state: MASState) -> dict[str, Any]:
        plan = self.harness.plan(agent, state)
        self.workflow._audit(state["request_id"], "harness", {"agent": agent, "plan": plan})
        self.workflow.logger.event(request_id=state["request_id"], step="harness_plan", component=agent, payload=plan)
        return plan

    def _build_graph(self):
        graph = StateGraph(MASState)
        graph.add_node("orchestrator", self.orchestrator_node)
        graph.add_node("analyst", self.analyst_node)
        graph.add_node("searcher", self.searcher_node)
        graph.add_node("validator", self.validator_node)
        graph.add_node("hitl_gate", self.hitl_gate_node)
        graph.add_node("synthesis", self.synthesis_node)

        graph.add_edge(START, "orchestrator")
        graph.add_conditional_edges(
            "orchestrator",
            lambda state: "synthesis" if state["orchestration"]["is_chitchat"] or state["orchestration"]["is_out_of_scope"] else "analyst",
            {"analyst": "analyst", "synthesis": "synthesis"},
        )
        graph.add_edge("analyst", "searcher")
        graph.add_edge("searcher", "validator")
        graph.add_conditional_edges(
            "validator",
            self.validation_route,
            {"retry": "searcher", "hitl": "hitl_gate", "synthesis": "synthesis"},
        )
        graph.add_conditional_edges(
            "hitl_gate",
            lambda state: "synthesis",
            {"synthesis": "synthesis"},
        )
        graph.add_edge("synthesis", END)
        return graph.compile()

    def orchestrator_node(self, state: MASState) -> dict[str, Any]:
        plan = self._harness_context("orchestrator", state)
        input_check = self.harness.guardrails.check_input(state["query"])
        value = self.workflow.orchestrate(state["query"])
        self.workflow._audit(state["request_id"], "orchestrator", value)
        messages = prompt_messages(request_id=state["request_id"], agent="orchestrator", query=state["query"], context=state.get("context"), history=state.get("history"), profile=state.get("profile"))
        return {"orchestration": value, "retry_count": state.get("retry_count", 0), "system_prompt": messages[0]["content"], "user_prompt": messages[1]["content"], "harness_plan": plan, "guardrail_result": {"passed": input_check.passed, "reasons": input_check.reasons}}

    def analyst_node(self, state: MASState) -> dict[str, Any]:
        self._harness_context("analyst", state)
        value = self.workflow.analyze(
            state["query"], state["orchestration"], state.get("profile", {}),
        )
        self.workflow._audit(state["request_id"], "admissions_analyst", value)
        return {"analysis": value}

    def searcher_node(self, state: MASState) -> dict[str, Any]:
        plan = self._harness_context("searcher", state)
        # On retry, use the original query plus the failed validation reasons
        # to broaden retrieval without losing the original query trace.
        query = state["analysis"]["retrieval_query"]
        if state.get("retry_count", 0):
            query += " " + " ".join(state.get("validation", {}).get("rejection_reasons", []))
        evidence = self.harness.invoke_tool("searcher", "knowledge_base.search", state, query=query, limit=8)
        web_evidence = self.harness.invoke_tool("searcher", "web.search", state, query=query, limit=5)
        evidence = evidence + web_evidence
        serialized = [item.__dict__ for item in evidence]
        self.workflow.logger.event(request_id=state["request_id"], step="tool_call", component="searcher", payload={"tool": "knowledge_base.search", "query": query, "result_count": len(serialized)})
        self.workflow.logger.event(request_id=state["request_id"], step="tool_call", component="searcher", payload={"tool": "web.search", "available": self.web_search.available, "query": query, "result_count": len(web_evidence)})
        self.workflow._audit(state["request_id"], "searcher", {"evidence": serialized})
        return {"evidence": serialized, "retry_count": state.get("retry_count", 0) + 1, "harness_plan": plan}

    def validator_node(self, state: MASState) -> dict[str, Any]:
        plan = self._harness_context("validator", state)
        evidence = [Evidence(**item) for item in state.get("evidence", [])]
        value = self.workflow.validate(evidence, state["orchestration"]["risk_level"])
        self.workflow._audit(state["request_id"], "validator", value)
        return {"validation": value, "harness_plan": plan}

    def validation_route(self, state: MASState) -> str:
        validation = state["validation"]
        if validation["needs_human"] and state["orchestration"]["risk_level"] == "high":
            return "hitl"
        if not validation["passed"] and state.get("retry_count", 0) < 2:
            return "retry"
        return "synthesis"

    def hitl_gate_node(self, state: MASState) -> dict[str, Any]:
        plan = self._harness_context("hitl_gate", state)
        payload = {"required": True, "reason": state["validation"]["rejection_reasons"], "status": "pending_human_review"}
        self.workflow._audit(state["request_id"], "hitl_gate", payload)
        return {"human_required": True, "harness_plan": plan}

    def synthesis_node(self, state: MASState) -> dict[str, Any]:
        plan = self._harness_context("synthesis", state)
        evidence = [item for item in state.get("evidence", []) if item["source_check_passed"] and item["relevance_score"] >= 0.35]
        validation = state.get("validation", {})
        if state["orchestration"]["is_chitchat"]:
            response = "Chào bạn. Mình có thể hỗ trợ tra cứu thông tin chương trình và hướng dẫn hồ sơ."
        elif state["orchestration"]["is_out_of_scope"]:
            response = "Mình không thể thực hiện yêu cầu đó. Mình chỉ hỗ trợ tra cứu và tư vấn thông tin tuyển sinh từ nguồn đã được phê duyệt."
        elif state["orchestration"]["need_clarification"]:
            response = "Mình cần thêm thông tin để tra cứu chính xác. Bạn vui lòng nêu rõ khóa học, mốc thời gian hoặc nội dung tuyển sinh bạn muốn hỏi."
        elif not evidence:
            response = "Mình chưa tìm thấy bằng chứng đủ tin cậy cho câu hỏi này. Bạn vui lòng cung cấp thêm chi tiết hoặc chờ cán bộ tuyển sinh xác nhận."
        else:
            snippets = " ".join(item["quote"] for item in evidence[:3])
            response = f"Theo các tài liệu hiện có, thông tin liên quan là: {snippets[:900]} Đây là tư vấn tham khảo dựa trên dữ liệu cục bộ, không phải quyết định tuyển sinh."
        if state.get("human_required") or validation.get("needs_human"):
            response += " Trường hợp này cần cán bộ tuyển sinh kiểm tra trước khi đưa ra kết luận chính thức."
        prompt_xml = XmlPrompt.build(state["request_id"], state["query"], state.get("context"), state.get("history"), state.get("profile"), [Evidence(**item) for item in evidence])
        messages = prompt_messages(request_id=state["request_id"], agent="synthesis", query=state["query"], context=state.get("context"), history=state.get("history"), profile=state.get("profile"), evidence=[Evidence(**item) for item in evidence])
        output_check = self.harness.guardrails.check_output(response, evidence, state["orchestration"]["risk_level"])
        self.workflow._audit(state["request_id"], "synthesis", {"response": response, "citation_count": len(evidence), "guardrail": output_check.__dict__})
        return {"response": response, "prompt_xml": prompt_xml, "evidence": evidence, "system_prompt": messages[0]["content"], "user_prompt": messages[1]["content"], "harness_plan": plan, "guardrail_result": {"passed": output_check.passed, "reasons": output_check.reasons}}

    def invoke(self, query: str, *, request_id: str, context: dict[str, Any] | None = None,
               history: list[dict[str, str]] | None = None, profile: dict[str, Any] | None = None) -> dict[str, Any]:
        initial: MASState = {"request_id": request_id, "query": query, "context": context or {}, "history": history or [], "profile": profile or {}, "retry_count": 0}
        return dict(self.graph.invoke(initial))
