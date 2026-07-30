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
        out_of_scope_words = ("dự báo thời tiết", "mật khẩu", "viết hộ", "làm hộ", "hack", "xóa hồ sơ")
        is_out_of_scope = any(word in lowered for word in out_of_scope_words)
        risk = "high" if any(word in lowered for word in high_risk_words) else "low"
        intent = "program_information"
        mappings = {"điều kiện": "admission_requirements", "phù hợp": "program_recommendation", "so sánh": "program_comparison", "học phí": "tuition_and_scholarship", "học bổng": "tuition_and_scholarship", "phụ cấp": "tuition_and_scholarship", "quyền lợi": "tuition_and_scholarship", "hạn": "deadline_information", "đăng ký": "application_process", "nộp hồ sơ": "application_process"}
        for marker, candidate_intent in mappings.items():
            if marker in lowered:
                intent = candidate_intent
                break
        resolved_intent = "chitchat" if is_chitchat else ("out_of_scope" if is_out_of_scope else intent)
        return {"intent": resolved_intent, "is_chitchat": is_chitchat, "is_out_of_scope": is_out_of_scope, "clarity_score": min(10, max(1, len(tokens(query)) // 2 + 3)), "risk_level": risk, "need_summary": False, "need_clarification": not is_chitchat and not is_out_of_scope and len(tokens(query)) < 4, "need_human": risk == "high", "next_agent": "synthesis" if is_chitchat or is_out_of_scope else "admissions_analyst"}

    def analyze(self, query: str, orchestration: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
        missing = []
        if orchestration["intent"] == "program_recommendation":
            missing = [field for field in ("education", "experience", "availability") if not profile.get(field)]
        lowered = query.lower()
        expansions = {
            "admission_requirements": "đối tượng điều kiện tiêu chí ứng tuyển",
            "tuition_and_scholarship": "miễn 100% học phí phụ cấp 8 triệu quyền lợi",
            "deadline_information": "hạn nộp hồ sơ mốc thời gian tuyển sinh",
            "application_process": "quy trình nộp hồ sơ ứng tuyển đăng ký",
            "program_recommendation": "đối tượng phù hợp điều kiện nền tảng",
        }
        extra = expansions.get(orchestration["intent"], "")
        if any(marker in lowered for marker in ("bao lâu", "kéo dài", "thời lượng")):
            extra += " 12 tuần thời gian đào tạo lộ trình"
        if any(marker in lowered for marker in ("quyền lợi", "phụ cấp")):
            extra += " miễn học phí phụ cấp quyền lợi học viên"
        retrieval_query = f"{query} {extra}".strip()
        return {"retrieval_query": retrieval_query, "rewritten_query": f"{query}. Trả lời dựa trên bằng chứng đã kiểm tra nguồn và nêu rõ giới hạn dữ liệu.", "intent": orchestration["intent"], "entities": profile, "missing_information": missing, "sub_tasks": ["Tìm bằng chứng liên quan", "Kiểm tra độ tin cậy và tính cập nhật", "Tổng hợp câu trả lời có nguồn"]}

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
        if orchestration["is_chitchat"]:
            validation = {"passed": True, "source_check_passed": True, "evidence_count": 0, "avg_relevance": 0.0, "avg_source_trust": 0.0, "risk_level": "low", "needs_human": False, "rejection_reasons": []}
            response = "Chào bạn. Mình có thể hỗ trợ tra cứu thông tin chương trình, điều kiện, lịch tuyển sinh và hướng dẫn hồ sơ."
            analysis, evidence, usable = {}, [], []
        elif orchestration["is_out_of_scope"]:
            validation = {"passed": False, "source_check_passed": False, "evidence_count": 0, "avg_relevance": 0.0, "avg_source_trust": 0.0, "risk_level": "low", "needs_human": False, "rejection_reasons": ["Yêu cầu nằm ngoài phạm vi tư vấn tuyển sinh"]}
            response = "Mình không thể thực hiện yêu cầu đó. Mình chỉ hỗ trợ tra cứu và tư vấn thông tin tuyển sinh từ nguồn đã được phê duyệt."
            analysis, evidence, usable = {}, [], []
        else:
            analysis = self.analyze(query, orchestration, profile)
            evidence = self.kb.search(analysis["retrieval_query"], limit=8)
            validation = self.validate(evidence, orchestration["risk_level"])
            usable = [item for item in evidence if item.source_check_passed and item.relevance_score >= 0.35]
            if orchestration["need_clarification"]:
                response = "Mình cần thêm thông tin để tra cứu chính xác. Bạn vui lòng nêu rõ khóa học, mốc thời gian hoặc nội dung tuyển sinh bạn muốn hỏi."
            else:
                response = "Mình chưa tìm thấy bằng chứng đủ tin cậy cho câu hỏi này. Bạn vui lòng cung cấp thêm chi tiết hoặc chờ cán bộ tuyển sinh xác nhận." if not usable else f"Theo các tài liệu hiện có, thông tin liên quan là: {' '.join(item.quote for item in usable[:3])[:900]} Đây là tư vấn tham khảo dựa trên dữ liệu cục bộ, không phải quyết định tuyển sinh."
            if validation["needs_human"]:
                response += " Trường hợp này cần cán bộ tuyển sinh kiểm tra trước khi đưa ra kết luận chính thức."
        for agent, payload in (("orchestrator", orchestration), ("admissions_analyst", analysis), ("searcher", {"evidence": [asdict(item) for item in evidence]}), ("validator", validation), ("synthesis", {"response": response, "citation_count": len(usable)})):
            self._audit(request_id, agent, payload)
        result = {"request_id": request_id, "response": response, "orchestration": orchestration, "analysis": analysis, "validation": validation, "evidence": [asdict(item) for item in usable], "sources": [asdict(self.kb.sources[item.source_id]) for item in usable], "prompt_xml": XmlPrompt.build(request_id, query, context, history, profile, usable)}
        self.logger.event(request_id=request_id, step="request_end", component="workflow", payload={"status": "completed", "citation_count": len(usable)})
        return result


def create_workflow(repo_root: Path | None = None, logger: TraceLogger | None = None) -> AdmissionsWorkflow:
    root = repo_root or Path(__file__).resolve().parents[2]
    return AdmissionsWorkflow(KnowledgeBase(root), logger=logger)
