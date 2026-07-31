import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from admissions_mas.domain.models import Evidence
from admissions_mas.services.synthesis import GeminiSynthesisService


class SynthesisTests(unittest.TestCase):
    def test_gemini_synthesis_falls_back_with_source_citation_without_key(self):
        old_key = os.environ.pop("GEMINI_API_KEY", None)
        try:
            service = GeminiSynthesisService()
            response = service.synthesize(
                query="Quyền lợi là gì?",
                evidence=[
                    Evidence(
                        evidence_id="ev_1",
                        source_id="src_1",
                        quote="Học viên được miễn học phí và nhận phụ cấp theo chính sách chương trình.",
                        locator="paragraph-1",
                        relevance_score=0.8,
                        source_trust_score=0.92,
                        query="Quyền lợi là gì?",
                        source_check_passed=True,
                        source_title="admissions",
                        source_uri="docs/admissions.md",
                    )
                ],
                risk_level="low",
                validation={"needs_human": False},
            )
            self.assertIn("admissions", response)
            self.assertIn("miễn học phí", response)
        finally:
            if old_key is not None:
                os.environ["GEMINI_API_KEY"] = old_key


if __name__ == "__main__":
    unittest.main()
