def build_generation_payload(
    promotion_context: dict,
    compliance_requirements: dict,
    historical_snippets: list[dict],
    task: str,
    section: str | None = None
) -> dict:
    payload = {
        "task": task,
        "promotion": promotion_context,
        "compliance_requirements": compliance_requirements,
        "historical_snippets": [
            {
                "id": s["id"],
                "doc_type": s["doc_type"],
                "section": s.get("section"),
                "channel": s.get("channel"),
                "text": s["text"]
            }
            for s in historical_snippets
        ]
    }

    if section:
        payload["section"] = section

    return payload
