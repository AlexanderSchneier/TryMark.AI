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
        self._applied_constraints = []


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

            f.write("HARD CONSTRAINTS APPLIED\n")
            f.write("-" * 24 + "\n")
            for c in self._applied_constraints:
                f.write(f"- {c['rule']}\n")

        print(f"\n📄 Compliance report written to: {filename}")
    def _total_prize_value(self) -> float:
        total = 0.0
        for prize in self._prizeLevels.values():
            if prize.prize_type == PrizeType.CASH and prize.amount:
                total += prize.amount
        return total

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
        applied = []
        warnings = []

        # ---- Normalize states ----
        normalized_states = set()

        for state in self._residence or []:
            s = state.strip().upper()

            if len(s) == 2:
                normalized_states.add(s)
            elif s in STATE_NAME_TO_CODE:
                normalized_states.add(STATE_NAME_TO_CODE[s])
                warnings.append(
                    f"State '{state}' normalized to '{STATE_NAME_TO_CODE[s]}'"
                )
            else:
                warnings.append(
                    f"Unrecognized state '{state}'. State-specific constraints may not apply."
                )

        state_codes = {f"US-{s}" for s in normalized_states}
        total_prize_value = self._total_prize_value()

        # ---- Apply constraints ----
        for constraint in self._hard_constraints:
            jurisdictions = set(constraint.get("jurisdictions", []))
            thresholds = constraint.get("thresholds", {})

            # ---- Threshold checks ----
            if "total_prize_value_usd" in thresholds:
                if total_prize_value <= thresholds["total_prize_value_usd"]:
                    continue

            if "prize_value_usd" in thresholds:
                if total_prize_value <= thresholds["prize_value_usd"]:
                    continue

            # ---- Federal rules ----
            if "US-FEDERAL" in jurisdictions:
                applied.append(constraint)
                continue

            # ---- State rules ----
            if jurisdictions.intersection(state_codes):
                applied.append(constraint)

        self._applied_constraints = applied
        self._constraint_warnings = warnings

    def print_hard_constraints(self) -> None:
        print("\nHARD CONSTRAINTS APPLIED:")
        for c in self._applied_constraints:
            print(f"- {c['rule']}")
    def print_constraint_warnings(self) -> None:
        if not getattr(self, "_constraint_warnings", None):
            return

        print("\n⚠️ CONSTRAINT WARNINGS:")
        for w in self._constraint_warnings:
            print(f"- {w}")



def create_document() -> Document:
    doc = Document()

    doc._name = input("Sweepstakes name: ").strip()
    doc._doorCount = int(input("How many physical locations are offering this promotion? ").strip())
    doc._doorLocation = input("Where are the locations? ").strip()

    # ---- Primary prize type ----
    prize_type_input = input("Primary prize type (cash/giftcard): ").strip().lower()
    if prize_type_input == "cash":
        doc._prizes = PrizeType.CASH
    elif prize_type_input == "giftcard":
        doc._prizes = PrizeType.GIFTCARD
    else:
        raise ValueError("Invalid prize type (must be 'cash' or 'giftcard')")

    # ---- Age ----
    age_input = int(input("Minimum age (18 or 21): ").strip())
    if age_input not in (18, 21):
        raise ValueError("Minimum age must be 18 or 21")
    doc._minAge = age_input

    # ---- Residence ----
    states = input("Eligible states (comma-separated): ").strip()
    doc._residence = [s.strip() for s in states.split(",") if s.strip()]

    # ---- Times ----
    doc._startTime = input("Start time: ").strip()
    doc._endTime = input("End time: ").strip()
    doc._winnerTime = input("Winner selection time: ").strip()
    doc._winnerResponseTime = input("Winner response deadline: ").strip()

    # ---- Prize levels (fixed count) ----
    num_levels = int(input("How many prize levels are there? ").strip())
    if num_levels <= 0:
        raise ValueError("Number of prize levels must be a positive integer")

    for i in range(1, num_levels + 1):
        print(f"\n--- Prize Level {i} ---")
        level = int(input("Level number (e.g., 1): ").strip())

        ptype = input("Prize type (cash/giftcard): ").strip().lower()
        if ptype == "cash":
            amount = float(input("Cash amount: ").strip())
            prize = Prize(PrizeType.CASH, amount=amount)
        elif ptype == "giftcard":
            description = input("Gift card description: ").strip()
            prize = Prize(PrizeType.GIFTCARD, description=description)
        else:
            raise ValueError("Invalid prize type (must be 'cash' or 'giftcard')")

        doc._prizeLevels[level] = prize

    return doc


def main():
    try:
        doc = create_document()

        doc.load_hard_constraints("hard_constraints.json")
        doc.apply_hard_constraints()
        doc.print_hard_constraints()
        doc.print_constraint_warnings()

        doc.validate()

        doc.write_compliance_report()

        print("\n✅ Document successfully created, validated, and exported.")

    except ValueError as e:
        print("\n❌ Validation failed:")
        print(f"   {e}")

    except Exception as e:
        print("\n❌ Unexpected error:")
        print(f"   {e}")


if __name__ == "__main__":
    main()



