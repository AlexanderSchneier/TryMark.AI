import os
import json
import uuid
import re
from docx import Document

# =========================
# CONFIG
# =========================

RAW_DOCS_DIR = "./raw_documents"
OUTPUT_FILE = "knowledge_base.json"

SECTION_HEADERS = [
    "Eligibility",
    "How to Enter",
    "Prize",
    "Prize(s)",
    "Winner Notification",
    "Privacy",
    "Release",
    "General Conditions",
    "Arbitration",
    "Disputes",
    "Sweepstakes Period",
    "Official Time"
]

DISCLOSURE_CHANNELS = [
    "POINT OF SALE",
    "PRINT",
    "WEB",
    "EMAIL",
    "FACEBOOK",
    "INSTAGRAM",
    "TIKTOK",
    "TWITTER",
    "X (FORMERLY TWITTER)",
    "X"
]

# =========================
# TEXT EXTRACTION
# =========================

def extract_docx_text(path):
    doc = Document(path)
    return "\n".join(
        p.text.strip()
        for p in doc.paragraphs
        if p.text and p.text.strip()
    )

# =========================
# SECTION SPLITTER (RULES)
# =========================

def split_into_sections(text):
    sections = {}
    current = "Intro"
    sections[current] = []

    for line in text.splitlines():
        for header in SECTION_HEADERS:
            if re.match(rf"^{re.escape(header)}\b", line, re.I):
                current = header
                sections[current] = []
                break
        sections[current].append(line)

    return {
        k: "\n".join(v).strip()
        for k, v in sections.items()
        if "\n".join(v).strip()
    }

# =========================
# CHANNEL SPLITTER (DISCLOSURES)
# =========================

def split_by_channel(text):
    chunks = {}
    current = None

    for line in text.splitlines():
        normalized = line.strip().upper()

        if normalized in DISCLOSURE_CHANNELS:
            current = normalized.lower()
            chunks[current] = []
        elif current:
            chunks[current].append(line)

    return {
        k: "\n".join(v).strip()
        for k, v in chunks.items()
        if "\n".join(v).strip()
    }

# =========================
# CLASSIFICATION
# =========================

def classify_section(section):
    mapping = {
        "Eligibility": (True, ["eligibility", "age", "residency"]),
        "How to Enter": (True, ["entry", "no_purchase"]),
        "Prize": (True, ["prize", "erv"]),
        "Prize(s)": (True, ["prize", "erv"]),
        "Winner Notification": (True, ["winner", "notification"]),
        "Privacy": (True, ["privacy"]),
        "Arbitration": (True, ["arbitration", "disputes"]),
        "Disputes": (True, ["disputes"]),
    }
    return mapping.get(section, (False, []))

# =========================
# MAIN PIPELINE
# =========================

def process_docx(path):
    filename = os.path.basename(path)
    filename_lower = filename.lower()
    text = extract_docx_text(path)
    entries = []

    # 🔑 Stronger disclosure detection
    is_disclosure_file = (
        "abbreviate" in filename_lower
        or "disclosure" in filename_lower
        or any(ch in text.upper() for ch in DISCLOSURE_CHANNELS)
    )

    if is_disclosure_file:
        chunks = split_by_channel(text)

        for channel, chunk in chunks.items():
            entries.append({
                "id": f"{filename}_{channel}_{uuid.uuid4().hex[:6]}",
                "doc_type": "abbreviated_disclosure",
                "section": None,
                "channel": channel,
                "hard_constraint": False,
                "text": chunk,
                "tags": ["abbreviated", "disclosure"]
            })

    else:
        sections = split_into_sections(text)

        for section, chunk in sections.items():
            hard, tags = classify_section(section)
            entries.append({
                "id": f"{filename}_{section}_{uuid.uuid4().hex[:6]}",
                "doc_type": "official_rules",
                "section": section,
                "channel": None,
                "hard_constraint": hard,
                "text": chunk,
                "tags": tags
            })

    return entries

def main():
    all_entries = []

    for file in os.listdir(RAW_DOCS_DIR):
        if file.lower().endswith(".docx"):
            path = os.path.join(RAW_DOCS_DIR, file)
            print(f"Processing: {file}")
            all_entries.extend(process_docx(path))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_entries, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Knowledge base built: {OUTPUT_FILE}")
    print(f"📦 Total chunks: {len(all_entries)}")

if __name__ == "__main__":
    main()