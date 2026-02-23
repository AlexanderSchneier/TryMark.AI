from document import create_document
from knowledge.retrieval import retrieve_relevant_chunks_for_section
from generation.payload_builder import build_generation_payload
from generation.generate import generate_text
from docx import Document
from io import BytesIO
import json
from dotenv import load_dotenv
load_dotenv()

from main import SECTIONS


def generate_official_rules(form_data: dict):

    # Build document using provided data instead of CLI prompts
    doc = create_document(from_api_data=form_data)  # You’ll modify this
    doc.load_hard_constraints("hard_constraints.json")
    doc.apply_hard_constraints()
    doc.validate()

    promotion_context = {
        "name": doc._name,
        "states": doc._residence,
        "min_age": doc._minAge,
        "start_time": doc._startTime,
        "end_time": doc._endTime,
        "winner_selection_time": doc._winnerTime,
        "winner_response_deadline": doc._winnerResponseTime,
        "prizes": [
            {"type": p.prize_type.value, "amount": p.amount}
            for p in doc._prizeLevels.values()
        ],
        "total_prize_value": doc._total_prize_value(),
        "entry_method": "unspecified",
        "in_store_entry": doc._inPersonEntry
    }

    compliance_requirements = doc._constraint_output

    generated_sections = {}

    for section in SECTIONS:

        relevant_snippets = retrieve_relevant_chunks_for_section(
            compliance_requirements,
            section_category=section["category"],
            section_title=section["title"],
            top_k=6,
            always_include_baseline=True,
            min_score=15
        )

        payload = build_generation_payload(
            promotion_context,
            compliance_requirements,
            relevant_snippets,
            section_name=section["title"],
            section_category=section["category"]
        )

        section_text = generate_text(payload)
        generated_sections[section["id"]] = section_text

    # Build docx in memory
    document = Document()
    document.add_heading("OFFICIAL SWEEPSTAKES RULES", level=1)

    for section in SECTIONS:
        document.add_heading(section["title"], level=2)
        content = generated_sections.get(section["id"], "")

        for line in content.split("\n"):
            document.add_paragraph(line)

    buffer = BytesIO()
    document.save(buffer)
    buffer.seek(0)

    return buffer