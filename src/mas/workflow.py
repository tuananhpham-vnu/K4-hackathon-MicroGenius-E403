import json
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .models import Evidence
from .observability import TraceLogger
from .prompts import XmlPrompt
from .retrieval import KnowledgeBase
from .utils import now_iso, tokens


class AdmissionsWorkflow:
    """Domain services used by both the legacy facade and LangGraph nodes."""

    def __init__(self, knowledge_base: KnowledgeBase, logger: TraceLogger | None = None):
        self.kb = knowledge_base
        self.audit_log: list[dict[str, Any]] = []
        self.logger = logger or TraceLogger()

    def _audit(self, request_id: str, agent: str, payload: dict[str, Any]) -> None:
        self.audit_log.append({"timestamp": now_iso(), "request_id": request_id, "agent": agent, "payload": payload})
        self.logger.event(request_id=request_id, step=agent, component="workflow", payload=payload)

    def orchestrate(self, query: str) -> dict[str, Any]:
        lowered = query.lower()
        high_risk_words = ("khiếu nại", "ngoại lệ", "phê duyệt", "trúng tuyển", "học bổng chắc chắn", "tình trạng hồ sơ")
        is_chitchat = len(tokens(query)) < 3 and any(word in lowered for word in ("hello", "chào", "hi"))
        risk = "high" if any(word in lowered for word in high_risk_words) else "low"
        intent = "program_information"
        mappings = {"điều kiện": "admission_requirements", "phù hợp": "program_recommendation", "so sánh": "program_comparison", "học phí": "tuition_and_scholarship", "học bổng": "tuition_and_scholarship", "hạn": "deadline_information", "đăng ký": "application_process", "nộp hồ sơ": "application_process"}
        for marker, candidate_intent in mappings.items():
            if marker in lowered:
                intent = candidate_intent
                break
        return {"intent": "chitchat" if is_chitchat else intent, "is_chitchat": is_chitchat, "clarity_score": min(10, max(1, len(tokens(query)) // 2 + 3)), "risk_level": risk, "need_summary": False, "need_clarification": len(tokens(query)) < 4, "need_human": risk == "high", "next_agent": "synthesis" if is_chitchat else "admissions_analyst"}

    def analyze(self, query: str, orchestration: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
        missing = []
        if orchestration["intent"] == "program_recommendation":
            missing = [field for field in ("education", "experience", "availability") if not profile.get(field)]
        return {"rewritten_query": f"{query}. Trả lời dựa trên bằng chứng đã kiểm tra nguồn và nêu rõ giới hạn dữ liệu.", "intent": orchestration["intent"], "entities": profile, "missing_information": missing, "sub_tasks": ["Tìm bằng chứng liên quan", "Kiểm tra độ tin cậy và tính cập nhật", "Tổng hợp câu trả lời có nguồn"]}

    def validate(self, evidence: list[Evidence], risk: str) -> dict[str, Any]:
        valid = [item for item in evidence if item.source_check_passed and item.relevance_score >= 0.35]
        avg_relevance = sum(item.relevance_score for item in valid) / len(valid) if valid else 0.0
        avg_trust = sum(item.source_trust_score for item in valid) / len(valid) if valid else 0.0
        passed = len(valid) >= 1 and avg_relevance >= 0.35 and avg_trust >= 0.70
        return {"passed": passed, "source_check_passed": bool(valid), "evidence_count": len(valid), "avg_relevance": round(avg_relevance, 3), "avg_source_trust": round(avg_trust, 3), "risk_level": risk, "needs_human": risk == "high" or not passed, "rejection_reasons": [] if passed else ["Không đủ evidence đạt ngưỡng source/relevance"]}

    def answer(self, query: str, *, context=None, history=None, profile=None, request_id=None) -> dict[str, Any]:
        request_id = request_id or f"req_{uuid.uuid4().hex[:12]}"
        self.logger.event(request_id=request_id, step="request_start", component="workflow", payload={"query": query})
        profile = profile or {}
        orchestration = self.orchestrate(query)
        analysis = self.analyze(query, orchestration, profile)
        evidence = self.kb.search(analysis["rewritten_query"], limit=8)
        validation = self.validate(evidence, orchestration["risk_level"])
        usable = [item for item in evidence if item.source_check_passed and item.relevance_score >= 0.35]
        response = "Chào bạn. Mình có thể hỗ trợ tra cứu thông tin chương trình và hướng dẫn hồ sơ." if orchestration["is_chitchat"] else ("Mình chưa tìm thấy bằng chứng đủ tin cậy cho câu hỏi này. Bạn vui lòng cung cấp thêm chi tiết hoặc chờ cán bộ tuyển sinh xác nhận." if not usable else f"Theo các tài liệu hiện có, thông tin liên quan là: {' '.join(item.quote for item in usable[:3])[:900]} Đây là tư vấn tham khảo dựa trên dữ liệu cục bộ, không phải quyết định tuyển sinh.")
        if validation["needs_human"]:
            response += " Trường hợp này cần cán bộ tuyển sinh kiểm tra trước khi đưa ra kết luận chính thức."
        for agent, payload in (("orchestrator", orchestration), ("admissions_analyst", analysis), ("searcher", {"evidence": [asdict(item) for item in evidence]}), ("validator", validation), ("synthesis", {"response": response, "citation_count": len(usable)})):
            self._audit(request_id, agent, payload)
        result = {"request_id": request_id, "response": response, "orchestration": orchestration, "analysis": analysis, "validation": validation, "evidence": [asdict(item) for item in usable], "sources": [asdict(self.kb.sources[item.source_id]) for item in usable], "prompt_xml": XmlPrompt.build(request_id, query, context, history, profile, usable)}
        self.logger.event(request_id=request_id, step="request_end", component="workflow", payload={"status": "completed", "citation_count": len(usable)})
        return result


def create_workflow(repo_root: Path | None = None, logger: TraceLogger | None = None) -> AdmissionsWorkflow:
    root = repo_root or Path(__file__).resolve().parents[2]
    return AdmissionsWorkflow(KnowledgeBase(root / "data" / "vlearn-pack"), logger=logger)
