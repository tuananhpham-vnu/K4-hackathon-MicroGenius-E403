"""LLM-backed answer synthesis with grounded fallback."""

from __future__ import annotations

import os
from typing import Any

from ..domain.models import Evidence


class GeminiSynthesisService:
    def __init__(self) -> None:
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-3.5-flash-lite")
        self.temperature = self._read_float(("GEMINI_TEMPERATURE", "TEMP"), 0.2)
        self._client = None

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    @staticmethod
    def _read_float(names: tuple[str, ...], default: float) -> float:
        for name in names:
            value = os.getenv(name)
            if value is None:
                continue
            try:
                return float(value)
            except (TypeError, ValueError):
                continue
        try:
            return float(default)
        except (TypeError, ValueError):
            return default

    def synthesize(
        self,
        *,
        query: str,
        evidence: list[Evidence],
        risk_level: str,
        validation: dict[str, Any] | None = None,
        human_required: bool = False,
        profile: dict[str, Any] | None = None,
        history: list[dict[str, str]] | None = None,
    ) -> str:
        fallback = fallback_response(query=query, evidence=evidence, validation=validation, human_required=human_required)
        if not self.configured or not evidence:
            return fallback
        try:
            return self._generate(
                query=query,
                evidence=evidence[:5],
                risk_level=risk_level,
                validation=validation or {},
                human_required=human_required,
                profile=profile or {},
                history=history or [],
            )
        except Exception:
            return fallback

    def _client_instance(self):
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def _generate(
        self,
        *,
        query: str,
        evidence: list[Evidence],
        risk_level: str,
        validation: dict[str, Any],
        human_required: bool,
        profile: dict[str, Any],
        history: list[dict[str, str]],
    ) -> str:
        from google.genai import types
        response = self._client_instance().models.generate_content(
            model=self.model_name,
            contents=self._prompt(
                query=query,
                evidence=evidence,
                risk_level=risk_level,
                validation=validation,
                human_required=human_required,
                profile=profile,
                history=history,
            ),
            config=types.GenerateContentConfig(
                temperature=self.temperature,
                max_output_tokens=900,
            ),
        )
        text = getattr(response, "text", "") or ""
        return text.strip() or fallback_response(query=query, evidence=evidence, validation=validation, human_required=human_required)

    @staticmethod
    def _prompt(
        *,
        query: str,
        evidence: list[Evidence],
        risk_level: str,
        validation: dict[str, Any],
        human_required: bool,
        profile: dict[str, Any],
        history: list[dict[str, str]],
    ) -> str:
        evidence_block = "\n\n".join(
            f"[{index}] source_id={item.source_id}\n"
            f"title={item.source_title or item.source_id}\n"
            f"uri={item.source_uri}\n"
            f"locator={item.locator}\n"
            f"trust={item.source_trust_score}; relevance={item.relevance_score}\n"
            f"quote={item.quote}"
            for index, item in enumerate(evidence, 1)
        )
        return f"""Bạn là Synthesis Agent cho hệ tư vấn tuyển sinh.

Nhiệm vụ: trả lời bằng tiếng Việt tự nhiên, ngắn gọn, hữu ích, chỉ dựa trên evidence đã được Validator thông qua.

Quy tắc bắt buộc:
- Không bịa thông tin ngoài evidence.
- Khi nêu một ý quan trọng, trích nguồn trong ngoặc vuông bằng tên tài liệu hoặc link, ví dụ [Tên tài liệu] hoặc [https://...].
- Nếu evidence chưa đủ để kết luận, nói rõ giới hạn dữ liệu và đề nghị bổ sung thông tin.
- Không đưa ra quyết định tuyển sinh chính thức.
- Nếu human_required=true hoặc risk_level=high, thêm câu rằng cán bộ tuyển sinh cần xác nhận trước khi kết luận chính thức.
- Không nhắc các chi tiết kỹ thuật như token, vector, hybrid search, agent, Validator.

User query:
{query}

Candidate profile:
{profile}

Recent history:
{history[-5:]}

Risk level: {risk_level}
Human required: {human_required}
Validation: {validation}

Evidence:
{evidence_block}

Hãy trả lời trực tiếp cho user."""


def fallback_response(
    *,
    query: str,
    evidence: list[Evidence],
    validation: dict[str, Any] | None = None,
    human_required: bool = False,
) -> str:
    validation = validation or {}
    if not evidence:
        response = "Mình chưa tìm thấy bằng chứng đủ tin cậy cho câu hỏi này. Bạn vui lòng cung cấp thêm chi tiết hoặc chờ cán bộ tuyển sinh xác nhận."
    else:
        parts = []
        for item in evidence[:3]:
            source_label = item.source_title or item.source_uri or item.source_id
            parts.append(f"{item.quote} [{source_label}]")
        response = (
            "Theo các tài liệu hiện có, thông tin liên quan là: "
            + " ".join(parts)[:1100]
            + " Đây là tư vấn tham khảo dựa trên dữ liệu đã kiểm tra nguồn, không phải quyết định tuyển sinh chính thức."
        )
    if human_required or validation.get("needs_human"):
        response += " Trường hợp này cần cán bộ tuyển sinh kiểm tra trước khi đưa ra kết luận chính thức."
    return response
