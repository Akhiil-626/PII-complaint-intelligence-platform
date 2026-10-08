"""Helpers for generating synthetic PII evaluation examples and expanding test datasets."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Dict, List


NAMES = ["Aarav Patel", "Meera Joshi", "David Miller", "Jennifer Garcia", "Ananya Sen", "Michael Chang"]
EMAILS = ["aarav.patel@example.com", "meera.j@gmail.com", "david.m99@workmail.org", "jennifer.garcia@outlook.com"]
PHONES = ["+91 9823456789", "+1 555-234-5678", "9123456780", "+91 8877665544"]
ACCOUNTS = ["ACC-98127341", "AC12093847", "ACC10023456", "ACC-77441122"]
AADHAARS = ["4521 8901 2345", "9812 3456 7890", "2345 6789 0123"]
COMPLAINT_IDS = ["CMP-2026-99120", "CASE-44129", "TICKET-77112"]
CREDIT_CARDS = ["4111 2222 3333 4444", "4532-1100-2299-4455", "5424 1800 2200 9988"]
PASSWORDS = ["secretP@ss99", "hunter2", "Welcome2026!"]
USERNAMES = ["aarav_p99", "meera_user", "d_miller"]

TEMPLATES = [
    (
        "My name is {name} and I am writing regarding an unauthorized charge on my credit card {card}. "
        "The account number is {account} and my reference ticket is {complaint_id}. "
        "Please reach out to me at {email} or {phone}.",
        ["PERSON", "CREDIT_CARD", "ACCOUNT_NUMBER", "COMPLAINT_ID", "EMAIL_ADDRESS", "PHONE_NUMBER"]
    ),
    (
        "Dear Support, my name is {name}. Someone took a fraudulent loan using my Aadhaar number {aadhaar}. "
        "My username is {username} and password is {password}. Complaint ID is {complaint_id}. "
        "Contact me at {phone} or {email}.",
        ["PERSON", "AADHAAR_NUMBER", "CREDENTIAL", "CREDENTIAL", "COMPLAINT_ID", "PHONE_NUMBER", "EMAIL_ADDRESS"]
    ),
    (
        "I need immediate help with account {account}. My name is {name} and credit card is {card}. "
        "Ticket is {complaint_id}. Email me at {email}.",
        ["ACCOUNT_NUMBER", "PERSON", "CREDIT_CARD", "COMPLAINT_ID", "EMAIL_ADDRESS"]
    )
]


def generate_synthetic_examples(count: int = 10, random_seed: int = 42) -> List[Dict[str, Any]]:
    """Create synthetic complaint texts with inserted ground-truth PII entity spans.
    
    Args:
        count: Number of synthetic complaints to generate.
        random_seed: Random seed for deterministic generation.
        
    Returns:
        List of dicts matching synth_data.json schema.
    """
    random.seed(random_seed)
    records = []

    for i in range(count):
        tmpl, entity_order = random.choice(TEMPLATES)
        name = random.choice(NAMES)
        email = random.choice(EMAILS)
        phone = random.choice(PHONES)
        account = random.choice(ACCOUNTS)
        aadhaar = random.choice(AADHAARS)
        cid = f"CMP-2026-{10000 + i}"
        card = random.choice(CREDIT_CARDS)
        uname = random.choice(USERNAMES)
        pwd = random.choice(PASSWORDS)

        vals = {
            "name": name,
            "email": email,
            "phone": phone,
            "account": account,
            "aadhaar": aadhaar,
            "complaint_id": cid,
            "card": card,
            "username": uname,
            "password": pwd,
        }

        text = tmpl.format(**vals)
        entities = []

        if "{name}" in tmpl:
            entities.append({"type": "PERSON", "text": name})
        if "{email}" in tmpl:
            entities.append({"type": "EMAIL_ADDRESS", "text": email})
        if "{phone}" in tmpl:
            entities.append({"type": "PHONE_NUMBER", "text": phone})
        if "{account}" in tmpl:
            entities.append({"type": "ACCOUNT_NUMBER", "text": account})
        if "{aadhaar}" in tmpl:
            entities.append({"type": "AADHAAR_NUMBER", "text": aadhaar})
        if "{complaint_id}" in tmpl:
            entities.append({"type": "COMPLAINT_ID", "text": cid})
        if "{card}" in tmpl:
            entities.append({"type": "CREDIT_CARD", "text": card})
        if "{username}" in tmpl:
            entities.append({"type": "CREDENTIAL", "text": f"username is {uname}"})
        if "{password}" in tmpl:
            entities.append({"type": "CREDENTIAL", "text": f"password is {pwd}"})

        records.append({
            "id": f"synth_{i+1:04d}",
            "complaint_text": text,
            "entities": entities,
        })

    return records


def expand_eval_dataset(source_path: str, output_path: str, additional_count: int = 10) -> None:
    """Expand an existing ground-truth evaluation set with new synthetic examples."""
    src = Path(source_path)
    out = Path(output_path)

    existing = []
    if src.exists():
        with open(src, "r", encoding="utf-8") as f:
            existing = json.load(f)

    new_examples = generate_synthetic_examples(count=additional_count)
    combined = existing + new_examples

    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2)
