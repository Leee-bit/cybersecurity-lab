"""
generate_data.py
-----------------
Generates 100% synthetic healthcare-adjacent data for privacy risk scanning demos.

IMPORTANT: All data below is fake, generated with the Faker library.
No real patient, customer, or employee data is used anywhere in this project.

Outputs (into ./data/):
  - patients.csv           : synthetic patient records (structured PII/PHI + insurance/billing)
  - appointment_logs.csv   : synthetic appointment booking/reminder call logs with embedded operator notes
  - clinical_notes.txt     : synthetic free-text clinical notes (unstructured PHI)
"""

import csv
import random
from pathlib import Path
from faker import Faker

fake = Faker("en_NZ")
Faker.seed(42)
random.seed(42)

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

CONDITIONS = [
    "sleep apnea", "COPD", "type 2 diabetes", "post-surgical recovery",
    "chronic respiratory failure", "hypertension", "asthma",
]

INSURANCE_PROVIDERS = ["Southern Cross", "NIB", "AIA Health", "Accuro", "Unimed"]

CLINICS = ["East Tamaki Respiratory Clinic", "Auckland Sleep Centre", "Northshore Community Health"]


def fake_nhi():
    """Fake NZ National Health Index-style identifier (format only, not a real algorithm)."""
    letters = "".join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ", k=3))
    digits = "".join(random.choices("0123456789", k=4))
    return f"{letters}{digits}"


def fake_policy_number():
    return f"POL-{''.join(random.choices('0123456789', k=8))}"


def generate_patients(n=150):
    path = DATA_DIR / "patients.csv"
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "patient_id", "full_name", "nhi_number", "dob", "email", "phone",
            "address", "condition", "insurance_provider", "policy_number", "clinician_notes",
        ])
        for i in range(1, n + 1):
            writer.writerow([
                f"P{i:04d}",
                fake.name(),
                fake_nhi(),
                fake.date_of_birth(minimum_age=18, maximum_age=90),
                fake.email(),
                fake.phone_number(),
                fake.address().replace("\n", ", "),
                random.choice(CONDITIONS),
                random.choice(INSURANCE_PROVIDERS),
                fake_policy_number(),
                f"Patient reports improved symptoms since starting therapy for {random.choice(CONDITIONS)}.",
            ])
    print(f"Wrote {n} synthetic patient records -> {path}")


def generate_appointment_logs(n=300):
    path = DATA_DIR / "appointment_logs.csv"
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["log_id", "clinic", "appointment_time", "operator_note"])
        for i in range(1, n + 1):
            note = random.choice([
                "Routine reminder call, no issues.",
                f"Contacted patient {fake.name()} to confirm appointment time.",
                f"Reschedule requested - patient email {fake.email()} used for confirmation.",
                "Appointment confirmed via SMS.",
                f"Patient phone {fake.phone_number()} on file, left voicemail reminder.",
                f"Insurance pre-approval needed, policy {fake_policy_number()} on file.",
            ])
            writer.writerow([
                f"L{i:05d}",
                random.choice(CLINICS),
                fake.date_time_this_year(),
                note,
            ])
    print(f"Wrote {n} synthetic appointment log entries -> {path}")


def generate_clinical_notes(n=40):
    path = DATA_DIR / "clinical_notes.txt"
    with open(path, "w") as f:
        for i in range(n):
            name = fake.name()
            nhi = fake_nhi()
            condition = random.choice(CONDITIONS)
            f.write(
                f"Note #{i+1}: Patient {name} (NHI {nhi}) presented with {condition}. "
                f"Contact on file: {fake.email()} / {fake.phone_number()}. "
                f"Recommend follow-up in 4 weeks.\n\n"
            )
    print(f"Wrote {n} synthetic clinical notes -> {path}")


if __name__ == "__main__":
    generate_patients()
    generate_appointment_logs()
    generate_clinical_notes()
    print("\nDone. All data above is synthetic (Faker-generated) - no real individuals.")
