"""Runtime harness for agent policy, tools, memory and guardrails."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    requires_source_trace: bool = False


@dataclass(frozen=True)
class HarnessPlan:
    agent: str
    reasoning_mode: str
    allowed_tools: tuple[str, ...]
    memory_scopes: tuple[str, ...]
    guardrails: tuple[str, ...]


@dataclass(frozen=True)
class GuardrailResult:
    passed: bool
    reasons: tuple[str, ...] = ()


class MemoryStore:
    """Small replaceable memory adapter; production can swap in PostgreSQL/Redis."""

    def __init__(self) -> None:
        self._items: dict[str, list[dict[str, Any]]] = {}

    def remember(self, session_id: str, item: dict[str, Any]) -> None:
        self._items.setdefault(session_id, []).append(item)

    def recall(self, session_id: str, limit: int = 10) -> list[dict[str, Any]]:
        return self._items.get(session_id, [])[-limit:]


class GuardrailEngine:
    HIGH_RISK_TERMS = ("khiếu nại", "ngoại lệ", "trúng tuyển", "phê duyệt", "học bổng đặc biệt")

    def check_input(self, query: str) -> GuardrailResult:
        if not query.strip():
            return GuardrailResult(False, ("query_empty",))
        return GuardrailResult(True)

    def check_output(self, response: str, evidence: list[dict[str, Any]], risk_level: str) -> GuardrailResult:
        reasons: list[str] = []
        if risk_level == "high" and "cán bộ tuyển sinh" not in response.lower():
            reasons.append("high_risk_requires_human_review")
        if evidence and "source" not in response.lower() and "tài liệu" not in response.lower():
            reasons.append("grounded_response_must_mention_source")
        return GuardrailResult(not reasons, tuple(reasons))

    def requires_hitl(self, query: str, risk_level: str) -> bool:
        lowered = query.lower()
        return risk_level == "high" or any(term in lowered for term in self.HIGH_RISK_TERMS)


ToolFunction = Callable[..., Any]


class AgentHarness:
    """Policy boundary around LLM reasoning and deterministic agent tools."""

    DEFAULT_PLANS = {
        "orchestrator": HarnessPlan("orchestrator", "llm", (), ("session",), ("input", "risk")),
        "analyst": HarnessPlan("analyst", "llm", (), ("session", "candidate_profile"), ("input", "no_invention")),
        "searcher": HarnessPlan("searcher", "llm", ("knowledge_base.search", "web.search", "source_registry.lookup"), ("session",), ("source_trace", "approved_sources")),
        "validator": HarnessPlan("validator", "llm", ("source_registry.lookup",), ("session",), ("source_trace", "relevance_threshold")),
        "hitl_gate": HarnessPlan("hitl_gate", "rule_and_human", (), ("session", "audit"), ("high_risk", "human_required")),
        "synthesis": HarnessPlan("synthesis", "llm", ("source_registry.lookup",), ("session", "candidate_profile"), ("citation", "no_decision", "output")),
    }

    def __init__(self, memory: MemoryStore | None = None, guardrails: GuardrailEngine | None = None):
        self.memory = memory or MemoryStore()
        self.guardrails = guardrails or GuardrailEngine()
        self.tools: dict[str, tuple[ToolSpec, ToolFunction]] = {}

    def register_tool(self, spec: ToolSpec, function: ToolFunction) -> None:
        self.tools[spec.name] = (spec, function)

    def plan(self, agent: str, state: dict[str, Any]) -> dict[str, Any]:
        plan = self.DEFAULT_PLANS.get(agent, HarnessPlan(agent, "llm", (), ("session",), ("output",)))
        return asdict(plan)

    def invoke_tool(self, agent: str, tool_name: str, state: dict[str, Any], **kwargs: Any) -> Any:
        plan = self.DEFAULT_PLANS.get(agent)
        if not plan or tool_name not in plan.allowed_tools:
            raise PermissionError(f"Tool {tool_name!r} is not allowed for agent {agent!r}")
        if tool_name not in self.tools:
            raise KeyError(f"Tool {tool_name!r} is not registered")
        return self.tools[tool_name][1](**kwargs)

    def remember(self, state: dict[str, Any], item: dict[str, Any]) -> None:
        session_id = state.get("context", {}).get("session_id", state.get("request_id", "default"))
        self.memory.remember(session_id, item)

    def recall(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        session_id = state.get("context", {}).get("session_id", state.get("request_id", "default"))
        return self.memory.recall(session_id)
