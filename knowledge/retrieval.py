import json
import re
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

KB_PATH = Path("knowledge_base.json")

# Category → keyword hints
CATEGORY_KEYWORDS = {
    "sweepstakes_classification": ["intro", "general", "overview", "conditions", "agreement", "official rules"],
    "entry_method": ["entry", "enter", "amoe", "how to", "no purchase", "alternate method"],
    "eligibility": ["eligibility", "eligible", "residents", "age", "void", "employees"],
    "winner_clearance": ["winner", "notification", "affidavit", "verification", "tax", "w-9", "1099"],
    "prizes": ["prize", "award", "value", "odds", "arv", "approximate retail value"],
    "bonding_registration": ["bond", "bonding", "registration", "register", "rhode island", "new york", "florida"],
}

# OPTIONAL: section-title hints (helps retrieval even if KB section names vary)
SECTION_TITLE_KEYWORDS = {
    "Agreement to Official Rules": ["agreement", "official rules", "bound", "by participating"],
    "Eligibility": ["eligibility", "eligible", "residents", "age", "void", "employees"],
    "How to Enter": ["how to enter", "entry", "enter", "amoe", "no purchase", "mail-in"],
    "Prize(s)": ["prize", "prizes", "arv", "approximate retail value", "odds", "value"],
    "Requirements of Potential Winners": ["affidavit", "verification", "w-9", "1099", "winner", "release"],
    "General Conditions": ["general conditions", "limitation", "liability", "disclaimer", "force majeure", "cancel"],
}


def load_knowledge_base() -> List[Dict[str, Any]]:
    if not KB_PATH.exists():
        raise FileNotFoundError("knowledge_base.json not found")
    with open(KB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize(text: Optional[str]) -> str:
    return re.sub(r"[^\w\s]", " ", (text or "").lower()).strip()


def stable_id(chunk: Dict[str, Any]) -> str:
    key = f"{chunk.get('doc_type')}||{chunk.get('section')}||{chunk.get('channel')}||{chunk.get('text')}"
    return hashlib.sha256(key.encode()).hexdigest()


def _score_chunk(
    chunk: Dict[str, Any],
    category: str,
    section_title: str,
    category_keywords: List[str],
    title_keywords: List[str],
) -> int:
    """
    Simple lexical scoring (cheap + deterministic).
    You can swap this out later for embeddings.
    """
    text = normalize(chunk.get("text"))
    section = normalize(chunk.get("section"))
    doc_type = normalize(chunk.get("doc_type"))

    score = 0

    # Hard constraints get a big boost (but not infinite)
    if chunk.get("hard_constraint"):
        score += 80

    # If chunk section strongly aligns with the current section title/category
    # (This is your "section-aware" part)
    # Example: section="Eligibility" and section_title="Eligibility"
    if normalize(section_title) and normalize(section_title) in section:
        score += 60
    if normalize(category.replace("_", " ")) in section:
        score += 35

    # Title keyword match (very strong for section targeting)
    for kw in title_keywords:
        nkw = normalize(kw)
        if nkw and nkw in section:
            score += 35
        if nkw and nkw in text:
            score += 20

    # Category keyword match
    for kw in category_keywords:
        nkw = normalize(kw)
        if nkw and nkw in section:
            score += 25
        if nkw and nkw in text:
            score += 12

    # Slight preference for official_rules doc type if present
    if "official_rules" in doc_type or "official rules" in doc_type:
        score += 8

    return score


def retrieve_relevant_chunks_for_section(
    constraint_output: Dict[str, Any],
    section_category: str,
    section_title: str,
    top_k: int = 6,
    always_include_baseline: bool = True,
    min_score: int = 15,
) -> List[Dict[str, Any]]:
    """
    Section-aware retrieval:
      - Uses triggered + foundational rules for relevance
      - BUT also can pull baseline boilerplate for that section even if no rule triggered
      - Returns multiple chunks (top_k), not 1-per-category
    """
    kb = load_knowledge_base()

    # active rules (you can later include conditional too if you want)
    active_rules = (
        constraint_output.get("foundational", [])
        + constraint_output.get("triggered", [])
    )

    # Determine which categories are "active" for this generation call
    active_categories = {r.get("category") for r in active_rules if r.get("category")}
    category_is_active = section_category in active_categories

    category_keywords = CATEGORY_KEYWORDS.get(section_category, [])
    title_keywords = SECTION_TITLE_KEYWORDS.get(section_title, [])

    scored: List[Tuple[int, Dict[str, Any]]] = []
    seen = set()

    for chunk in kb:
        cid = stable_id(chunk)
        if cid in seen:
            continue

        # If we're doing baseline retrieval, we allow section-matched chunks even if not active.
        # If not baseline mode, we require the category to be active.
        if (not always_include_baseline) and (not category_is_active):
            continue

        score = _score_chunk(
            chunk=chunk,
            category=section_category,
            section_title=section_title,
            category_keywords=category_keywords,
            title_keywords=title_keywords,
        )

        # If the category isn't active, require strong section match to include baseline boilerplate
        if not category_is_active and always_include_baseline:
            # baseline threshold higher (prevents random pull)
            if score < (min_score + 20):
                continue
        else:
            if score < min_score:
                continue

        seen.add(cid)

        out = dict(chunk)
        out["_category"] = section_category
        out["_score"] = score

        # Fill missing section label for readability
        if not out.get("section"):
            out["section"] = section_title

        scored.append((score, out))

    # Sort best-first
    scored.sort(key=lambda t: t[0], reverse=True)

    # Return top_k
    return [c for _, c in scored[:top_k]]
