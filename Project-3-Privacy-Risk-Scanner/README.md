# Privacy Risk & PII Exposure Scanner

A standalone tool that scans a dataset for PII/PHI (personal and health information), scores the findings by risk, and produces a prioritised risk register mapped to **NZ Privacy Act 2020** principles and **ISO/IEC 27799** (health informatics security).

Built as a self-directed project to explore how technical detection work (regex/pattern matching, data classification) connects to real privacy risk assurance practice — the kind of translation between "we found data" and "here's what to do about it" that privacy and risk teams do daily.

> **All data used is synthetic.** `generate_data.py` creates fake patient records with the [Faker](https://faker.readthedocs.io/) library. No real individual's data is used anywhere in this project.

## Why this project

My other cloud security work (a graph-based analysis of privilege escalation paths in AWS IAM) focuses on *who can reach what* — access control from the infrastructure side. That work kept raising a question it didn't answer: once someone (or some system) has access to a dataset, what's actually sitting inside it, and how much does it matter if it gets exposed?

This project explores that other half of the problem: not access control, but data classification and risk prioritisation. Most PII-detection tools stop at "found an email address." This one goes a step further — it groups findings by category, weighs them by **likelihood × sensitivity**, and maps each category to the specific privacy principle or health-information security control it implicates. Health data was a natural test case, since it's one of the most heavily regulated personal-data categories under NZ law, which made it a useful stress test for the idea.

## Pipeline

```
generate_data.py   → synthetic patient/appointment/clinical data (data/)
      ↓
scanner.py         → detects PII/PHI via regex + column heuristics (output/findings.json)
      ↓
risk_score.py      → aggregates + scores by likelihood x sensitivity (output/risk_register.json)
      ↓
report.py          → renders an HTML risk dashboard (output/risk_dashboard.html)
```

## Detected data types

| Type | Detection method | Sensitivity |
|---|---|---|
| Name | Column heuristic | 4 |
| NHI-style number | Regex | 5 |
| Health condition | Column heuristic | 5 |
| Clinical free text | Column heuristic | 5 |
| Address | Column heuristic | 3 |
| Email | Regex | 3 |
| NZ phone number | Regex | 3 |
| Insurance policy number | Regex | 4 |
| Insurance provider | Column heuristic | 3 |
| Date of birth | Regex | 4 |

## Risk scoring

`risk_score = likelihood (1-5) × sensitivity (1-5)`

| Score | Level |
|---|---|
| ≥ 20 | Critical |
| ≥ 12 | High |
| ≥ 6 | Medium |
| < 6 | Low |

Each finding type is also mapped to:
- The most relevant **Information Privacy Principle (IPP)** under NZ's Privacy Act 2020
- The relevant **ISO/IEC 27799** control area (health informatics security)
- A **recommended control** (e.g. tokenisation, field-level encryption, masking)

## Running it

```bash
pip install faker
python generate_data.py   # creates synthetic dataset
python scanner.py         # detects PII/PHI
python risk_score.py      # builds the risk register
python report.py          # renders output/risk_dashboard.html
```

Open `output/risk_dashboard.html` in a browser to view the risk register.

## Design decisions & limitations

- **Regex + column heuristics over full NER**: keeps the tool dependency-light and fast, at the cost of missing PII embedded in unpredictable free text. A production tool would layer in NER (spaCy) or a managed service (AWS Macie) for unstructured content.
- **Likelihood is a proxy** (frequency of occurrence across scanned files), not a true probabilistic exposure model. A real deployment would factor in access controls, encryption status, and network exposure.
- **NHI-style numbers are format-only** — they don't use the real NZ NHI check-digit algorithm, deliberately, since this is a public demo project.
- **Risk scoring convention, not an ISO 31000 formula**: ISO 31000 describes a general risk management *process* (identify → analyse → evaluate → treat → monitor) but doesn't mandate a specific formula. Likelihood × consequence is a widely used convention *within* that process (often visualised as a risk matrix), which is what this project's scoring is loosely based on.
- **Privacy Act 2020, as amended**: the Act now includes IPP 3A (added by the Privacy Amendment Act 2025, in force from 1 May 2026), bringing the total to 14 IPPs rather than the original 13. This project's compliance mapping currently references IPPs 5, 8, and 11, which are unaffected by that change.
- **Not legal advice** — the IPP/ISO mappings are simplified for illustration and would need review by a qualified privacy professional before use in a real risk register.

## Possible extensions

- Swap regex layer for spaCy NER to catch PII in unstructured free text
- Add a cross-border transfer check (flag if data would leave NZ/approved jurisdictions)
- Track findings over time to show risk trend, not just a point-in-time snapshot
