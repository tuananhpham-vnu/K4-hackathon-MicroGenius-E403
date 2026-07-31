import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from server import parse_query_payload


class ServerPayloadTests(unittest.TestCase):
    def test_valid_payload_is_normalized(self):
        payload = parse_query_payload(b'{"query":"  hello  ","context":{},"history":[]}')
        self.assertEqual(payload["query"], "hello")

    def test_payload_must_be_an_object(self):
        with self.assertRaisesRegex(ValueError, "JSON object"):
            parse_query_payload(b'["not", "an", "object"]')

    def test_nested_fields_have_expected_types(self):
        with self.assertRaisesRegex(ValueError, "history must be"):
            parse_query_payload(b'{"query":"hello","history":{}}')

    def test_query_has_a_size_limit(self):
        raw = ('{"query":"' + "x" * 4001 + '"}').encode()
        with self.assertRaisesRegex(ValueError, "4000"):
            parse_query_payload(raw)


if __name__ == "__main__":
    unittest.main()
