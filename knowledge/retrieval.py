import json
import re
import hashlib
from pathlib import Path
from typing import Dict, List, Any

KB_PATH = Path("knowledge_base.json")

# Category → keyword hints (NOT exact section names anymore)
CATEGORY_KEYWORDS = {
    "sweepstakes_classification": ["intro", "general", "overview", "conditions"],
    "entry_method": ["entry", "enter", "amoe", "how to"],
    "eligibility": ["eligibility", "eligible", "residents", "age"],
    "winner_clearance": ["winner", "notification", "affidavit", "verification", "tax"],
    "prizes": ["prize", "award", "value", "odds"],
    "bonding_registration": ["bond", "bonding", "registration", "register", "rhode island", "new york"],
}

def load_knowledge_base() -> List[Dict[str, Any]]:
    if not KB_PATH.exists():
        raise FileNotFoundError("knowledge_base.json not found")
    with open(KB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def normalize(text: str) -> str:
    return re.sub(r"[^\w\s]", "", (text or "").lower()).strip()

def stable_id(chunk: Dict[str, Any]) -> str:
    key = f"{chunk.get('doc_type')}||{chunk.get('section')}||{chunk.get('text')}"
    return hashlib.sha256(key.encode()).hexdigest()

def retrieve_relevant_chunks(constraint_output: Dict[str, Any]) -> List[Dict[str, Any]]:
    kb = load_knowledge_base()
    results = []
    seen = set()

    # Only pull from constraints that actually matter
    active_rules = (
        constraint_output.get("foundational", [])
        + constraint_output.get("triggered", [])
    )

    for rule in active_rules:
        category = rule.get("category")
        if not category:
            continue

        keywords = CATEGORY_KEYWORDS.get(category, [])

        for chunk in kb:
            text = normalize(chunk.get("text"))
            section = normalize(chunk.get("section"))
            score = 0

            # Strong signal: hard constraints always win
            if chunk.get("hard_constraint"):
                score += 50

            # Section keyword match
            for kw in keywords:
                if kw in section:
                    score += 25
                if kw in text:
                    score += 10

            if score < 10:
                continue

            cid = stable_id(chunk)
            if cid in seen:
                continue
            seen.add(cid)

            out = dict(chunk)
            out["_category"] = category
            out["_score"] = score

            # 👇 ADD THIS
            if not chunk.get("section"):
                out["section"] = category.replace("_", " ").title()

            results.append(out)

    # Sort: hard constraints first, then score
    # Sort: hard constraints first, then score
    results.sort(
        key=lambda c: (c.get("hard_constraint") is not True, -(c["_score"]))
    )

    # 👇 COLLAPSE TO ONE CHUNK PER CATEGORY
    collapsed = {}
    for c in results:
        cat = c["_category"]
        if cat not in collapsed:
            collapsed[cat] = c

    return list(collapsed.values())


