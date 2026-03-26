from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from enums import DecisionType


@dataclass
class PendingDecision:
    decision_type: DecisionType
    player: int
    source_card_id: int | None = None
    payload: dict[str, Any] = field(default_factory=dict)