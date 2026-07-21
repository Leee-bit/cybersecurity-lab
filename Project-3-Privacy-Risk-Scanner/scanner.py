"""
scanner.py
----------
Scans structured (CSV) and unstructured (TXT) files for PII/PHI patterns.

Design note: uses regex + column-name heuristics rather than a full NER model,
so it runs anywhere with zero heavyweight dependencies. This mirrors how a
first-pass DLP (data loss prevention) triage tool works in practice - catch
the high-confidence patterns fast, flag the rest for human review.

Output: findings.json - a list of every match with file, location, and type.
"""

import csv
import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# --- Pattern library -------------------------------------------------------
# Each entry: (label, compiled regex, sensitivity 1-5)
PATTERNS = {
    "EMAIL": (re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"), 3),
    "PHONE_NZ": (re.compile(r"(\+?64|0)[\s-]?[2-9]\d{1,2}[\s-]?\d{3,4}[\s-]?\d{3,4}"), 3),
    "NHI_NUMBER": (re.compile(r"\b[A-Z]{3}\d{4}\b"), 5),
    "POLICY_NUMBER": (re.compile(r"\bPOL-\d{8}\b"), 4),
    "DOB": (re.compile(r"\b\d{4}-\d{2}-\d{2}\b"), 4),
}

# Column names that indicate PHI even without pattern-matching the value
SENSITIVE_COLUMN_NAMES = {
    "full_name": ("NAME", 4),
    "nhi_number": ("NHI_NUMBER", 5),
    "condition": ("HEALTH_CONDITION", 5),
    "clinician_notes": ("CLINICAL_TEXT", 5),
    "address": ("ADDRESS", 3),
    "insurance_provider": ("INSURANCE_INFO", 3),
    "policy_number": ("POLICY_NUMBER", 4),
}


def scan_text_blob(text, source_file, location):
    findings = []
    for label, (pattern, sensitivity) in PATTERNS.items():
        for match in pattern.finditer(text):
            findings.append({
                "file": source_file,
                "location": location,
                "type": label,
                "sensitivity": sensitivity,
                "sample": _redact(match.group()),
            })
    return findings


def _redact(value):
    """Show enough to verify a match without dumping full PII into the report."""
    if len(value) <= 4:
        return "*" * len(value)
    return value[:2] + "*" * (len(value) - 4) + value[-2:]


def scan_csv(path):
    findings = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2):  # header is row 1
            for col, value in row.items():
                if not value:
                    continue
                location = f"row {row_num}, column '{col}'"
                # Column-name heuristic (catches names/conditions regex won't)
                if col in SENSITIVE_COLUMN_NAMES:
                    label, sensitivity = SENSITIVE_COLUMN_NAMES[col]
                    findings.append({
                        "file": path.name,
                        "location": location,
                        "type": label,
                        "sensitivity": sensitivity,
                        "sample": _redact(value),
                    })
                # Pattern match (catches emails/phones/NHI regardless of column)
                findings.extend(scan_text_blob(value, path.name, location))
    return findings


def scan_txt(path):
    with open(path) as f:
        text = f.read()
    return scan_text_blob(text, path.name, "free text")


def main():
    all_findings = []
    for csv_file in DATA_DIR.glob("*.csv"):
        all_findings.extend(scan_csv(csv_file))
    for txt_file in DATA_DIR.glob("*.txt"):
        all_findings.extend(scan_txt(txt_file))

    out_path = OUTPUT_DIR / "findings.json"
    with open(out_path, "w") as f:
        json.dump(all_findings, f, indent=2, default=str)

    print(f"Scanned {len(list(DATA_DIR.glob('*')))} files, found {len(all_findings)} PII/PHI instances.")
    print(f"Findings written -> {out_path}")


if __name__ == "__main__":
    main()
