from dotenv import load_dotenv
load_dotenv()

from document import create_document
from knowledge.retrieval import retrieve_relevant_chunks
from generation.payload_builder import build_generation_payload
from generation.generate import generate_text
import json



# Canonical Official Rules structure
SECTIONS = [
    {
        "id": "classification",
        "title": "Agreement to Official Rules",
        "category": "sweepstakes_classification"
    },
    {
        "id": "eligibility",
        "title": "Eligibility",
        "category": "eligibility"
    },
    {
        "id": "entry_method",
        "title": "How to Enter",
        "category": "entry_method"
    },
    {
        "id": "prizes",
        "title": "Prize(s)",
        "category": "prizes"
    },
    {
        "id": "winner_clearance",
        "title": "Requirements of Potential Winners",
        "category": "winner_clearance"
    },
    {
        "id": "general_conditions",
        "title": "General Conditions",
        "category": "bonding_registration"
    }
]


def main():
    # 1️⃣ Collect promotion facts
    doc = create_document()
    doc.load_hard_constraints("hard_constraints.json")
    doc.apply_hard_constraints()
    doc.validate()

    promotion_context = {
        "name": doc._name,
        "states": doc._residence,
        "min_age": doc._minAge,
        "prizes": [
            {"type": p.prize_type.value, "amount": p.amount}
            for p in doc._prizeLevels.values()
        ],
        "total_prize_value": doc._total_prize_value(),
        "entry_method": "unspecified",
        "in_store_entry": False
    }

    compliance_requirements = doc._constraint_output

    print("\n=== CONSTRAINT OUTPUT ===\n")
    print(json.dumps(compliance_requirements, indent=2))

    # 2️⃣ Retrieve KB chunks ONCE
    snippets = retrieve_relevant_chunks(compliance_requirements)

    print("\n=== RETRIEVED KB CHUNKS ===\n")
    for c in snippets:
        print(
            c.get("_category"),
            "|",
            c.get("section"),
            "| score:",
            c.get("_score")
        )

    # 3️⃣ Generate document section-by-section
    print("\n=== GENERATING DOCUMENT SECTIONS ===\n")

    generated_sections = {}

    for section in SECTIONS:
        category = section["category"]

        relevant_snippets = [
            s for s in snippets
            if s.get("_category") == category
        ]

        payload = build_generation_payload(
            promotion_context,
            compliance_requirements,
            relevant_snippets,
            section_name=section["title"],
            section_category=category
        )

        print(f"→ Generating section: {section['title']}")

        section_text = generate_text(payload)
        generated_sections[section["id"]] = section_text

    # 4️⃣ Assemble final document deterministically
    print("\n\n=== FINAL GENERATED DOCUMENT ===\n")

    for section in SECTIONS:
        print(section["title"].upper())
        print("-" * len(section["title"]))
        print(generated_sections.get(section["id"], ""))
        print("\n")


if __name__ == "__main__":
    main()
