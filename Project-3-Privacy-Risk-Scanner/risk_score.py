"""
risk_score.py
-------------
Aggregates raw findings.json into a risk register: groups by PII/PHI type,
computes a risk score (likelihood x sensitivity), and maps each finding
type to the relevant NZ Privacy Act 2020 Information Privacy Principle (IPP)
and ISO/IEC 27799 (health informatics security) control area.

This is the step that turns "we found some data" into something a privacy/
risk team can actually act on and prioritise.
"""

import json
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "output"

# Maps each PII/PHI type to the most relevant compliance reference.
# References are simplified for demo purposes - not legal advice.
COMPLIANCE_MAP = {
    "NAME": {
        "ipp": "IPP 8 - Accuracy",
        "iso27799": "7.2 - Access control to personal health information",
        "control": "Access restriction + audit logging on name fields",
    },
    "NHI_NUMBER": {
        "ipp": "IPP 5 & 11 - Storage security / Limits on disclosure",
        "iso27799": "7.4 - Unique patient identification controls",
        "control": "Tokenise or encrypt at rest; restrict export capability",
    },
    "HEALTH_CONDITION": {
        "ipp": "IPP 11 - Limits on disclosure (health info is highly sensitive)",
        "iso27799": "6.1 - Health information security policy",
        "control": "Field-level encryption; role-based access only",
    },
    "CLINICAL_TEXT": {
        "ipp": "IPP 11 - Limits on disclosure",
        "iso27799": "8.1 - Handling of unstructured clinical records",
        "control": "Free-text redaction/DLP scanning before export",
    },
    "ADDRESS": {
        "ipp": "IPP 11 - Limits on disclosure",
        "iso27799": "7.3 - Physical/contact data minimisation",
        "control": "Minimise retention; mask in non-production environments",
    },
    "EMAIL": {
        "ipp": "IPP 11 - Limits on disclosure",
        "iso27799": "7.2 - Access control",
        "control": "Mask in logs; restrict third-party sharing",
    },
    "PHONE_NZ": {
        "ipp": "IPP 11 - Limits on disclosure",
        "iso27799": "7.2 - Access control",
        "control": "Mask in logs; restrict third-party sharing",
    },
    "POLICY_NUMBER": {
        "ipp": "IPP 5 & 11 - Storage security / Limits on disclosure",
        "iso27799": "7.4 - Unique identifier traceability",
        "control": "Mask in logs; treat as sensitive when paired with health/condition data",
    },
    "INSURANCE_INFO": {
        "ipp": "IPP 11 - Limits on disclosure",
        "iso27799": "7.3 - Financial/health data minimisation",
        "control": "Restrict to billing team access only; audit log access",
    },
    "DOB": {
        "ipp": "IPP 11 - Limits on disclosure",
        "iso27799": "7.3 - Data minimisation",
        "control": "Store age-band instead of full DOB where possible",
    },
}


def likelihood_score(count, total_files):
    """Simple likelihood proxy: how widespread a finding type is across files scanned."""
    if count > 100:
        return 5
    if count > 40:
        return 4
    if count > 15:
        return 3
    if count > 5:
        return 2
    return 1


def build_register():
    with open(OUTPUT_DIR / "findings.json") as f:
        findings = json.load(f)

    files_seen = {f["file"] for f in findings}
    by_type = {}
    for finding in findings:
        t = finding["type"]
        by_type.setdefault(t, {"count": 0, "sensitivity": finding["sensitivity"], "files": set()})
        by_type[t]["count"] += 1
        by_type[t]["files"].add(finding["file"])

    register = []
    for ptype, info in by_type.items():
        likelihood = likelihood_score(info["count"], len(files_seen))
        risk_score = likelihood * info["sensitivity"]
        compliance = COMPLIANCE_MAP.get(ptype, {})
        register.append({
            "type": ptype,
            "instances_found": info["count"],
            "files_affected": sorted(info["files"]),
            "sensitivity": info["sensitivity"],
            "likelihood": likelihood,
            "risk_score": risk_score,
            "risk_level": _risk_level(risk_score),
            "ipp_reference": compliance.get("ipp", "N/A"),
            "iso27799_reference": compliance.get("iso27799", "N/A"),
            "recommended_control": compliance.get("control", "Review manually"),
        })

    register.sort(key=lambda r: r["risk_score"], reverse=True)

    out_path = OUTPUT_DIR / "risk_register.json"
    with open(out_path, "w") as f:
        json.dump(register, f, indent=2)

    print(f"Risk register built: {len(register)} PII/PHI categories ranked -> {out_path}")
    return register


def _risk_level(score):
    if score >= 20:
        return "CRITICAL"
    if score >= 12:
        return "HIGH"
    if score >= 6:
        return "MEDIUM"
    return "LOW"


if __name__ == "__main__":
    build_register()
