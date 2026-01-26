from enum import Enum
from typing import Literal, Dict

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
        self._prizeLevels: Dict[int, prize] = {}

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
















