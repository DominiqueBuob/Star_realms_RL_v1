from __future__ import annotations

from typing import Mapping, Protocol

from data.card_defs import CardDef
from data.state import GameState


class Bot(Protocol):
    name: str

    def choose_action(self, state: GameState, card_registry: Mapping[str, CardDef]) -> dict:
        ...