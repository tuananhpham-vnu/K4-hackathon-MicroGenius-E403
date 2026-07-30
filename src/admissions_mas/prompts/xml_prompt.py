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

        profile_node = root.find("./candidate_profile")
        return {
            "request_id": value("request_id"), "agent": value("agent", "orchestrator"), "query": value("query"),
            "context": {child.tag: (child.text or "").strip() for child in root.findall("./context/*")},
            "history": [{"id": node.get("id", ""), "role": node.get("role", ""), "text": (node.text or "").strip()} for node in root.findall("./history/turn")],
            "candidate_profile": {child.tag: (child.text or "").strip() for child in profile_node} if profile_node is not None else {},
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
            ET.SubElement(context_node, str(key)).text = str(value)
        history_node = ET.SubElement(root, "history")
        for item in history or []:
            node = ET.SubElement(history_node, "turn", id=str(item.get("id", "")), role=str(item.get("role", "")))
            node.text = str(item.get("text", ""))
        profile_node = ET.SubElement(root, "candidate_profile")
        for key, value in (profile or {}).items():
            ET.SubElement(profile_node, str(key)).text = str(value)
        evidence_node = ET.SubElement(root, "retrieved_evidence")
        for item in evidence:
            ET.SubElement(evidence_node, "item", id=item.evidence_id, source_id=item.source_id)
        return ET.tostring(root, encoding="unicode")
