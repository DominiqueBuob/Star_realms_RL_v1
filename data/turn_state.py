from __future__ import annotations

from dataclasses import dataclass, field

from data.enums import AcquireDestination, CardType, Faction, Phase


@dataclass
class PendingAcquireModifier:
    destination: AcquireDestination
    card_type: CardType | None = None
    uses: int = 1


@dataclass
class TurnState:
    phase: Phase = Phase.ACTION
    trade: int = 0
    combat: int = 0

    cards_played_this_turn: list[int] = field(default_factory=list)
    ships_played_this_turn: list[int] = field(default_factory=list)
    bases_played_this_turn: list[int] = field(default_factory=list)

    factions_played_count: dict[Faction, int] = field(default_factory=dict)
    scrapped_from_hand_or_discard_this_turn: int = 0

    pending_acquire_modifiers: list[PendingAcquireModifier] = field(default_factory=list)

    copied_ship_targets: dict[int, int] = field(default_factory=dict)
    copied_base_targets: dict[int, int] = field(default_factory=dict)

    def count_faction(self, faction: Faction) -> int:
        return self.factions_played_count.get(faction, 0)

    def register_factions(self, factions: tuple[Faction, ...]) -> None:
        for faction in factions:
            self.factions_played_count[faction] = self.factions_played_count.get(faction, 0) + 1