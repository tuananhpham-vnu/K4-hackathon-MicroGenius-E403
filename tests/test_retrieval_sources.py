import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from admissions_mas.retrieval.knowledge_base import KnowledgeBase, regex_chunks


class RetrievalSourceTests(unittest.TestCase):
    def test_regex_chunks_splits_paragraphs(self):
        text = "Admission requirements are described in official documents. Tuition support is also described in official documents."
        chunks = regex_chunks(text, min_chars=20)
        self.assertGreaterEqual(len(chunks), 1)

    def test_local_retrieval_keeps_source_metadata_on_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "Tailieutubtc"
            corpus.mkdir()
            (corpus / "admissions.md").write_text(
                "Điều kiện tuyển sinh yêu cầu ứng viên có nền tảng lập trình và tư duy toán học.",
                encoding="utf-8",
            )
            kb = KnowledgeBase(root)
            results = kb.search("điều kiện tuyển sinh lập trình", limit=1)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].source_title, "admissions")
            self.assertTrue(results[0].source_uri.endswith("admissions.md"))


if __name__ == "__main__":
    unittest.main()
