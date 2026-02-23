def build_generation_payload(
    promotion_context: dict,
    compliance_requirements: dict,
    historical_snippets: list[dict],
    section_name: str,
    section_category: str,
    required_clauses: list[dict] | None = None,
) -> dict:

    # ------------------------------------------------------------------
    # 1️⃣ Pull only rules relevant to this section
    #    + Prevent generic 50-state override if specific states exist
    # ------------------------------------------------------------------
    section_rules = []

    for group in compliance_requirements.values():
        for rule in group:
            if rule["category"] != section_category:
                continue

            if (
                section_category == "eligibility"
                and "50 United States" in rule["rule"]
                and promotion_context.get("states")
            ):
                continue

            section_rules.append(rule["rule"])

    # ------------------------------------------------------------------
    # 2️⃣ Prize Breakdown (Prevents Structure Hallucination)
    # ------------------------------------------------------------------
    prize_lines = []

    for i, p in enumerate(promotion_context.get("prizes", []), start=1):
        if p.get("type") == "cash":
            prize_lines.append(f"Level {i}: Cash - ${p.get('amount')}")
        elif p.get("type") == "giftcard":
            prize_lines.append(f"Level {i}: Gift Card - {p.get('description')}")

    prize_block = "\n".join(prize_lines) if prize_lines else "None"

    # ------------------------------------------------------------------
    # 3️⃣ Structured Promotion Facts Block
    # ------------------------------------------------------------------
    promotion_facts_block = f"""
PROMOTION FACTS (DO NOT INVENT OR OMIT):

Sweepstakes Name: {promotion_context.get("name")}
Eligible States: {", ".join(promotion_context.get("states", []))}
Minimum Age: {promotion_context.get("min_age")}
Start Date/Time: {promotion_context.get("start_time")}
End Date/Time: {promotion_context.get("end_time")}
Winner Selection Time: {promotion_context.get("winner_selection_time")}
Winner Response Deadline: {promotion_context.get("winner_response_deadline")}

Primary Prize Type: {promotion_context.get("primary_prize_type")}
Number of Prize Levels: {len(promotion_context.get("prizes", []))}

Prize Levels (MUST be drafted exactly as listed):
{prize_block}

Total Prize Value: ${promotion_context.get("total_prize_value")}
"""

    # ------------------------------------------------------------------
    # 4️⃣ ENTRY METHOD FACTS BLOCK (NEW - STRUCTURED)
    # ------------------------------------------------------------------
    entry = promotion_context.get("entry_method", {})
    entry_block = ""

    if entry and entry.get("channel"):
        channel = entry.get("channel")

        if channel == "web":
            fields = ", ".join(entry.get("required_fields", []))
            entry_block = f"""
ENTRY METHOD DETAILS (DO NOT INVENT):
Channel: Web Entry
Website URL: {entry.get("url")}
Required Fields: {fields}
"""
        elif channel == "mail":
            entry_block = """
ENTRY METHOD DETAILS (DO NOT INVENT):
Channel: Mail-In Entry
"""
        elif channel == "in_store":
            entry_block = """
ENTRY METHOD DETAILS (DO NOT INVENT):
Channel: In-Store Entry
"""
        elif channel == "social":
            entry_block = """
ENTRY METHOD DETAILS (DO NOT INVENT):
Channel: Social Media Entry
"""

    # ------------------------------------------------------------------
    # 5️⃣ Filter Historical Snippets (Eligibility Fix)
    # ------------------------------------------------------------------
    if section_category == "eligibility" and promotion_context.get("states"):
        filtered_snippets = []
        for s in historical_snippets or []:
            text_lower = (s.get("text") or "").lower()
            if (
                "50 us" in text_lower
                or "50 united states" in text_lower
                or "washington, d.c" in text_lower
                or "and dc" in text_lower
                or "and d.c" in text_lower
            ):
                continue
            filtered_snippets.append(s)
        historical_snippets = filtered_snippets

    # ------------------------------------------------------------------
    # 6️⃣ Historical Snippets Block
    # ------------------------------------------------------------------
    if historical_snippets:
        snippets_block = "\n\n".join(
            f"[Snippet ID: {s.get('id')} | Section: {s.get('section')}]\n{s.get('text')}"
            for s in historical_snippets
        )
    else:
        snippets_block = "None provided."

    # ------------------------------------------------------------------
    # 7️⃣ Compliance Rules Block
    # ------------------------------------------------------------------
    if section_rules:
        rules_block = "\n".join(f"- {r}" for r in section_rules)
    else:
        rules_block = "None specifically applicable beyond general compliance."

    # ------------------------------------------------------------------
    # 8️⃣ Mandatory Clause Block
    # ------------------------------------------------------------------
    if required_clauses:
        clauses_block = "\n".join(
            f"- [{c.get('id')}] {c.get('text')}"
            for c in required_clauses
        )
    else:
        clauses_block = "None"

    # ------------------------------------------------------------------
    # 9️⃣ Base Instruction Prompt
    # ------------------------------------------------------------------
    instruction_prompt = f"""
You are drafting the "{section_name}" section of a U.S. sweepstakes Official Rules document.

INSTRUCTIONS:
- Write ONLY this section.
- Do NOT reference other sections.
- Use formal legal drafting style.
- Follow the tone and structure of real Official Rules.
- Use the Promotion Facts exactly as provided.
- Do NOT invent additional prizes, states, dates, eligibility criteria, or prize structure.
- Do NOT contradict compliance requirements.
- Do NOT reintroduce 50-state eligibility language if specific states are listed.
- If drafting the "How to Enter" section:
  - Use the ENTRY METHOD DETAILS exactly as provided.
  - Do NOT invent additional entry mechanics.
  - If Web entry is listed, clearly state the URL and required fields.

{promotion_facts_block}

{entry_block}

APPLICABLE COMPLIANCE REQUIREMENTS:
{rules_block}

MANDATORY CLAUSES (MUST APPEAR VERBATIM IF LISTED):
{clauses_block}

If any Mandatory Clauses are listed above:
- You MUST include them exactly.
- Do NOT paraphrase them.
- They must appear clearly within this section.

RELEVANT HISTORICAL LANGUAGE (for structure and tone only — do not copy verbatim):
{snippets_block}

Generate the final drafted section below:
"""

    # ------------------------------------------------------------------
    # 🔟 Prize-Specific Enforcement
    # ------------------------------------------------------------------
    if section_category == "prizes":
        instruction_prompt += """

PRIZE DRAFTING REQUIREMENTS (MANDATORY):
- Enumerate each prize level separately.
- Use the exact number of prize levels provided in Promotion Facts.
- State the individual dollar amount for each prize level.
- Clearly calculate and state the total approximate retail value (ARV).
- Do NOT consolidate multiple prize levels into a single prize.
- Do NOT describe the prize as a single item if multiple levels exist.
"""

    return {
        "prompt": instruction_prompt
    }