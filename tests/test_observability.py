import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mas.observability import TraceLogger


class ObservabilityTests(unittest.TestCase):
    def test_trace_logger_writes_jsonl_events(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mas.jsonl"
            logger = TraceLogger(path, console=False)
            logger.event(request_id="req_1", step="validator", component="workflow", payload={"passed": True})
            records = logger.read()
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["request_id"], "req_1")
            self.assertEqual(records[0]["step"], "validator")
            json.dumps(records)


if __name__ == "__main__":
    unittest.main()
