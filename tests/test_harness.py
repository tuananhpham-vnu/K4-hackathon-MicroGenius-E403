import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mas.harness import AgentHarness, GuardrailEngine, MemoryStore, ToolSpec


class HarnessTests(unittest.TestCase):
    def test_searcher_can_use_search_but_synthesis_cannot(self):
        harness = AgentHarness()
        harness.register_tool(ToolSpec("knowledge_base.search", "test search"), lambda query, limit: [query, limit])
        self.assertEqual(harness.invoke_tool("searcher", "knowledge_base.search", {}, query="q", limit=2), ["q", 2])
        with self.assertRaises(PermissionError):
            harness.invoke_tool("synthesis", "knowledge_base.search", {}, query="q", limit=2)

    def test_memory_is_scoped_by_session(self):
        harness = AgentHarness(memory=MemoryStore())
        state = {"request_id": "req_1", "context": {"session_id": "session_a"}}
        harness.remember(state, {"intent": "program_information"})
        self.assertEqual(harness.recall(state)[0]["intent"], "program_information")
        other = {"request_id": "req_2", "context": {"session_id": "session_b"}}
        self.assertEqual(harness.recall(other), [])

    def test_high_risk_guardrail_requires_human(self):
        guardrails = GuardrailEngine()
        self.assertTrue(guardrails.requires_hitl("xin ngoại lệ tuyển sinh", "low"))
        result = guardrails.check_output("Thông tin đã xác minh.", [], "high")
        self.assertFalse(result.passed)


if __name__ == "__main__":
    unittest.main()
