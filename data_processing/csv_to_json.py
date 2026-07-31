"""Convert one CSV file to a UTF-8 JSON array.

Edit INPUT and OUTPUT below, then run:
    python scripts/csv_to_json.py
"""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]

# Change these two paths when converting a different file.
INPUT = "data/raw_data/dataset_facebook-groups-scraper_2026-07-30_08-20-01-507 (2).csv"
OUTPUT = "data/dataset_facebook-groups-scraper_2026-07-30_08-20-01-507 (2).json"


def convert_csv_to_json(input_path: Path, output_path: Path) -> int:
    """Read CSV rows as dictionaries and save them as formatted JSON."""
    with input_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None:
            raise ValueError("CSV không có dòng tiêu đề (header).")
        rows = list(reader)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as json_file:
        json.dump(rows, json_file, ensure_ascii=False, indent=2)
        json_file.write("\n")

    return len(rows)


def main() -> None:
    input_path = ROOT_DIR / INPUT
    output_path = ROOT_DIR / OUTPUT

    if not input_path.is_file():
        raise FileNotFoundError(f"Không tìm thấy file CSV: {input_path}")

    row_count = convert_csv_to_json(input_path, output_path)
    print(f"Created: {output_path}")
    print(f"Rows converted: {row_count}")


if __name__ == "__main__":
    main()
