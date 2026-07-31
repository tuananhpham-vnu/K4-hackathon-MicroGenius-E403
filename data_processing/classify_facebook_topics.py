"""Split filtered Facebook posts into admissions, student support, and other topics.

Run from the project root:
    python scripts/classify_facebook_topics.py
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]

# INPUT is the source JSON file. OUTPUT is the folder for topic JSON files.
INPUT = "data/facebook_text_fields.json"
OUTPUT = "data"

# A post that explicitly concerns post-acceptance support (for example,
# enrolment, orientation, or deferment) is labelled student_support first.
# This avoids mislabelling an enrolled learner as an admissions enquiry.
POST_ACCEPTANCE_PATTERNS = [
    r"nhap hoc|khai giang|lich hoc|phong hoc|lop hoc|diem danh",
    r"the hoc vien|dong phuc|bao luu|nghi hoc",
    r"onboard|onboarding|canvas|codelab|github|lab\b|bai tap|workshop|kiem tra giua ky",
    r"team|nhom|teammate|mentor|coach|giang vien",
    r"thuc tap|phase [123]|thu vien|can ?tin|cong truong|phong tu hoc",
    r"hoc o|buoi hoc|di hoc|xin phep nghi",
]

ADMISSIONS_PATTERNS = [
    r"\btuyen sinh\b",
    r"\bphong tuyen sinh\b",
    r"\b(vong|dot)\s+(xet tuyen|ho so|cv|thi)\b",
    r"\bpass\s*cv\b",
    r"\b(nop|gui)\s*cv\b",
    r"\b(danh gia nang luc|dgnl)\b",
    r"\bthi dau vao\b",
    r"\bket qua\b.{0,35}\b(ho so|cv|thi|dgnl)\b",
    r"\b(ho so|cv)\b.{0,35}\b(khoa|k[3-9]|tuyen)\b",
    r"\b(mo|dong)\s+(don|form)\b",
    r"\bnhan ho so\b",
    r"\bchi tieu\b",
    r"\b(ky|dot) tuyen\b",
    r"\b(dang ky|dki|dky)\s+(thi|du thi)\b",
    r"\b(thi|xet) lai\b",
    r"\b(dieu kien|kien thuc nen)\b.{0,50}\b(tham gia|dang ky|apply)\b",
    r"\bapply\b.{0,50}\bchuong trinh\b",
    r"\b(de thi|bai thi)\b.{0,50}\b(dgnl|dau vao)\b",
    r"\b(khoa|k)\s*[3-9]\b.{0,35}\b(mo don|dong don|mo form|dong form|nhan ho so|tuyen sinh|thi|ket qua)\b",
    r"\b(khoa|k)\s*[3-9]\b.{0,20}\bbao gio\b.{0,20}\b(mo|tuyen|thi)\b",
    r"\b(rot|truot)\b.{0,15}\b(vong|ho so|cv|dgnl)\b",
]

STUDENT_SUPPORT_PATTERNS = [
    r"nhap hoc|khai giang|lich hoc|phong hoc|lop hoc|diem danh",
    r"tai khoan|dang nhap|email|mail",
    r"the hoc vien|dong phuc|bao luu|nghi hoc",
    r"onboard|onboarding|canvas|codelab|github|lab\b|bai tap|workshop|kiem tra giua ky",
    r"team|nhom|teammate|mentor|coach|giang vien",
    r"thuc tap|phase [123]|thu vien|can ?tin|cong truong|phong tu hoc",
    r"hoc vien|hoc o|buoi hoc|di hoc|xin phep nghi",
    r"lien he.*btc|lien he.*admin",
]


def normalize(text: str) -> str:
    """Make Vietnamese keyword matching accent- and case-insensitive."""
    decomposed = unicodedata.normalize("NFD", text)
    without_accents = "".join(char for char in decomposed if unicodedata.category(char) != "Mn")
    return without_accents.lower().replace("đ", "d")


def matches_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def classify_post(post: dict[str, Any]) -> str:
    main_text = post.get("text")
    normalized_text = normalize(main_text) if isinstance(main_text, str) else ""

    if matches_any(normalized_text, POST_ACCEPTANCE_PATTERNS):
        return "student_support"
    if matches_any(normalized_text, ADMISSIONS_PATTERNS):
        return "admissions"
    if matches_any(normalized_text, STUDENT_SUPPORT_PATTERNS):
        return "student_support"
    return "other"


def write_json(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as output_file:
        json.dump(records, output_file, ensure_ascii=False, indent=2)
        output_file.write("\n")


def main() -> None:
    input_path = ROOT_DIR / INPUT
    output_dir = ROOT_DIR / OUTPUT
    output_files = {
        "admissions": output_dir / "facebook_admissions.json",
        "student_support": output_dir / "facebook_student_support.json",
        "other": output_dir / "facebook_other_topics.json",
    }

    if not input_path.is_file():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with input_path.open("r", encoding="utf-8") as input_file:
        posts = json.load(input_file)
    if not isinstance(posts, list):
        raise ValueError("Input file must be a JSON array.")

    groups: dict[str, list[dict[str, Any]]] = {name: [] for name in output_files}
    for post in posts:
        if isinstance(post, dict):
            groups[classify_post(post)].append(post)

    for name, output_path in output_files.items():
        write_json(output_path, groups[name])
        print(f"{name}: {len(groups[name])} -> {output_path}")


if __name__ == "__main__":
    main()
