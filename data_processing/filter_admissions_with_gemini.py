"""Find admissions-consultation questions that were misclassified as student support.

Set GEMINI_API_KEY in the environment, edit INPUT/OUTPUT if needed, then run:
    python scripts/filter_admissions_with_gemini.py
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]

# Keep credentials in the repository's ignored .env file.  ``override=False``
# lets an explicitly set PowerShell environment variable take precedence.
load_dotenv(ROOT_DIR / ".env", override=False)

# Change these paths when processing a different dataset.
INPUT = "data/facebook_student_support.json"
OUTPUT = "data/facebook_admissions_from_student_support.json"

MODEL = "gemini-3.5-flash-lite"
BATCH_SIZE = 10
MAX_RETRIES = 6
# One API call handles a complete batch.  Five seconds between calls keeps the
# script below the common free-tier limit of 15 requests per minute.
MIN_REQUEST_INTERVAL_SECONDS = 5.0
MAX_RETRY_DELAY_SECONDS = 90.0

_last_request_started_at = 0.0

SYSTEM_INSTRUCTION = """
Bạn là bộ phân loại dữ liệu cho chatbot tư vấn tuyển sinh Chương trình AI Thực Chiến.

Với mỗi bài đăng Facebook, hãy xác định bài có chứa câu hỏi hoặc nhu cầu tư vấn tuyển
sinh hay không. Đánh dấu true nếu nội dung hỏi về điều kiện tham gia, bằng cấp/nền tảng,
kinh nghiệm, kiến thức cần ôn, chứng chỉ, bài test/phỏng vấn, hồ sơ/đăng ký, deadline,
kết quả tuyển sinh, học phí/học bổng, khóa đang tuyển, địa điểm hoặc hình thức học trước
khi đăng ký. Một bài vừa nói chuyện học tập vừa hỏi điều kiện/phỏng vấn vẫn phải là true.

Đánh dấu false nếu bài chỉ hỗ trợ học viên đã nhập học, ví dụ lịch lớp, bài tập, điểm danh,
tài khoản, mentor, hoạt động nội bộ; hoặc nếu không có nhu cầu tư vấn tuyển sinh.

Chỉ trả về JSON array. Mỗi phần tử phải có đúng ba field:
{"index": <số nguyên>, "is_admissions_question": <true/false>, "reason": <lý do ngắn bằng tiếng Việt>}.
""".strip()


def get_api_key() -> str:
    """Read the Gemini API key without storing secrets in source code."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Thiếu GEMINI_API_KEY. PowerShell: $env:GEMINI_API_KEY = 'your-api-key'"
        )
    return api_key


def get_response_text(response: dict[str, Any]) -> str:
    """Extract generated text from a Gemini generateContent response."""
    try:
        parts = response["candidates"][0]["content"]["parts"]
        return "".join(part.get("text", "") for part in parts)
    except (IndexError, KeyError, TypeError) as error:
        raise ValueError(f"Gemini response không có nội dung hợp lệ: {response}") from error


def parse_json_array(text: str) -> list[dict[str, Any]]:
    """Parse model JSON, tolerating an accidental Markdown code fence."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    parsed = json.loads(cleaned)
    if not isinstance(parsed, list):
        raise ValueError("Gemini phải trả về một JSON array.")
    return parsed


def retry_delay_seconds(error: Exception, attempt: int) -> float:
    """Back off safely, respecting a numeric Retry-After response header."""
    delay = min(10.0 * (2 ** (attempt - 1)), MAX_RETRY_DELAY_SECONDS)
    if isinstance(error, urllib.error.HTTPError):
        retry_after = error.headers.get("Retry-After")
        if retry_after:
            try:
                delay = max(delay, float(retry_after))
            except ValueError:
                pass
    return min(delay, MAX_RETRY_DELAY_SECONDS)


def wait_for_request_slot() -> None:
    """Throttle requests so a complete run does not cause HTTP 429 errors."""
    global _last_request_started_at
    remaining = MIN_REQUEST_INTERVAL_SECONDS - (time.monotonic() - _last_request_started_at)
    if remaining > 0:
        time.sleep(remaining)
    _last_request_started_at = time.monotonic()


def classify_batch(posts: list[dict[str, Any]], api_key: str) -> list[dict[str, Any]]:
    """Ask Gemini to classify one batch of main post texts."""
    items = [
        {"index": index, "text": post.get("text", "")}
        for index, post in enumerate(posts)
    ]
    request_body = {
        "systemInstruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
        "contents": [{"role": "user", "parts": [{"text": json.dumps(items, ensure_ascii=False)}]}],
        "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
    request = urllib.request.Request(
        url,
        data=json.dumps(request_body, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST",
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            wait_for_request_slot()
            with urllib.request.urlopen(request, timeout=60) as response:
                response_data = json.loads(response.read().decode("utf-8"))
            classifications = parse_json_array(get_response_text(response_data))
            return validate_classifications(classifications, len(posts))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError) as error:
            if attempt == MAX_RETRIES:
                raise RuntimeError(f"Gemini lỗi ở batch sau {MAX_RETRIES} lần thử: {error}") from error
            delay = retry_delay_seconds(error, attempt)
            if isinstance(error, urllib.error.HTTPError) and error.code == 429:
                print(f"Gemini rate limit (HTTP 429); waiting {delay:.0f}s before retrying...")
            else:
                print(f"Gemini request failed ({error}); retrying in {delay:.0f}s...")
            time.sleep(delay)

    raise RuntimeError("Không thể phân loại batch.")


def validate_classifications(
    classifications: list[dict[str, Any]], expected_count: int
) -> list[dict[str, Any]]:
    """Ensure Gemini returned exactly one valid result for every input post."""
    by_index: dict[int, dict[str, Any]] = {}
    for item in classifications:
        index = item.get("index")
        is_admissions_question = item.get("is_admissions_question")
        reason = item.get("reason")
        if not isinstance(index, int) or not isinstance(is_admissions_question, bool) or not isinstance(reason, str):
            raise ValueError(f"Kết quả Gemini sai schema: {item}")
        if index in by_index:
            raise ValueError(f"Kết quả Gemini có index trùng: {index}")
        by_index[index] = item

    if set(by_index) != set(range(expected_count)):
        raise ValueError("Gemini không trả về đủ kết quả cho batch.")
    return [by_index[index] for index in range(expected_count)]


def main() -> None:
    input_path = ROOT_DIR / INPUT
    output_path = ROOT_DIR / OUTPUT
    if not input_path.is_file():
        raise FileNotFoundError(f"Không tìm thấy file input: {input_path}")

    posts = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(posts, list):
        raise ValueError("File input phải là JSON array.")

    api_key = get_api_key()
    selected_posts: list[dict[str, Any]] = []
    for start in range(0, len(posts), BATCH_SIZE):
        batch = posts[start : start + BATCH_SIZE]
        classifications = classify_batch(batch, api_key)
        for post, classification in zip(batch, classifications):
            if classification["is_admissions_question"]:
                selected_posts.append({
                    **post,
                    "gemini_classification": {
                        "is_admissions_question": True,
                        "reason": classification["reason"],
                        "model": MODEL,
                    },
                })
        print(f"Processed {min(start + BATCH_SIZE, len(posts))}/{len(posts)} posts")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(selected_posts, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Created: {output_path}")
    print(f"Admissions-consultation posts: {len(selected_posts)}")


if __name__ == "__main__":
    main()
