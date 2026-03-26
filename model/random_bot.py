from __future__ import annotations

import random
from typing import Mapping

from data.card_defs import CardDef
from data.legal_actions import get_legal_actions
from data.state import GameState


class RandomBot:
    name = "random"

    def __init__(self, seed: int | None = None):
        self.rng = random.Random(seed)

    def choose_action(self, state: GameState, card_registry: Mapping[str, CardDef]) -> dict:
        actions = get_legal_actions(state, card_registry)
        if not actions:
            raise ValueError("No legal actions available.")
        return self.rng.choice(actions)