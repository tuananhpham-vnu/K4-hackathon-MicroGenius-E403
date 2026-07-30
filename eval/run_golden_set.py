"""Run the repository golden set and write an honest, reproducible report."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from admissions_mas.services.observability import TraceLogger
from admissions_mas.services.workflow import create_workflow


def main() -> int:
    cases = json.loads((ROOT / "eval" / "golden_set.json").read_text(encoding="utf-8"))
    workflow = create_workflow(ROOT, logger=TraceLogger(ROOT / "logs" / "eval.jsonl", console=False))
    results = []
    for case in cases:
        result = workflow.answer(case["query"], request_id=f"eval_{case['id'].lower()}")
        checks = {
            "intent": result["orchestration"]["intent"] == case["expected_intent"],
            "human_route": result["validation"]["needs_human"] == case["expect_human"],
            "evidence": len(result["evidence"]) >= case["min_evidence"],
        }
        if "expect_clarification" in case:
            checks["clarification"] = result["orchestration"]["need_clarification"] == case["expect_clarification"]
        results.append({
            "id": case["id"],
            "category": case["category"],
            "passed": all(checks.values()),
            "checks": checks,
            "actual_intent": result["orchestration"]["intent"],
            "actual_human": result["validation"]["needs_human"],
            "evidence_count": len(result["evidence"]),
        })

    passed = sum(item["passed"] for item in results)
    report = {
        "total": len(results),
        "passed": passed,
        "pass_rate": round(passed / len(results), 3),
        "quality_bar": 0.8,
        "quality_bar_met": passed / len(results) >= 0.8,
        "results": results,
    }
    (ROOT / "eval" / "results.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: report[key] for key in ("total", "passed", "pass_rate", "quality_bar_met")}, ensure_ascii=False))
    return 0 if report["quality_bar_met"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
