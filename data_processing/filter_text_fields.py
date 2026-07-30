"""Keep the post URL and every JSON field whose name contains ``text``.

Edit INPUT and OUTPUT below, then run:
    python scripts/filter_text_fields.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]

# Change these two paths when filtering a different file.
INPUT = "data/dataset_facebook-groups-scraper_2026-07-30_08-20-01-507 (2).json"
OUTPUT = "data/facebook_text_fields.json"


def clean_text(value: Any) -> str | None:
    """Normalize whitespace and discard empty text values."""
    if not isinstance(value, str):
        return None
    cleaned = " ".join(value.split())
    return cleaned or None


def extract_text_fields(value: Any, path: str = "") -> dict[str, Any]:
    """Extract every nested field whose name contains ``text``."""
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


def filter_file(input_path: Path, output_path: Path) -> tuple[int, int]:
    with input_path.open("r", encoding="utf-8") as input_file:
        records = json.load(input_file)
    if not isinstance(records, list):
        raise ValueError("File input phải là một JSON array.")

    filtered_records = [
        {"url": record.get("url"), **extract_text_fields(record)}
        for record in records
        if isinstance(record, dict)
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as output_file:
        json.dump(filtered_records, output_file, ensure_ascii=False, indent=2)
        output_file.write("\n")

    text_value_count = sum(len(record) - 1 for record in filtered_records)
    return len(filtered_records), text_value_count


def main() -> None:
    input_path = ROOT_DIR / INPUT
    output_path = ROOT_DIR / OUTPUT
    if not input_path.is_file():
        raise FileNotFoundError(f"Không tìm thấy file input: {input_path}")

    record_count, text_value_count = filter_file(input_path, output_path)
    print(f"Created: {output_path}")
    print(f"Posts: {record_count}; text fields kept: {text_value_count}")


if __name__ == "__main__":
    main()
