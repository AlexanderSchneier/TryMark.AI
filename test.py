from knowledge.retrieval import retrieve_relevant_chunks

# Simulate the constraint output you just verified
constraint_output = {
    "foundational": [
        {
            "rule": "Winners must be selected at random.",
            "category": "sweepstakes_classification"
        }
    ],
    "triggered": [],
    "conditional": [],
    "evaluated_not_triggered": [
        {
            "rule": "Winners receiving prizes valued over $600 require enhanced identity verification.",
            "category": "winner_clearance"
        }
    ]
}

chunks = retrieve_relevant_chunks(constraint_output)

print(f"\nRetrieved {len(chunks)} chunks:\n")

for c in chunks:
    print(
        f"- section={c.get('section')} | "
        f"doc_type={c.get('doc_type')} | "
        f"channel={c.get('channel')}"
    )
