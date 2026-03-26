from __future__ import annotations

from dataclasses import dataclass, field
import random

from data.turn_state import TurnState
from data.pending import PendingDecision


@dataclass
class CardInstance:
    instance_id: int
    card_def_id: str
    owner: int | None = None


@dataclass
class PlayerState:
    authority: int = 50
    forced_discards_next_turn: int = 0

    draw_pile: list[int] = field(default_factory=list)
    hand: list[int] = field(default_factory=list)
    discard_pile: list[int] = field(default_factory=list)

    ships_in_play: list[int] = field(default_factory=list)
    bases_in_play: list[int] = field(default_factory=list)

    def all_in_play(self) -> list[int]:
        return self.ships_in_play + self.bases_in_play


@dataclass
class GameState:
    cards: dict[int, CardInstance] = field(default_factory=dict)

    players: list[PlayerState] = field(default_factory=lambda: [PlayerState(), PlayerState()])

    trade_deck: list[int] = field(default_factory=list)
    trade_row: list[int] = field(default_factory=list)

    explorer_pile_count: int = 10
    scrap_heap: list[int] = field(default_factory=list)

    active_player: int = 0
    turn_number: int = 1

    turn: TurnState = field(default_factory=TurnState)
    pending: list[PendingDecision] = field(default_factory=list)

    winner: int | None = None

    rng: random.Random = field(default_factory=random.Random)
    next_instance_id: int = 1

    def current_player(self) -> PlayerState:
        return self.players[self.active_player]

    def opponent_player(self) -> PlayerState:
        return self.players[1 - self.active_player]

    def new_instance(self, card_def_id: str, owner: int | None = None) -> int:
        instance_id = self.next_instance_id
        self.next_instance_id += 1
        self.cards[instance_id] = CardInstance(
            instance_id=instance_id,
            card_def_id=card_def_id,
            owner=owner,
        )
        return instance_id