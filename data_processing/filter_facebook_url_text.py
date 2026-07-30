"""Keep a post URL and every field whose name contains ``text``.

Edit INPUT and OUTPUT below, then run:
    python scripts/filter_facebook_url_text.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]

# Change these two paths when filtering a different file.
INPUT = "data/dataset_facebook-groups-scraper_2026-07-30_08-20-01-507 (2).json"
OUTPUT = "data/facebook_url_text.json"


def clean_text(value: Any) -> str | None:
    """Normalize whitespace and discard empty text values."""
    if not isinstance(value, str):
        return None
    cleaned = " ".join(value.split())
    return cleaned or None


def extract_text_fields(value: Any, path: str = "") -> dict[str, Any]:
    """Extract every non-empty field whose name contains ``text``."""
    extracted: dict[str, Any] = {}

    if isinstance(value, dict):
        for key, child_value in value.items():
            child_path = f"{path}/{key}" if path else key
            if "text" in key.lower():
                if isinstance(child_value, str):
                    cleaned = clean_text(child_value)
                    if cleaned is not None:
                        extracted[child_path] = cleaned
                elif child_value is not None:
                    extracted[child_path] = child_value

            if isinstance(child_value, (dict, list)):
                extracted.update(extract_text_fields(child_value, child_path))

    elif isinstance(value, list):
        for index, child_value in enumerate(value):
            child_path = f"{path}/{index}" if path else str(index)
            extracted.update(extract_text_fields(child_value, child_path))

    return extracted


def filter_records(records: list[Any]) -> list[dict[str, Any]]:
    """Keep a post URL and its matching text fields."""
    return [
        {"url": record.get("url"), **extract_text_fields(record)}
        for record in records
        if isinstance(record, dict)
    ]


def main() -> None:
    input_path = ROOT_DIR / INPUT
    output_path = ROOT_DIR / OUTPUT
    if not input_path.is_file():
        raise FileNotFoundError(f"Không tìm thấy file input: {input_path}")

    with input_path.open("r", encoding="utf-8") as input_file:
        records = json.load(input_file)
    if not isinstance(records, list):
        raise ValueError("File input phải là một JSON array.")

    filtered_records = filter_records(records)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as output_file:
        json.dump(filtered_records, output_file, ensure_ascii=False, indent=2)
        output_file.write("\n")

    print(f"Created: {output_path}")
    print(f"Posts retained: {len(filtered_records)}")


if __name__ == "__main__":
    main()
