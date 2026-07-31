import re
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any

from ..domain.models import Evidence
from ..infrastructure.text import now_iso, tokens
from ..prompts.xml_prompt import XmlPrompt
from ..retrieval.knowledge_base import KnowledgeBase
from .observability import TraceLogger
from .synthesis import GeminiSynthesisService

# Phrases that flag a request as something the chatbot must never decide on its
# own (admission outcomes, exceptions, complaints, deadline/profile changes).
HIGH_RISK_WORDS = (
    "khiếu nại", "ngoại lệ", "phê duyệt", "trúng tuyển", "học bổng chắc chắn",
    "tình trạng hồ sơ", "gia hạn", "xét lại", "duyệt hồ sơ", "đặc cách",
)

# Requests that fall outside admissions consulting altogether, or that ask for
# data/actions the chatbot must refuse without ever touching the knowledge base.
OUT_OF_SCOPE_WORDS = (
    "dự báo thời tiết", "mật khẩu", "viết hộ", "làm hộ", "hack", "xóa hồ sơ",
    "đặt vé", "số điện thoại của", "email và số điện thoại", "tất cả ứng viên",
)

GREETING_PATTERN = re.compile(r"\b(chào|hello|hi)\b", re.IGNORECASE)
THANK_PATTERN = re.compile(r"cảm ơn|cám ơn|\bthank", re.IGNORECASE)

# Rule-based fast path (no LLM call): a bare confirmation/denial reply to a
# clarification the bot itself just asked. Only the exact word/phrase counts —
# "không" as negation inside a longer sentence must NOT match here.
CANCEL_WORDS = {"không", "sai", "không phải", "thôi", "bỏ đi", "hủy", "huỷ"}

# Meta questions about the assistant itself ("what can you do?") rather than a
# concrete admissions question. These should get a flexible, LLM-phrased
# description of scope instead of being forced through the rigid "please
# clarify your admissions question" template that short/anchor-less queries
# otherwise fall into.
CAPABILITY_PATTERN = re.compile(
    r"làm được (những )?gì|làm (được )?gì cho|giúp (được )?gì|hỗ trợ (được )?(những )?gì|"
    r"có thể (giúp|làm) gì|chức năng (của )?(bạn|mình)|bạn là ai|bạn là gì|"
    r"what can you do|who are you",
    re.IGNORECASE,
)

# Presence of one of these means the query already names a concrete topic, so
# a short question shouldn't be treated as too vague to answer.
ANCHOR_WORDS = (
    "chương trình", "khóa", "lộ trình", "hồ sơ", "tuyển sinh", "đăng ký",
    "đầu vào", "hạn nộp", "vòng", "phỏng vấn",
)

COMMUNITY_SOURCE_MARKERS = (
    "nhóm facebook", "trên facebook", "group facebook", "đọc trong nhóm",
    "nghe nói", "trên mạng xã hội",
)

PROFILE_SIGNAL_PATTERNS = {
    "education": re.compile(r"tốt nghiệp|đại học|cao đẳng|trung cấp|bằng cấp|sinh viên|cử nhân|chưa có bằng", re.IGNORECASE),
    "experience": re.compile(r"kinh nghiệm|tự học|lập trình|python|\d+\s*(năm|tháng)", re.IGNORECASE),
    "availability": re.compile(r"toàn thời gian|bán thời gian|tham gia đầy đủ|full.?time", re.IGNORECASE),
}

COHORT_PATTERN = re.compile(r"khóa\s*(\d+)", re.IGNORECASE)
DATE_PATTERN = re.compile(r"\d{1,2}/\d{1,2}")

CONTACT_LINE = "cán bộ tuyển sinh (email: AIthucchien@vinuni.edu.vn, hotline: 0979.489.846)"

NOT_ENOUGH_EVIDENCE_TEXT = (
    "Mình chưa tìm thấy bằng chứng đủ tin cậy từ tài liệu chính thức cho câu hỏi này. "
    f"Bạn vui lòng cung cấp thêm chi tiết hoặc liên hệ {CONTACT_LINE} để được xác nhận."
)

HIGH_RISK_TEXT = (
    "Mình không thể xác nhận, phê duyệt, thay đổi hồ sơ/hạn nộp hay đưa ra bất kỳ quyết định "
    "tuyển sinh nào (kết quả trúng tuyển, ngoại lệ, khiếu nại, học bổng...) qua chatbot. "
    f"Trường hợp này cần {CONTACT_LINE} trực tiếp xem xét và xử lý."
)

OUT_OF_SCOPE_TEXT = (
    "Mình không thể thực hiện yêu cầu này vì nó nằm ngoài phạm vi tư vấn tuyển sinh (tra cứu "
    "thông tin từ nguồn chính thức). Mình không tìm kiếm, tiết lộ hay chỉnh sửa dữ liệu cá nhân/"
    f"hồ sơ, và không hỗ trợ các tác vụ ngoài tư vấn. Nếu cần hỗ trợ về hồ sơ, vui lòng liên hệ {CONTACT_LINE}."
)

CONFLICTING_SOURCES_TEXT = (
    "Câu hỏi này nhắc tới hai nguồn có thông tin khác nhau, nên mình không thể tự chọn một "
    f"đáp án. Trường hợp nguồn mâu thuẫn cần {CONTACT_LINE} xác nhận tài liệu/thông tin hiện hành."
)

GENERIC_CLARIFICATION_TEXT = (
    "Mình cần thêm thông tin để tra cứu chính xác. Bạn vui lòng nêu rõ khóa học, mốc thời gian "
    "hoặc nội dung tuyển sinh (điều kiện, hồ sơ, lịch học, chi phí...) bạn muốn hỏi."
)

RECOMMENDATION_CLARIFICATION_TEXT = (
    "Để đánh giá mức độ phù hợp, bạn vui lòng cho mình biết thêm: trình độ học vấn/chuyên ngành, "
    "kinh nghiệm liên quan (lập trình, dữ liệu...) và bạn có thể tham gia toàn thời gian hay "
    "không. Dựa trên thông tin đó mình sẽ đối chiếu với tiêu chí tuyển sinh hiện hành."
)

# Templates the bot itself sends when it's waiting on the user for more
# detail. Used to recognize, from history alone, that the *previous* turn was
# a clarification request — so a bare "thôi"/"hủy" reply can be resolved by
# rule instead of looping back into another clarification ask.
CLARIFICATION_TEMPLATES = (GENERIC_CLARIFICATION_TEXT, RECOMMENDATION_CLARIFICATION_TEXT)

CANCEL_ACK_TEXT = (
    "Được rồi, mình dừng câu hỏi này lại. Bạn cứ hỏi mình nội dung khác về tuyển sinh bất cứ lúc "
    "nào nhé."
)

COMMUNITY_SOURCE_NOTICE = (
    "Mình không dùng thông tin từ bài đăng/nhóm cộng đồng để kết luận, chỉ dựa trên tài liệu "
    "chính thức đã kiểm chứng. "
)

CHITCHAT_GREETING_TEXT = (
    "Chào bạn. Mình có thể hỗ trợ tra cứu thông tin chương trình, điều kiện, lịch tuyển sinh và "
    "hướng dẫn hồ sơ."
)

CHITCHAT_THANKS_TEXT = (
    "Không có gì, rất vui được hỗ trợ bạn! Nếu cần thêm thông tin về tuyển sinh, cứ hỏi mình nhé."
)

INTENT_MAPPINGS = {
    "điều kiện": "admission_requirements",
    "phù hợp": "program_recommendation",
    "so sánh": "program_comparison",
    "học phí": "tuition_and_scholarship",
    "chi phí": "tuition_and_scholarship",
    "học bổng": "tuition_and_scholarship",
    "phụ cấp": "tuition_and_scholarship",
    "quyền lợi": "tuition_and_scholarship",
    "hạn": "deadline_information",
    "đăng ký": "application_process",
    "nộp hồ sơ": "application_process",
}


def _classify_chitchat(query: str) -> str | None:
    if THANK_PATTERN.search(query) and len(tokens(query)) < 6:
        return "thanks"
    if GREETING_PATTERN.search(query) and len(tokens(query)) < 4:
        return "greeting"
    return None


def _is_ambiguous(query: str) -> bool:
    lowered = query.lower()
    has_anchor = any(word in lowered for word in ANCHOR_WORDS)
    return not has_anchor and len(tokens(query)) < 5


def _has_topic_marker(query: str) -> bool:
    """Broader anchor set than `_is_ambiguous`: also counts an INTENT_MAPPINGS
    keyword or a concrete cohort/date value as naming a real topic.

    Only meant to be applied when the user is directly replying to the bot's
    own clarification ask (see CLARIFICATION_TEMPLATES below) — a bare reply
    like "Học phí" answers "nêu rõ ... nội dung tuyển sinh (điều kiện, hồ sơ,
    ... chi phí...)" even though "học phí" isn't in ANCHOR_WORDS. Applying
    this broader set to a fresh, unprompted first turn would wrongly treat
    genuinely vague queries ("Hạn bao giờ?") as already answered.
    """
    lowered = query.lower()
    return (
        any(word in lowered for word in ANCHOR_WORDS)
        or any(marker in lowered for marker in INTENT_MAPPINGS)
        or bool(COHORT_PATTERN.search(query))
        or bool(DATE_PATTERN.search(query))
    )


def _has_conflicting_sources(query: str) -> bool:
    lowered = query.lower()
    dates = set(DATE_PATTERN.findall(query))
    return len(dates) >= 2 and ("nhưng" in lowered or "mâu thuẫn" in lowered)


def _mentions_community_source(query: str) -> bool:
    lowered = query.lower()
    return any(marker in lowered for marker in COMMUNITY_SOURCE_MARKERS)


def extract_profile_signals(query: str) -> dict[str, str]:
    """Pull self-declared education/experience/availability facts out of free text."""
    return {field: query for field, pattern in PROFILE_SIGNAL_PATTERNS.items() if pattern.search(query)}


def _last_user_message(history: list[dict[str, str]] | None) -> str:
    """Most recent prior user turn, used to resolve elliptical follow-ups ("Còn phụ cấp thì sao?")."""
    for turn in reversed(history or []):
        role = str(turn.get("role") or "").lower()
        text = str(turn.get("text") or turn.get("content") or "").strip()
        if role in ("user", "human") and text:
            return text
    return ""


def _last_assistant_message(history: list[dict[str, str]] | None) -> str:
    """Most recent prior bot turn — used to tell what question the user is replying to."""
    for turn in reversed(history or []):
        role = str(turn.get("role") or "").lower()
        text = str(turn.get("text") or turn.get("content") or "").strip()
        if role in ("assistant", "bot", "ai") and text:
            return text
    return ""


def _is_cancel_reply(query: str, history: list[dict[str, str]] | None) -> bool:
    """Fast-path rule: bare "thôi/hủy/không..." replying to the bot's own clarification ask.

    Only the exact word/phrase counts, so this never fires on "không" used as
    negation inside an ordinary sentence. No LLM call needed either way.
    """
    normalized = query.strip().lower().rstrip(".!?")
    if normalized not in CANCEL_WORDS:
        return False
    last_assistant = _last_assistant_message(history).strip()
    return last_assistant in CLARIFICATION_TEMPLATES


class AdmissionsWorkflow:
    """Domain services used by both the legacy facade and LangGraph nodes."""

    def __init__(self, knowledge_base: KnowledgeBase, logger: TraceLogger | None = None, synthesis: GeminiSynthesisService | None = None):
        self.kb = knowledge_base
        self.audit_log: list[dict[str, Any]] = []
        self.logger = logger or TraceLogger()
        self.synthesis = synthesis or GeminiSynthesisService()
        self._max_known_cohort_cache: int | None = None

    def _audit(self, request_id: str, agent: str, payload: dict[str, Any]) -> None:
        self.audit_log.append({"timestamp": now_iso(), "request_id": request_id, "agent": agent, "payload": payload})
        self.logger.event(request_id=request_id, step=agent, component="workflow", payload=payload)

    def orchestrate(self, query: str, profile: dict[str, Any] | None = None, history: list[dict[str, str]] | None = None) -> dict[str, Any]:
        profile = profile or {}
        lowered = query.lower()
        is_chitchat = _classify_chitchat(query) is not None
        is_out_of_scope = any(word in lowered for word in OUT_OF_SCOPE_WORDS)
        is_capability_question = not is_chitchat and not is_out_of_scope and bool(CAPABILITY_PATTERN.search(query))
        is_cancel = (
            not is_chitchat and not is_out_of_scope and not is_capability_question
            and _is_cancel_reply(query, history)
        )
        risk = "high" if any(word in lowered for word in HIGH_RISK_WORDS) else "low"
        intent = "program_information"
        for marker, candidate_intent in INTENT_MAPPINGS.items():
            if marker in lowered:
                intent = candidate_intent
                break
        resolved_intent = (
            "chitchat" if is_chitchat else
            "out_of_scope" if is_out_of_scope else
            "capability_question" if is_capability_question else
            "cancel_clarification" if is_cancel else
            intent
        )

        # Elliptical follow-ups ("Còn phụ cấp thì sao?") look ambiguous on their
        # own but are perfectly clear combined with the previous user turn — so
        # only fall back to asking for clarification if the query is still
        # anchor-less once the prior turn is folded in.
        contextual_query = query
        need_clarification = False
        if not is_chitchat and not is_out_of_scope and not is_capability_question and not is_cancel:
            if resolved_intent == "program_recommendation":
                signals = {**extract_profile_signals(query), **{k: v for k, v in profile.items() if v}}
                need_clarification = any(field not in signals for field in ("education", "experience", "availability"))
            else:
                ambiguous = _is_ambiguous(query)
                if ambiguous:
                    last_user = _last_user_message(history)
                    if last_user:
                        combined = f"{last_user} {query}"
                        if not _is_ambiguous(combined):
                            contextual_query = combined
                            ambiguous = False
                # Second-turn reply to the bot's own clarification ask: a
                # short, topic-only answer ("Học phí") should count as having
                # supplied the missing information instead of looping back
                # into another clarification round.
                if ambiguous and _has_topic_marker(query) and _last_assistant_message(history).strip() in CLARIFICATION_TEMPLATES:
                    ambiguous = False
                need_clarification = ambiguous

        skip_retrieval = is_chitchat or is_out_of_scope or is_capability_question or is_cancel
        return {
            "intent": resolved_intent, "is_chitchat": is_chitchat, "is_out_of_scope": is_out_of_scope,
            "is_capability_question": is_capability_question, "is_cancel": is_cancel, "contextual_query": contextual_query,
            "clarity_score": min(10, max(1, len(tokens(query)) // 2 + 3)), "risk_level": risk, "need_summary": False,
            "need_clarification": need_clarification, "need_human": risk == "high",
            "next_agent": "synthesis" if skip_retrieval else "admissions_analyst",
        }

    def analyze(self, query: str, orchestration: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
        merged_profile = {**extract_profile_signals(query), **{k: v for k, v in profile.items() if v}}
        missing = []
        if orchestration["intent"] == "program_recommendation":
            missing = [field for field in ("education", "experience", "availability") if field not in merged_profile]
        # Use the history-resolved contextual query (raw query + prior user
        # turn, when the raw query alone was anchor-less) so a follow-up like
        # "Còn phụ cấp thì sao?" retrieves against "học phí ... phụ cấp" instead
        # of just the fragment.
        contextual_query = orchestration.get("contextual_query", query)
        lowered = contextual_query.lower()
        expansions = {
            "admission_requirements": "đối tượng điều kiện tiêu chí ứng tuyển",
            "tuition_and_scholarship": "miễn 100% học phí phụ cấp 8 triệu quyền lợi",
            "deadline_information": "hạn nộp hồ sơ mốc thời gian tuyển sinh",
            "application_process": "quy trình nộp hồ sơ ứng tuyển đăng ký",
            "program_recommendation": "đối tượng phù hợp điều kiện nền tảng dự tuyển yêu cầu học vấn kinh nghiệm",
        }
        extra = expansions.get(orchestration["intent"], "")
        if any(marker in lowered for marker in ("bao lâu", "kéo dài", "thời lượng")):
            extra += " 12 tuần thời gian đào tạo lộ trình"
        if any(marker in lowered for marker in ("quyền lợi", "phụ cấp")):
            extra += " miễn học phí phụ cấp quyền lợi học viên"
        if any(marker in lowered for marker in ("kết quả", "thông báo")):
            extra += " kết quả dự thi thông báo email cá nhân ứng viên"
        # Long personal narratives (self-described education/experience) dilute
        # lexical overlap against the (much shorter) eligibility-criteria docs,
        # so recommendation queries search on the topic expansion alone rather
        # than the raw narrative — the narrative itself is only needed for the
        # profile-completeness check above, not for finding the criteria text.
        query_for_retrieval = "" if orchestration["intent"] == "program_recommendation" else contextual_query
        retrieval_query = f"{query_for_retrieval} {extra}".strip()
        return {"retrieval_query": retrieval_query, "rewritten_query": f"{query}. Trả lời dựa trên bằng chứng đã kiểm tra nguồn và nêu rõ giới hạn dữ liệu.", "intent": orchestration["intent"], "entities": merged_profile, "missing_information": missing, "sub_tasks": ["Tìm bằng chứng liên quan", "Kiểm tra độ tin cậy và tính cập nhật", "Tổng hợp câu trả lời có nguồn"]}

    def validate(self, evidence: list[Evidence], risk: str) -> dict[str, Any]:
        valid = [item for item in evidence if item.source_check_passed and item.relevance_score >= 0.30]
        avg_relevance = sum(item.relevance_score for item in valid) / len(valid) if valid else 0.0
        avg_trust = sum(item.source_trust_score for item in valid) / len(valid) if valid else 0.0
        passed = len(valid) >= 1 and avg_relevance >= 0.30 and avg_trust >= 0.70
        return {"passed": passed, "source_check_passed": bool(valid), "evidence_count": len(valid), "avg_relevance": round(avg_relevance, 3), "avg_source_trust": round(avg_trust, 3), "risk_level": risk, "needs_human": risk == "high" or not passed, "rejection_reasons": [] if passed else ["Không đủ evidence đạt ngưỡng source/relevance"]}

    def _max_known_cohort(self) -> int:
        # Community posts (Facebook chatter) mention every cohort number
        # speculatively ("khi nào khóa 7 mở đơn?") — only official, citable
        # sources may define what the "current" cohort actually is.
        if self._max_known_cohort_cache is None:
            numbers = [
                int(match)
                for document in self.kb.documents
                if self.kb.sources[document["source_id"]].authority == "approved_local"
                and self.kb.sources[document["source_id"]].trust_score >= 0.7
                for match in COHORT_PATTERN.findall(document["text"])
            ]
            self._max_known_cohort_cache = max(numbers) if numbers else 0
        return self._max_known_cohort_cache

    def _cohort_status(self, query: str, usable_evidence: list[Evidence]) -> tuple[str, int] | None:
        """Classify a "khóa N" mention in the query against what the corpus actually covers.

        Returns None when there is no cohort mention or the exact cohort is
        already grounded in evidence. "soft" means N is plausibly the next
        cohort after the newest one on record (answer with the closest known
        info plus a caveat). "hard" means N is not a real/known cohort at all
        (refuse rather than guess).
        """
        match = COHORT_PATTERN.search(query)
        if not match:
            return None
        cohort = int(match.group(1))
        combined = " ".join(item.quote for item in usable_evidence).lower()
        if f"khóa {cohort}" in combined or f"khóa{cohort}" in combined:
            return None
        max_known = self._max_known_cohort()
        return ("soft" if usable_evidence and cohort <= max_known + 1 else "hard", cohort)

    def _hard_cohort_text(self, cohort: int) -> str:
        return (
            f"Tài liệu chính thức mình đang có chưa đủ căn cứ về Khóa {cohort} — không tìm thấy "
            f"thông tin nào đề cập tới khóa này. Để tránh cung cấp sai thông tin, bạn vui lòng "
            f"liên hệ {CONTACT_LINE} để được xác nhận chính xác cho Khóa {cohort}."
        )

    def _soft_cohort_prefix(self, cohort: int) -> str:
        max_known = self._max_known_cohort()
        return (
            f"Tài liệu hiện có chưa tách riêng thông tin cho Khóa {cohort}; đây là thông tin gần "
            f"nhất mình có, áp dụng cho Khóa {max_known} (khóa đang tuyển sinh hiện tại) — bạn nên "
            f"xác nhận lại với {CONTACT_LINE} nếu cần chính xác cho Khóa {cohort}. "
        )

    def _ungrounded_numbers(self, query: str, usable_evidence: list[Evidence]) -> bool:
        residual = COHORT_PATTERN.sub("", query)
        numbers = re.findall(r"\d{2,4}", residual)
        if not numbers:
            return False
        combined = " ".join(item.quote for item in usable_evidence)
        return any(number not in combined for number in numbers)

    def _happy_path_answer(self, query: str, usable_evidence: list[Evidence], orchestration: dict[str, Any],
                            validation: dict[str, Any], profile: dict[str, Any] | None, history: list[dict[str, str]] | None) -> str:
        return self.synthesis.synthesize(
            query=query, evidence=usable_evidence, risk_level=orchestration["risk_level"],
            validation=validation, human_required=False, profile=profile or {}, history=history or [],
        )

    def synthesize(self, query: str, orchestration: dict[str, Any], validation: dict[str, Any], usable_evidence: list[Evidence],
                    *, profile: dict[str, Any] | None = None, history: list[dict[str, str]] | None = None) -> tuple[str, list[Evidence]]:
        """Single source of truth for response text, shared by the legacy facade and the LangGraph nodes.

        Refusals, HITL routing and clarification are always fixed templates —
        the LLM (self.synthesis) is only ever invoked for the evidence-backed
        happy path, so it can never soften a safety-relevant decision.
        """
        if orchestration["is_chitchat"]:
            kind = _classify_chitchat(query)
            return (CHITCHAT_THANKS_TEXT if kind == "thanks" else CHITCHAT_GREETING_TEXT), []
        if orchestration["is_out_of_scope"]:
            return OUT_OF_SCOPE_TEXT, []
        if orchestration.get("is_capability_question"):
            return self.synthesis.answer_capability_question(query=query, history=history), []
        if orchestration.get("is_cancel"):
            return CANCEL_ACK_TEXT, []

        response: str
        evidence_out: list[Evidence]
        if _has_conflicting_sources(query):
            response, evidence_out = CONFLICTING_SOURCES_TEXT, []
        elif orchestration["risk_level"] == "high":
            response, evidence_out = HIGH_RISK_TEXT, []
        elif orchestration["need_clarification"]:
            is_recommendation = orchestration["intent"] == "program_recommendation"
            response, evidence_out = (RECOMMENDATION_CLARIFICATION_TEXT if is_recommendation else GENERIC_CLARIFICATION_TEXT), []
        elif not usable_evidence:
            response, evidence_out = NOT_ENOUGH_EVIDENCE_TEXT, []
        else:
            cohort_status = self._cohort_status(query, usable_evidence)
            if cohort_status and cohort_status[0] == "hard":
                response, evidence_out = self._hard_cohort_text(cohort_status[1]), []
            elif self._ungrounded_numbers(query, usable_evidence):
                response, evidence_out = NOT_ENOUGH_EVIDENCE_TEXT, []
            else:
                response = self._happy_path_answer(query, usable_evidence, orchestration, validation, profile, history)
                if cohort_status and cohort_status[0] == "soft":
                    response = self._soft_cohort_prefix(cohort_status[1]) + response
                evidence_out = usable_evidence

        if _mentions_community_source(query):
            response = COMMUNITY_SOURCE_NOTICE + response
        return response, evidence_out

    def answer(self, query: str, *, context=None, history=None, profile=None, request_id=None) -> dict[str, Any]:
        request_id = request_id or f"req_{uuid.uuid4().hex[:12]}"
        self.logger.event(request_id=request_id, step="request_start", component="workflow", payload={"query": query})
        profile = profile or {}
        orchestration = self.orchestrate(query, profile, history)
        if orchestration["is_chitchat"] or orchestration["is_out_of_scope"] or orchestration["is_capability_question"] or orchestration.get("is_cancel"):
            passed = orchestration["is_chitchat"] or orchestration["is_capability_question"] or orchestration.get("is_cancel", False)
            validation = {"passed": passed, "source_check_passed": False, "evidence_count": 0, "avg_relevance": 0.0, "avg_source_trust": 0.0, "risk_level": "low", "needs_human": False, "rejection_reasons": [] if passed else ["Yêu cầu nằm ngoài phạm vi tư vấn tuyển sinh"]}
            analysis, evidence, usable = {}, [], []
        else:
            analysis = self.analyze(query, orchestration, profile)
            evidence = self.kb.search(analysis["retrieval_query"], limit=8)
            validation = self.validate(evidence, orchestration["risk_level"])
            usable = [item for item in evidence if item.source_check_passed and item.relevance_score >= 0.30]
        response, usable = self.synthesize(query, orchestration, validation, usable, profile=profile, history=history)
        for agent, payload in (("orchestrator", orchestration), ("admissions_analyst", analysis), ("searcher", {"evidence": [asdict(item) for item in evidence]}), ("validator", validation), ("synthesis", {"response": response, "citation_count": len(usable), "model": self.synthesis.model_name if self.synthesis.configured else "fallback"})):
            self._audit(request_id, agent, payload)
        result = {"request_id": request_id, "response": response, "orchestration": orchestration, "analysis": analysis, "validation": validation, "evidence": [asdict(item) for item in usable], "sources": [asdict(self.kb.sources[item.source_id]) for item in usable], "prompt_xml": XmlPrompt.build(request_id, query, context, history, profile, usable)}
        self.logger.event(request_id=request_id, step="request_end", component="workflow", payload={"status": "completed", "citation_count": len(usable)})
        return result


def create_workflow(repo_root: Path | None = None, logger: TraceLogger | None = None) -> AdmissionsWorkflow:
    root = repo_root or Path(__file__).resolve().parents[3]
    return AdmissionsWorkflow(KnowledgeBase(root), logger=logger)
