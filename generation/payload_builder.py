def build_generation_payload(
    promotion_context: dict,
    compliance_requirements: dict,
    historical_snippets: list[dict],
    section_name: str,
    section_category: str,
) -> dict:

    # pull only rules relevant to this section
    section_rules = []
    for group in compliance_requirements.values():
        for rule in group:
            if rule["category"] == section_category:
                section_rules.append(rule["rule"])

    payload = {
        "task": "generate_official_rules_section",
        "section": {
            "name": section_name,
            "category": section_category,
            "purpose": f"Draft the {section_name} section of a sweepstakes Official Rules document."
        },
        "promotion": promotion_context,
        "required_rules": section_rules,
        "historical_snippets": [
            {
                "id": s["id"],
                "section": s.get("section"),
                "text": s["text"]
            }
            for s in historical_snippets
        ],
        "output_requirements": [
            "Write ONLY this section.",
            "Do not reference other sections.",
            "Use formal legal drafting style.",
            "Match the structure and tone of real Official Rules.",
            "If required information is missing, explicitly state it."
        ]
    }

    return payload
