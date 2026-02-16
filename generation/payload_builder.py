def build_generation_payload(
    promotion_context: dict,
    compliance_requirements: dict,
    historical_snippets: list[dict],
    section_name: str,
    section_category: str,
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

            # Prevent broad federal 50-state language from overriding
            # specific state-restricted promotions
            if (
                section_category == "eligibility"
                and "50 United States" in rule["rule"]
                and promotion_context.get("states")
            ):
                continue

            section_rules.append(rule["rule"])


    # ------------------------------------------------------------------
    # 2️⃣ Structured Promotion Facts Block
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
Total Prize Value: ${promotion_context.get("total_prize_value")}
"""


    # ------------------------------------------------------------------
    # 3️⃣ Historical Snippets Block
    # ------------------------------------------------------------------
    if historical_snippets:
        snippets_block = "\n\n".join(
            f"[Snippet ID: {s.get('id')} | Section: {s.get('section')}]\n{s.get('text')}"
            for s in historical_snippets
        )
    else:
        snippets_block = "None provided."


    # ------------------------------------------------------------------
    # 4️⃣ Compliance Rules Block
    # ------------------------------------------------------------------
    if section_rules:
        rules_block = "\n".join(f"- {r}" for r in section_rules)
    else:
        rules_block = "None specifically applicable beyond general compliance."


    # ------------------------------------------------------------------
    # 5️⃣ Base Instruction Prompt
    # ------------------------------------------------------------------
    instruction_prompt = f"""
You are drafting the "{section_name}" section of a U.S. sweepstakes Official Rules document.

INSTRUCTIONS:
- Write ONLY this section.
- Do NOT reference other sections.
- Use formal legal drafting style.
- Follow the tone and structure of real Official Rules.
- Use the Promotion Facts exactly as provided.
- Do NOT say information is missing if it appears in the Promotion Facts.
- Do NOT invent additional prizes, states, dates, or eligibility criteria.

{promotion_facts_block}

APPLICABLE COMPLIANCE REQUIREMENTS:
{rules_block}

RELEVANT HISTORICAL LANGUAGE (for structure and tone only — do not copy verbatim):
{snippets_block}

Generate the final drafted section below:
"""


    # ------------------------------------------------------------------
    # 6️⃣ Prize-Specific Enforcement
    # ------------------------------------------------------------------
    if section_category == "prizes":
        instruction_prompt += """

PRIZE DRAFTING REQUIREMENTS (MANDATORY):
- Enumerate each prize level separately.
- Use the exact number of prize levels provided in Promotion Facts.
- State the individual dollar amount for each prize level.
- Clearly calculate and state the total approximate retail value (ARV).
- Do NOT consolidate multiple prize levels into a single prize.
"""


    return {
        "prompt": instruction_prompt
    }
