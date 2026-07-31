from typing import Any, Iterable
from xml.etree import ElementTree as ET

from ..domain.models import Evidence


class XmlPrompt:
    """Builds and parses the shared XML envelope passed between agents."""

    @staticmethod
    def parse(xml: str) -> dict[str, Any]:
        root = ET.fromstring(xml)
        if root.tag != "request":
            raise ValueError("XML root must be <request>")

        def value(path: str, default: str = "") -> str:
            node = root.find(path)
            return (node.text or "").strip() if node is not None else default

        def fields(path: str) -> dict[str, str]:
            output: dict[str, str] = {}
            for child in root.findall(f"{path}/*"):
                # New envelopes use a fixed valid tag and keep arbitrary keys
                # in an attribute. Accept legacy tag-as-key envelopes too.
                key = child.get("key") if child.tag == "field" else child.tag
                if key:
                    output[key] = (child.text or "").strip()
            return output

        return {
            "request_id": value("request_id"), "agent": value("agent", "orchestrator"), "query": value("query"),
            "context": fields("./context"),
            "history": [{"id": node.get("id", ""), "role": node.get("role", ""), "text": (node.text or "").strip()} for node in root.findall("./history/turn")],
            "candidate_profile": fields("./candidate_profile"),
            "retrieved_evidence": [{"id": node.get("id", ""), "source_id": node.get("source_id", "")} for node in root.findall("./retrieved_evidence/item")],
        }

    @staticmethod
    def build(request_id: str, query: str, context: dict[str, Any] | None = None,
              history: list[dict[str, str]] | None = None, profile: dict[str, Any] | None = None,
              evidence: Iterable[Evidence] = ()) -> str:
        root = ET.Element("request")
        ET.SubElement(root, "request_id").text = request_id
        ET.SubElement(root, "agent").text = "orchestrator"
        ET.SubElement(root, "query").text = query
        context_node = ET.SubElement(root, "context")
        for key, value in (context or {}).items():
            ET.SubElement(context_node, "field", key=str(key)).text = str(value)
        history_node = ET.SubElement(root, "history")
        for item in history or []:
            node = ET.SubElement(history_node, "turn", id=str(item.get("id", "")), role=str(item.get("role", "")))
            node.text = str(item.get("text", ""))
        profile_node = ET.SubElement(root, "candidate_profile")
        for key, value in (profile or {}).items():
            ET.SubElement(profile_node, "field", key=str(key)).text = str(value)
        evidence_node = ET.SubElement(root, "retrieved_evidence")
        for item in evidence:
            ET.SubElement(evidence_node, "item", id=item.evidence_id, source_id=item.source_id)
        return ET.tostring(root, encoding="unicode")
