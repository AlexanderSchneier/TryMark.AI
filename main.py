from document import create_document
from knowledge.retrieval import retrieve_relevant_chunks
from generation.payload_builder import build_generation_payload
import json


def main():
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

    return  # STOP HERE



if __name__ == "__main__":
    main()
