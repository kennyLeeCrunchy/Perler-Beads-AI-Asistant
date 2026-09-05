from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "color_standards"
PDF_PATH = DATA_DIR / "mard_291_rgb_hex.pdf"
OUTPUT_SPECS = [
    {
        "page_index": 0,
        "expected_count": 221,
        "csv_path": DATA_DIR / "mard_221_colors_vertical.csv",
        "jsonl_path": DATA_DIR / "mard_221_colors_vertical.jsonl",
    },
    {
        "page_index": 1,
        "expected_count": 70,
        "csv_path": DATA_DIR / "mard_supplement_70_colors_vertical.csv",
        "jsonl_path": DATA_DIR / "mard_supplement_70_colors_vertical.jsonl",
    },
    {
        "page_index": 2,
        "expected_count": 291,
        "csv_path": DATA_DIR / "mard_291_colors_vertical.csv",
        "jsonl_path": DATA_DIR / "mard_291_colors_vertical.jsonl",
    },
]

PAIR_RE = re.compile(r"\b([A-Z]{1,2}\d{1,2})\s+([0-9A-F]{6})\b")
CODE_RE = re.compile(r"^([A-Z]{1,2})(\d{1,2})$")


def parse_rgb(hex_value: str) -> tuple[int, int, int]:
    return (
        int(hex_value[0:2], 16),
        int(hex_value[2:4], 16),
        int(hex_value[4:6], 16),
    )


def extract_page(text: str, expected_count: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    group_order: list[str] = []
    seen_codes: set[str] = set()

    for match in PAIR_RE.finditer(text):
        mard_code, hex_value = match.groups()
        code_match = CODE_RE.match(mard_code)
        if not code_match:
            raise RuntimeError(f"Unexpected MARD code format: {mard_code}")

        group, number_text = code_match.groups()
        if group not in group_order:
            group_order.append(group)

        red, green, blue = parse_rgb(hex_value)
        rows.append(
            {
                "mard_code": mard_code,
                "group": group,
                "number": int(number_text),
                "hex": f"#{hex_value}",
                "r": red,
                "g": green,
                "b": blue,
            }
        )

        if mard_code in seen_codes:
            raise RuntimeError(f"Duplicate MARD code found: {mard_code}")
        seen_codes.add(mard_code)

    if len(rows) != expected_count:
        raise RuntimeError(f"Expected {expected_count} colors, extracted {len(rows)}")

    group_rank = {group: index for index, group in enumerate(group_order)}
    rows.sort(key=lambda row: (group_rank[str(row["group"])], int(row["number"])))
    return rows


def write_outputs(
    rows: list[dict[str, object]], csv_path: Path, jsonl_path: Path
) -> None:
    fieldnames = ["mard_code", "group", "number", "hex", "r", "g", "b"]
    with csv_path.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    with jsonl_path.open("w", encoding="utf-8") as jsonl_file:
        for row in rows:
            jsonl_file.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    reader = PdfReader(str(PDF_PATH))
    if len(reader.pages) < 3:
        raise RuntimeError(f"Expected at least 3 pages, found {len(reader.pages)}")

    for spec in OUTPUT_SPECS:
        text = reader.pages[spec["page_index"]].extract_text() or ""
        rows = extract_page(text, spec["expected_count"])
        write_outputs(rows, spec["csv_path"], spec["jsonl_path"])
        print(f"wrote {len(rows)} rows")
        print(spec["csv_path"])
        print(spec["jsonl_path"])


if __name__ == "__main__":
    main()
