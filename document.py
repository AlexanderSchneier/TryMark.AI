from enum import Enum
from typing import Literal, Dict
import json


STATE_NAME_TO_CODE = {
    "ALABAMA": "AL",
    "ALASKA": "AK",
    "ARIZONA": "AZ",
    "ARKANSAS": "AR",
    "CALIFORNIA": "CA",
    "COLORADO": "CO",
    "CONNECTICUT": "CT",
    "DELAWARE": "DE",
    "FLORIDA": "FL",
    "GEORGIA": "GA",
    "HAWAII": "HI",
    "IDAHO": "ID",
    "ILLINOIS": "IL",
    "INDIANA": "IN",
    "IOWA": "IA",
    "KANSAS": "KS",
    "KENTUCKY": "KY",
    "LOUISIANA": "LA",
    "MAINE": "ME",
    "MARYLAND": "MD",
    "MASSACHUSETTS": "MA",
    "MICHIGAN": "MI",
    "MINNESOTA": "MN",
    "MISSISSIPPI": "MS",
    "MISSOURI": "MO",
    "MONTANA": "MT",
    "NEBRASKA": "NE",
    "NEVADA": "NV",
    "NEW HAMPSHIRE": "NH",
    "NEW JERSEY": "NJ",
    "NEW MEXICO": "NM",
    "NEW YORK": "NY",
    "NORTH CAROLINA": "NC",
    "NORTH DAKOTA": "ND",
    "OHIO": "OH",
    "OKLAHOMA": "OK",
    "OREGON": "OR",
    "PENNSYLVANIA": "PA",
    "RHODE ISLAND": "RI",
    "SOUTH CAROLINA": "SC",
    "SOUTH DAKOTA": "SD",
    "TENNESSEE": "TN",
    "TEXAS": "TX",
    "UTAH": "UT",
    "VERMONT": "VT",
    "VIRGINIA": "VA",
    "WASHINGTON": "WA",
    "WEST VIRGINIA": "WV",
    "WISCONSIN": "WI",
    "WYOMING": "WY",
    "DISTRICT OF COLUMBIA": "DC",
    "WASHINGTON DC": "DC",
    "WASHINGTON D.C.": "DC",
    "D.C.": "DC"
}


class PrizeType(Enum):
    CASH = "cash"
    GIFTCARD = "giftcard"


class Prize:
    def __init__(self, prize_type: PrizeType, amount: float | None = None, description: str | None = None):
        self.prize_type = prize_type
        self.amount = amount
        self.description = description


class Document:
    def __init__(self):
        self._name: str | None = None 
        self._doorCount: int| None =  None
        self._doorLocation: str| None = None
        self._prizes:PrizeType | None = None
        self._language = "English"
        self._inPersonEntry = False #Do participants need to visit the store in person
        self._inPersonAnnouncement = False #Do Participants need to be at store for winner announcment
        self._timeZone = "Eastern Time"
        self._minAge: Literal[18,21] = 18
        self._residence: list[str] | None = None
        self._startTime: str
        self._endTime: str
        self._winnerTime: str
        self._winnerResponseTime: str
        self._prizeLevels: Dict[int, Prize] = {}
        self._hard_constraints = []
        self._entryChannel: str | None = None
        self._entryUrl: str | None = None
        self._entryFields: list[str] = []

    def _safe_filename(self) -> str:
        return self._name.strip().replace(" ", "_") + ".txt"

    def write_compliance_report(self) -> None:
        filename = self._safe_filename()

        with open(filename, "w") as f:
            f.write("SWEEPSTAKES COMPLIANCE REPORT\n")
            f.write("=" * 32 + "\n\n")

            f.write("DOCUMENT INFORMATION\n")
            f.write("-" * 22 + "\n")
            f.write(f"Sweepstakes Name: {self._name}\n")
            f.write(f"Door Count: {self._doorCount}\n")
            f.write(f"Door Location: {self._doorLocation}\n")
            f.write(f"Primary Prize Type: {self._prizes.value}\n")
            f.write(f"Minimum Age: {self._minAge}\n")
            f.write(f"Eligible States: {', '.join(self._residence or [])}\n")
            f.write(f"Start Time: {self._startTime}\n")
            f.write(f"End Time: {self._endTime}\n")
            f.write(f"Winner Selection Time: {self._winnerTime}\n")
            f.write(f"Winner Response Deadline: {self._winnerResponseTime}\n\n")

            f.write("PRIZE LEVELS\n")
            f.write("-" * 12 + "\n")
            for level, prize in self._prizeLevels.items():
                if prize.prize_type.name == "CASH":
                    f.write(f"Level {level}: Cash - ${prize.amount}\n")
                else:
                    f.write(f"Level {level}: Gift Card - {prize.description}\n")
            f.write("\n")


            f.write("COMPLIANCE REQUIREMENTS SUMMARY\n")
            f.write("-" * 32 + "\n\n")

            sections = self._constraint_output

            # ---- Foundational ----
            f.write("FOUNDATIONAL LEGAL REQUIREMENTS\n")
            f.write("-" * 32 + "\n")
            for c in sections["foundational"]:
                f.write(f"- {c['rule']}\n")
            f.write("\n")

            # ---- Triggered ----
            f.write("REQUIREMENTS TRIGGERED BY THIS PROMOTION\n")
            f.write("-" * 40 + "\n")
            for c in sections["triggered"]:
                f.write(f"- {c['rule']} ({c['reason']})\n")
            f.write("\n")

            # ---- Conditional ----
            f.write("CONDITIONAL / RISK-BASED REQUIREMENTS\n")
            f.write("-" * 40 + "\n")
            for c in sections["conditional"]:
                f.write(f"- {c['rule']} ({c['reason']})\n")
            f.write("\n")

            # ---- Evaluated but Not Triggered ----
            if sections["evaluated_not_triggered"]:
                f.write("RULES EVALUATED BUT NOT TRIGGERED\n")
                f.write("-" * 36 + "\n")
                for c in sections["evaluated_not_triggered"]:
                    f.write(f"- {c['rule']} ({c['reason']})\n")
                f.write("\n")

            print(f"\n📄 Compliance report written to: {filename}")





    def _total_prize_value(self) -> float:
        total = 0.0
        for prize in self._prizeLevels.values():
            if prize.prize_type == PrizeType.CASH and prize.amount:
                total += prize.amount
        return total
    def _max_prize_value(self) -> float:
        vals = []
        for prize in self._prizeLevels.values():
            if prize.prize_type == PrizeType.CASH and prize.amount:
                vals.append(float(prize.amount))
            # Gift cards can be handled later when you add a value field
        return max(vals) if vals else 0.0


    def _any_prize_exceeds(self, threshold: float) -> bool:
        for prize in self._prizeLevels.values():
            if prize.prize_type == PrizeType.CASH and prize.amount and float(prize.amount) > threshold:
                return True
        return False

    def load_hard_constraints(self, path: str) -> None:
        with open(path, "r") as f:
            data = json.load(f)
        self._hard_constraints = data["constraints"]

    def validate(self) -> None:
        if not self._name:
            raise ValueError("Name is required")

        if self._doorCount is None or self._doorCount <= 0:
            raise ValueError("Door count must be a positive integer")

        if not self._doorLocation:
            raise ValueError("Door location is required")

        if self._prizes is None:
            raise ValueError("Primary prize type is required")

        if self._residence is None or len(self._residence) == 0:
            raise ValueError("At least one residence/state is required")

        # --- Time fields ---
        if not self._startTime:
            raise ValueError("Start time is required")

        if not self._endTime:
            raise ValueError("End time is required")

        if not self._winnerTime:
            raise ValueError("Winner selection time is required")

        if not self._winnerResponseTime:
            raise ValueError("Winner response time is required")

        # --- Age ---
        if self._minAge not in (18, 21):
            raise ValueError("Minimum age must be 18 or 21")

        # --- Prize levels ---
        if not self._prizeLevels:
            raise ValueError("Prize levels must be defined")

        for level, prize in self._prizeLevels.items():
            if not isinstance(level, int) or level <= 0:
                raise ValueError(f"Invalid prize level: {level}")

            if not isinstance(prize, Prize):
                raise ValueError(f"Prize at level {level} must be a Prize object")

            if prize.prize_type is None:
                raise ValueError(f"Prize type missing at level {level}")

            # Cash prizes must have a valid amount
            if prize.prize_type == PrizeType.CASH:
                if prize.amount is None or prize.amount <= 0:
                    raise ValueError(f"Cash prize at level {level} must have a positive amount")
    
    
    def apply_hard_constraints(self) -> None:
        foundational = []
        triggered = []
        conditional = []
        evaluated_not_triggered = []
        warnings = []

        # ---- Normalize states ----
        normalized_states = set()

        for state in self._residence or []:
            s = state.strip().upper()

            if len(s) == 2:
                normalized_states.add(s)
            elif s in STATE_NAME_TO_CODE:
                normalized_states.add(STATE_NAME_TO_CODE[s])
                warnings.append(f"State '{state}' normalized to '{STATE_NAME_TO_CODE[s]}'")
            else:
                warnings.append(
                    f"Unrecognized state '{state}'. State-specific constraints may not apply."
                )

        state_codes = {f"US-{s}" for s in normalized_states}
        total_prize_value = self._total_prize_value()

        for constraint in self._hard_constraints:
            jurisdictions = set(constraint.get("jurisdictions", []))
            thresholds = constraint.get("thresholds", {})
            cid = constraint.get("id")
            rule = constraint["rule"]
            category = constraint.get("category")


            # ---- Foundational rules (always true federal rules, no thresholds) ----
            if "US-FEDERAL" in jurisdictions and not thresholds:
                foundational.append({
                    "id": cid,
                    "rule": rule,
                    "category": category,
                    "reason": "Applies to all U.S. sweepstakes"
                })
                continue

            # ---- Threshold-based checks ----
            threshold_failed = False
            reasons = []

            if "total_prize_value_usd" in thresholds:
                if total_prize_value > thresholds["total_prize_value_usd"]:
                    reasons.append(
                        f"Total prize value (${total_prize_value}) exceeds "
                        f"${thresholds['total_prize_value_usd']}"
                    )
                else:
                    threshold_failed = True

            if "prize_value_usd" in thresholds:
                if self._any_prize_exceeds(thresholds["prize_value_usd"]):
                    reasons.append(
                        f"At least one prize exceeds ${thresholds['prize_value_usd']}"
                    )
                else:
                    threshold_failed = True
            # ---- Jurisdiction match ----
            jurisdiction_match = (
                "US-FEDERAL" in jurisdictions
                or jurisdictions.intersection(state_codes)
            )

            # ---- Categorize ----
            if jurisdiction_match and not threshold_failed:
                triggered.append({
                    "id": cid,
                    "rule": rule,
                    "category": category,
                    "reason": "; ".join(reasons) if reasons else "Promotion configuration triggered this rule"
                })
            elif jurisdiction_match:
                evaluated_not_triggered.append({
                    "id": cid,
                    "rule": rule,
                    "category": category,
                    "reason": "Jurisdiction applicable, but thresholds not met"
                })
            else:
                conditional.append({
                    "id": cid,
                    "rule": rule,
                    "category": category,
                    "reason": "Applies only if certain actions or configurations are used"
                })

        self._constraint_output = {
            "foundational": foundational,
            "triggered": triggered,
            "conditional": conditional,
            "evaluated_not_triggered": evaluated_not_triggered
        }

        self._constraint_warnings = warnings


def create_document(from_api_data: dict | None = None) -> Document:
    doc = Document()

    # -------------------------------
    # API MODE
    # -------------------------------
    if from_api_data:

        doc._name = from_api_data["name"]
        doc._doorCount = from_api_data.get("door_count", 1)
        doc._doorLocation = from_api_data.get("door_location", "")

        primary_prize = from_api_data.get("primary_prize_type", "cash").lower()
        if primary_prize == "cash":
            doc._prizes = PrizeType.CASH
        elif primary_prize == "giftcard":
            doc._prizes = PrizeType.GIFTCARD
        else:
            raise ValueError("Invalid prize type")

        doc._minAge = from_api_data["min_age"]
        if doc._minAge not in (18, 21):
            raise ValueError("Minimum age must be 18 or 21")

        doc._residence = from_api_data["states"]

        doc._startTime = from_api_data["start_time"]
        doc._endTime = from_api_data["end_time"]
        doc._winnerTime = from_api_data["winner_selection_time"]
        doc._winnerResponseTime = from_api_data["winner_response_deadline"]

        # 🔥 ENTRY METHOD (NEW)
        entry_data = from_api_data.get("entry_method", {})
        doc._entryChannel = entry_data.get("channel")
        doc._entryUrl = entry_data.get("url")
        doc._entryFields = entry_data.get("required_fields", [])

        for idx, prize_data in enumerate(from_api_data["prizes"], start=1):

            if prize_data["type"] == "cash":
                prize = Prize(
                    PrizeType.CASH,
                    amount=prize_data["amount"]
                )

            elif prize_data["type"] == "giftcard":
                prize = Prize(
                    PrizeType.GIFTCARD,
                    description=prize_data.get("description", "")
                )

            else:
                raise ValueError("Invalid prize type")

            doc._prizeLevels[idx] = prize

        return doc

    # -------------------------------
    # CLI MODE
    # -------------------------------

    doc._name = input("Sweepstakes name: ").strip()
    doc._doorCount = int(input("How many physical locations are offering this promotion? ").strip())
    doc._doorLocation = input("Where are the locations? ").strip()

    prize_type_input = input("Primary prize type (cash/giftcard): ").strip().lower()
    if prize_type_input == "cash":
        doc._prizes = PrizeType.CASH
    elif prize_type_input == "giftcard":
        doc._prizes = PrizeType.GIFTCARD
    else:
        raise ValueError("Invalid prize type")

    age_input = int(input("Minimum age (18 or 21): ").strip())
    if age_input not in (18, 21):
        raise ValueError("Minimum age must be 18 or 21")
    doc._minAge = age_input

    states = input("Eligible states (comma-separated): ").strip()
    doc._residence = [s.strip() for s in states.split(",") if s.strip()]

    doc._startTime = input("Start time: ").strip()
    doc._endTime = input("End time: ").strip()
    doc._winnerTime = input("Winner selection time: ").strip()
    doc._winnerResponseTime = input("Winner response deadline: ").strip()

    # 🔥 ENTRY METHOD (NEW CLI INPUT)
    print("\n--- Entry Method ---")
    doc._entryChannel = input("Entry channel (web/mail/in_store/social): ").strip().lower()

    if doc._entryChannel == "web":
        doc._entryUrl = input("Website URL: ").strip()
        fields = input("Required fields (comma separated, e.g. name,email,phone): ").strip()
        doc._entryFields = [f.strip() for f in fields.split(",") if f.strip()]

    num_levels = int(input("How many prize levels are there? ").strip())
    if num_levels <= 0:
        raise ValueError("Number of prize levels must be positive")

    for i in range(1, num_levels + 1):
        print(f"\n--- Prize Level {i} ---")
        level = int(input("Level number: ").strip())

        ptype = input("Prize type (cash/giftcard): ").strip().lower()
        if ptype == "cash":
            amount = float(input("Cash amount: ").strip())
            prize = Prize(PrizeType.CASH, amount=amount)
        elif ptype == "giftcard":
            description = input("Gift card description: ").strip()
            prize = Prize(PrizeType.GIFTCARD, description=description)
        else:
            raise ValueError("Invalid prize type")

        doc._prizeLevels[level] = prize

    return doc

    # -------------------------------
    # CLI MODE (your existing logic)
    # -------------------------------

    doc._name = input("Sweepstakes name: ").strip()
    doc._doorCount = int(input("How many physical locations are offering this promotion? ").strip())
    doc._doorLocation = input("Where are the locations? ").strip()

    prize_type_input = input("Primary prize type (cash/giftcard): ").strip().lower()
    if prize_type_input == "cash":
        doc._prizes = PrizeType.CASH
    elif prize_type_input == "giftcard":
        doc._prizes = PrizeType.GIFTCARD
    else:
        raise ValueError("Invalid prize type")

    age_input = int(input("Minimum age (18 or 21): ").strip())
    if age_input not in (18, 21):
        raise ValueError("Minimum age must be 18 or 21")
    doc._minAge = age_input

    states = input("Eligible states (comma-separated): ").strip()
    doc._residence = [s.strip() for s in states.split(",") if s.strip()]

    doc._startTime = input("Start time: ").strip()
    doc._endTime = input("End time: ").strip()
    doc._winnerTime = input("Winner selection time: ").strip()
    doc._winnerResponseTime = input("Winner response deadline: ").strip()

    num_levels = int(input("How many prize levels are there? ").strip())
    if num_levels <= 0:
        raise ValueError("Number of prize levels must be positive")

    for i in range(1, num_levels + 1):
        print(f"\n--- Prize Level {i} ---")
        level = int(input("Level number: ").strip())

        ptype = input("Prize type (cash/giftcard): ").strip().lower()
        if ptype == "cash":
            amount = float(input("Cash amount: ").strip())
            prize = Prize(PrizeType.CASH, amount=amount)
        elif ptype == "giftcard":
            description = input("Gift card description: ").strip()
            prize = Prize(PrizeType.GIFTCARD, description=description)
        else:
            raise ValueError("Invalid prize type")

        doc._prizeLevels[level] = prize

    return doc