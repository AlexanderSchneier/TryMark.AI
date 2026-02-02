#RAG
import json
from pathlib import Path

KB_PATH = Path("knowledge_base.json")

# Map constraint categories to KB sections
CATEGORY_TO_SECTIONS = {
    "sweepstakes_classification": ["Intro", "General Conditions"],
    "entry_method": ["How to Enter"],
    "eligibility": ["Eligibility"],
    "winner_clearance": ["Winner Notification"],
    "prizes": ["Prize", "Prize(s)"],
    "bonding_registration": ["Eligibility", "Prize"]
}

def load_knowledge_base() -> list[dict]:
    if not KB_PATH.exists():
        raise FileNotFoundError("knowledge_base.json not found")
    with open(KB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)



def retrieve_relevant_chunks(constraint_output: dict) -> list[dict]:
    kb = load_knowledge_base()
    results = []
    seen_texts = set()

    for bucket in ("foundational", "triggered"):
        for rule in constraint_output.get(bucket, []):
            category = rule.get("category")
            if not category:
                continue

            valid_sections = CATEGORY_TO_SECTIONS.get(category, [])

            for chunk in kb:
                if chunk.get("section") not in valid_sections:
                    continue

                normalized = chunk["text"].strip().lower()
                if normalized in seen_texts:
                    continue

                seen_texts.add(normalized)
                results.append(chunk)

    return results



##NEED TO FIX THIS FILE ITS MESSED UP AND RETRIVING INCORRECT DATA