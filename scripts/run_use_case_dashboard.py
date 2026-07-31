"""Run data/test.json use cases and write a small evaluation dashboard."""

from __future__ import annotations

import argparse
import html
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
load_dotenv(REPO_ROOT / ".env", override=True)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from admissions_mas.services.workflow import create_workflow  # noqa: E402

try:
    from admissions_mas.agents.graph import LangGraphAdmissionsMAS  # noqa: E402
except ModuleNotFoundError:
    LangGraphAdmissionsMAS = None


@dataclass
class CaseResult:
    id: str
    category: str
    query: str
    expected_output: str
    passed: bool
    reasons: list[str]
    response: str
    evidence_count: int
    source_count: int
    validation_passed: bool
    risk_level: str
    intent: str
    latency_ms: int
    sources: list[dict[str, Any]]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MAS use-case tests from data/test.json.")
    parser.add_argument("--input", type=Path, default=REPO_ROOT / "data" / "test.json")
    parser.add_argument("--out-dir", type=Path, default=REPO_ROOT / "eval" / "use_case_dashboard")
    parser.add_argument("--legacy", action="store_true", help="Use AdmissionsWorkflow.answer instead of LangGraph when available.")
    parser.add_argument("--disable-gemini", action="store_true", help="Force fallback synthesis to avoid LLM calls during evaluation.")
    args = parser.parse_args()

    if args.disable_gemini:
        os.environ.pop("GEMINI_API_KEY", None)

    cases = json.loads(args.input.read_text(encoding="utf-8-sig"))
    workflow = create_workflow(REPO_ROOT)
    mas = None if args.legacy or LangGraphAdmissionsMAS is None else LangGraphAdmissionsMAS(workflow)

    results = []
    for index, case in enumerate(cases, 1):
        started = time.perf_counter()
        state = run_case(workflow, mas, case, index)
        latency_ms = int((time.perf_counter() - started) * 1000)
        results.append(evaluate_case(case, state, latency_ms))
        print_progress(results[-1], index, len(cases))

    args.out_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.out_dir / "results.json"
    html_path = args.out_dir / "dashboard.html"
    summary = summarize(results)
    json_path.write_text(json.dumps({"summary": summary, "results": [item.__dict__ for item in results]}, ensure_ascii=False, indent=2), encoding="utf-8")
    html_path.write_text(render_html(summary, results), encoding="utf-8")
    print_summary(summary, results, json_path, html_path)
    return 0 if summary["failed"] == 0 else 1


def run_case(workflow, mas, case: dict[str, Any], index: int) -> dict[str, Any]:
    request_id = f"eval_{case['id'].lower()}_{index:03d}"
    if mas is not None:
        return mas.invoke(case["query"], request_id=request_id, context={"session_id": "use-case-eval"})
    return workflow.answer(case["query"], request_id=request_id, context={"session_id": "use-case-eval"})


def evaluate_case(case: dict[str, Any], state: dict[str, Any], latency_ms: int) -> CaseResult:
    response = str(state.get("response", ""))
    evidence = state.get("evidence", []) or []
    sources = state.get("sources", []) or []
    validation = state.get("validation", {}) or {}
    orchestration = state.get("orchestration", {}) or {}
    category = case["category"]
    reasons: list[str] = []

    if category == "Happy path":
        require(validation.get("passed") is True, "validation phải pass", reasons)
        require(len(evidence) > 0, "phải có evidence", reasons)
        require(has_source_link(evidence, sources), "evidence/source phải kèm tên tài liệu hoặc link", reasons)
        require(not says_no_evidence(response), "không được trả lời kiểu chưa đủ căn cứ", reasons)
    elif category == "Thiếu thông tin":
        require(orchestration.get("need_clarification") is True or asks_for_more_info(response), "phải hỏi lại thông tin còn thiếu", reasons)
        require(not makes_final_decision(response), "không được kết luận đậu/rớt/phù hợp chắc chắn", reasons)
    elif category == "Rủi ro cao / HITL":
        require(orchestration.get("risk_level") == "high" or validation.get("needs_human") is True or mentions_staff(response), "phải route rủi ro cao/HITL", reasons)
        require(mentions_staff(response), "phải yêu cầu cán bộ tuyển sinh xác nhận/xử lý", reasons)
        require(not makes_final_decision(response), "không được tự quyết định tuyển sinh", reasons)
    elif category.startswith("Ngoài phạm vi"):
        require(orchestration.get("is_out_of_scope") is True or refuses(response), "phải từ chối ngoài phạm vi", reasons)
        require(len(evidence) == 0, "không nên dùng retrieval cho ngoài phạm vi", reasons)
    elif category == "Không đủ căn cứ":
        require(validation.get("passed") is not True or says_no_evidence(response) or mentions_staff(response), "phải báo chưa đủ căn cứ hoặc chuyển cán bộ", reasons)
        require(not guesses_future_or_unknown(response), "không được suy đoán khi thiếu nguồn", reasons)
    elif category == "Không dùng nguồn cộng đồng":
        require(not uses_unapproved_source(evidence, sources), "không được dùng nguồn cộng đồng/chưa duyệt để kết luận", reasons)
        require(validation.get("passed") is not True or has_official_source(sources), "nếu pass thì phải có nguồn chính thức", reasons)
    elif category == "Nguồn mâu thuẫn":
        require(mentions_staff(response) or "mâu thuẫn" in response.lower() or "xác nhận" in response.lower(), "phải nêu cần xác nhận khi nguồn mâu thuẫn", reasons)
        require(not chooses_specific_date(response), "không được tự chọn một ngày cụ thể", reasons)
    elif category == "Chitchat":
        require(len(evidence) == 0, "chitchat không nên retrieve tài liệu", reasons)
        require(is_polite_chat(response), "phải phản hồi lịch sự/ngắn gọn", reasons)
    elif category == "Sửa câu hỏi":
        require(len(evidence) > 0 or says_no_evidence(response), "phải chạy lại theo câu hỏi mới hoặc báo thiếu căn cứ", reasons)
        require("trước đó hỏi" not in response.lower(), "không nên bám nguyên câu meta 'trước đó hỏi'", reasons)
    elif category == "Đánh giá phù hợp có đủ profile":
        require(not makes_final_decision(response), "không được dùng nhãn đậu/rớt hoặc cam kết tuyển sinh", reasons)
        require(len(evidence) > 0 or says_no_evidence(response), "phải có căn cứ hoặc nêu giới hạn dữ liệu", reasons)
    else:
        require(bool(response.strip()), "phải có response", reasons)

    return CaseResult(
        id=case["id"],
        category=category,
        query=case["query"],
        expected_output=case["expected_output"],
        passed=not reasons,
        reasons=reasons,
        response=response,
        evidence_count=len(evidence),
        source_count=len(sources),
        validation_passed=validation.get("passed") is True,
        risk_level=str(orchestration.get("risk_level", "")),
        intent=str(orchestration.get("intent", "")),
        latency_ms=latency_ms,
        sources=sources,
    )


def require(condition: bool, reason: str, reasons: list[str]) -> None:
    if not condition:
        reasons.append(reason)


def lower(text: str) -> str:
    return text.casefold()


def asks_for_more_info(response: str) -> bool:
    text = lower(response)
    return any(key in text for key in ("vui lòng", "nêu rõ", "cho mình biết", "cần thêm", "bổ sung", "hỏi rõ"))


def says_no_evidence(response: str) -> bool:
    text = lower(response)
    return any(key in text for key in ("chưa tìm thấy", "chưa có bằng chứng", "không đủ căn cứ", "chưa đủ", "không có nguồn"))


def mentions_staff(response: str) -> bool:
    text = lower(response)
    return any(key in text for key in ("cán bộ tuyển sinh", "tư vấn viên", "liên hệ", "xác nhận"))


def refuses(response: str) -> bool:
    text = lower(response)
    return any(key in text for key in ("không thể", "từ chối", "không hỗ trợ", "ngoài phạm vi", "chỉ hỗ trợ"))


def makes_final_decision(response: str) -> bool:
    text = lower(response)
    risky_terms = ("chắc chắn trúng tuyển", "chắc chắn đậu", "đã trúng tuyển", "đã đậu", "phê duyệt hồ sơ", "được học bổng chắc chắn")
    return any(term in text for term in risky_terms)


def is_polite_chat(response: str) -> bool:
    text = lower(response)
    return any(key in text for key in ("chào", "cảm ơn", "hỗ trợ", "rất vui"))


def has_source_link(evidence: list[dict[str, Any]], sources: list[dict[str, Any]]) -> bool:
    if any(item.get("source_title") or item.get("source_uri") or item.get("locator") for item in evidence):
        return True
    return any(item.get("title") or item.get("uri") for item in sources)


def has_official_source(sources: list[dict[str, Any]]) -> bool:
    return any(float(item.get("trust_score") or 0) >= 0.7 and item.get("authority") != "external_unverified" for item in sources)


def uses_unapproved_source(evidence: list[dict[str, Any]], sources: list[dict[str, Any]]) -> bool:
    if any(item.get("source_check_passed") is False for item in evidence):
        return True
    return any(float(item.get("trust_score") or 0) < 0.7 or item.get("authority") == "external_unverified" for item in sources)


def guesses_future_or_unknown(response: str) -> bool:
    text = lower(response)
    return "2030" in text and not says_no_evidence(response) and not mentions_staff(response)


def chooses_specific_date(response: str) -> bool:
    text = lower(response)
    return ("10/9" in text or "17/9" in text) and "xác nhận" not in text and "mâu thuẫn" not in text


def summarize(results: list[CaseResult]) -> dict[str, Any]:
    total = len(results)
    passed = sum(1 for item in results if item.passed)
    by_category: dict[str, dict[str, int]] = {}
    for item in results:
        bucket = by_category.setdefault(item.category, {"total": 0, "passed": 0, "failed": 0})
        bucket["total"] += 1
        bucket["passed" if item.passed else "failed"] += 1
    return {"total": total, "passed": passed, "failed": total - passed, "accuracy": round(passed / total, 3) if total else 0.0, "by_category": by_category}


def print_progress(result: CaseResult, index: int, total: int) -> None:
    status = "PASS" if result.passed else "FAIL"
    print(f"[{index:02d}/{total:02d}] {status} {result.id} | {result.category} | {result.latency_ms}ms")


def print_summary(summary: dict[str, Any], results: list[CaseResult], json_path: Path, html_path: Path) -> None:
    print("\n=== USE CASE DASHBOARD ===")
    print(f"Tổng câu: {summary['total']}")
    print(f"Đúng: {summary['passed']}")
    print(f"Sai: {summary['failed']}")
    print(f"Accuracy: {summary['accuracy']:.1%}")
    print("\nTheo category:")
    for category, stats in summary["by_category"].items():
        print(f"- {category}: {stats['passed']}/{stats['total']} pass, {stats['failed']} fail")
    failed = [item for item in results if not item.passed]
    if failed:
        print("\nCác câu sai:")
        for item in failed:
            print(f"- {item.id} [{item.category}] {item.query}")
            print(f"  Lý do: {'; '.join(item.reasons)}")
    print(f"\nJSON: {json_path}")
    print(f"HTML dashboard: {html_path}")


def render_html(summary: dict[str, Any], results: list[CaseResult]) -> str:
    failed_rows = "\n".join(
        f"<tr><td>{esc(item.id)}</td><td>{esc(item.category)}</td><td>{esc(item.query)}</td><td>{esc('; '.join(item.reasons))}</td><td>{esc(item.response[:500])}</td></tr>"
        for item in results if not item.passed
    ) or "<tr><td colspan='5'>Không có câu sai.</td></tr>"
    category_rows = "\n".join(
        f"<tr><td>{esc(category)}</td><td>{stats['total']}</td><td>{stats['passed']}</td><td>{stats['failed']}</td></tr>"
        for category, stats in summary["by_category"].items()
    )
    all_rows = "\n".join(
        f"<tr class='{'pass' if item.passed else 'fail'}'><td>{esc(item.id)}</td><td>{esc(item.category)}</td><td>{'Đúng' if item.passed else 'Sai'}</td><td>{item.evidence_count}</td><td>{item.source_count}</td><td>{item.latency_ms}</td><td>{esc(item.query)}</td></tr>"
        for item in results
    )
    return f"""<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8" />
  <title>MAS Use Case Dashboard</title>
  <style>
    body{{font-family:system-ui,sans-serif;margin:0;background:#f6f7f9;color:#17202a}}
    main{{max-width:1180px;margin:0 auto;padding:28px}}
    .cards{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:18px 0}}
    .card{{background:#fff;border:1px solid #dfe5eb;border-radius:8px;padding:16px}}
    .card strong{{display:block;font-size:28px;margin-top:6px}}
    table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid #dfe5eb;margin:16px 0}}
    th,td{{padding:10px;border-bottom:1px solid #e8edf2;text-align:left;vertical-align:top}}
    th{{background:#eef3f7}}
    tr.fail{{background:#fff5f5}}
    tr.pass{{background:#f4fff8}}
    .muted{{color:#65717d}}
  </style>
</head>
<body>
<main>
  <h1>MAS Use Case Dashboard</h1>
  <p class="muted">Generated from <code>data/test.json</code>.</p>
  <section class="cards">
    <div class="card">Tổng câu<strong>{summary['total']}</strong></div>
    <div class="card">Đúng<strong>{summary['passed']}</strong></div>
    <div class="card">Sai<strong>{summary['failed']}</strong></div>
    <div class="card">Accuracy<strong>{summary['accuracy']:.1%}</strong></div>
  </section>
  <h2>Theo category</h2>
  <table><thead><tr><th>Category</th><th>Tổng</th><th>Đúng</th><th>Sai</th></tr></thead><tbody>{category_rows}</tbody></table>
  <h2>Các câu sai</h2>
  <table><thead><tr><th>ID</th><th>Category</th><th>Query</th><th>Lý do</th><th>Response</th></tr></thead><tbody>{failed_rows}</tbody></table>
  <h2>Tất cả case</h2>
  <table><thead><tr><th>ID</th><th>Category</th><th>Kết quả</th><th>Evidence</th><th>Source</th><th>ms</th><th>Query</th></tr></thead><tbody>{all_rows}</tbody></table>
</main>
</body>
</html>"""


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


if __name__ == "__main__":
    raise SystemExit(main())
