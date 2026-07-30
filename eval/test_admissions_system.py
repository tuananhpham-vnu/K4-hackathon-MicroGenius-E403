import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from admissions_system import XmlPrompt, create_workflow
from mas.prompt_templates import prompt_messages
from mas.prompt_templates import prompt_messages


class TraceabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = create_workflow()

    def test_xml_round_trip_preserves_request_fields(self):
        xml = XmlPrompt.build("req_test", "câu hỏi", {"session_id": "s1"}, [{"id": "1", "role": "user", "text": "trước đó"}], {"major": "AI"})
        parsed = XmlPrompt.parse(xml)
        self.assertEqual(parsed["request_id"], "req_test")
        self.assertEqual(parsed["query"], "câu hỏi")
        self.assertEqual(parsed["context"]["session_id"], "s1")
        self.assertEqual(parsed["candidate_profile"]["major"], "AI")

    def test_query_keeps_source_and_scores(self):
        result = self.workflow.answer("AI chatbot support xác định bài toán cho ai?")
        self.assertIn("request_id", result)
        self.assertTrue(result["prompt_xml"].startswith("<request>"))
        self.assertEqual(len(result["evidence"]), len(result["sources"]))
        for evidence in result["evidence"]:
            self.assertTrue(evidence["source_id"])
            self.assertGreaterEqual(evidence["relevance_score"], 0.35)
            self.assertIn(evidence["source_id"], {source["source_id"] for source in result["sources"]})

    def test_high_risk_routes_to_human(self):
        result = self.workflow.answer("Tôi muốn khiếu nại và xin ngoại lệ tuyển sinh")
        self.assertTrue(result["orchestration"]["need_human"])
        self.assertTrue(result["validation"]["needs_human"])

    def test_agent_prompt_contract_contains_system_and_xml_user_prompt(self):
        messages = prompt_messages(request_id="req_prompt", agent="searcher", query="điều kiện tuyển sinh")
        self.assertEqual([message["role"] for message in messages], ["system", "user"])
        self.assertIn("source_id", messages[0]["content"])
        self.assertIn("<request>", messages[1]["content"])
        self.assertIn("<agent>searcher</agent>", messages[1]["content"])

    def test_system_and_user_prompts_are_traceable(self):
        messages = prompt_messages(request_id="req_prompt", agent="searcher", query="tìm điều kiện", profile={"major": "AI"})
        self.assertEqual([message["role"] for message in messages], ["system", "user"])
        self.assertIn("source_id", messages[0]["content"])
        self.assertIn("<request_id>req_prompt</request_id>", messages[1]["content"])
        self.assertIn("<agent>searcher</agent>", messages[1]["content"])
        self.assertIn("<candidate_profile>", messages[1]["content"])


if __name__ == "__main__":
    unittest.main()
