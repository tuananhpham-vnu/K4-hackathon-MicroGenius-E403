"""Prompt contracts shared by every agent in the MAS graph."""

from pathlib import Path
from typing import Any

from ..domain.models import Evidence
from .xml_prompt import XmlPrompt


CONFIG_DIR = Path(__file__).resolve().parents[3] / "config"
COMMON_SYSTEM_PROMPT = (CONFIG_DIR / "system_prompt.txt").read_text(encoding="utf-8") if (CONFIG_DIR / "system_prompt.txt").exists() else ""


SYSTEM_PROMPTS: dict[str, str] = {
    "orchestrator": """Bạn là Orchestrator của VinAI Admissions Multi-Agent Assistant.
Phân loại intent, đánh giá clarity và risk, sau đó chọn agent tiếp theo.
Không tự trả lời nội dung tuyển sinh và không suy đoán khi thiếu dữ liệu.
Case khiếu nại, ngoại lệ, học bổng đặc biệt, cập nhật hồ sơ hoặc quyết định trúng tuyển phải chuyển HITL.""",
    "analyst": """Bạn là Admissions Analyst.
Phân tích query và history, trích xuất candidate profile, phát hiện dữ liệu thiếu,
viết lại query thành các sub-task rõ ràng cho Searcher. Không tạo facts mới.""",
    "searcher": """Bạn là Searcher.
Chỉ sử dụng nguồn được phê duyệt. Mỗi evidence bắt buộc giữ source_id, locator,
quote, source trust score và query relevance score. Không làm mất nguồn ở bất kỳ bước nào.""",
    "validator": """Bạn là Validator.
Kiểm tra source, relevance, độ đầy đủ, nhất quán và tính cập nhật của evidence.
Evidence không đạt ngưỡng phải bị loại hoặc yêu cầu retry. Không cho phép trả lời không có citation.""",
    "synthesis": """Bạn là Synthesis Agent.
Chỉ tổng hợp từ evidence đã được Validator thông qua. Trích dẫn source_id khi nêu facts,
nêu rõ giới hạn dữ liệu và không biến tư vấn tham khảo thành quyết định tuyển sinh.""",
}


def system_prompt(agent: str) -> str:
    role_prompt = SYSTEM_PROMPTS.get(agent, SYSTEM_PROMPTS["synthesis"])
    return f"{COMMON_SYSTEM_PROMPT}\n\nVai trò agent:\n{role_prompt}".strip()


def user_prompt(*, request_id: str, agent: str, query: str, context: dict[str, Any] | None = None,
                history: list[dict[str, str]] | None = None, profile: dict[str, Any] | None = None,
                evidence: list[Evidence] | None = None) -> str:
    envelope = XmlPrompt.build(request_id, query, context, history, profile, evidence or ())
    return envelope.replace("<agent>orchestrator</agent>", f"<agent>{agent}</agent>", 1)


def prompt_messages(*, request_id: str, agent: str, query: str, context=None, history=None,
                    profile=None, evidence=None) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": system_prompt(agent)},
        {"role": "user", "content": user_prompt(request_id=request_id, agent=agent, query=query, context=context, history=history, profile=profile, evidence=evidence)},
    ]
