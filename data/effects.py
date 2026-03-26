from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Tuple

from enums import AcquireDestination, CardType, Faction


class Effect:
    pass


@dataclass(frozen=True)
class GainTrade(Effect):
    amount: int


@dataclass(frozen=True)
class GainCombat(Effect):
    amount: int


@dataclass(frozen=True)
class GainAuthority(Effect):
    amount: int


@dataclass(frozen=True)
class DrawCards(Effect):
    amount: int


@dataclass(frozen=True)
class OpponentDiscards(Effect):
    amount: int = 1


@dataclass(frozen=True)
class ScrapFromHand(Effect):
    min_cards: int = 0
    max_cards: int = 1


@dataclass(frozen=True)
class ScrapFromDiscard(Effect):
    min_cards: int = 0
    max_cards: int = 1


@dataclass(frozen=True)
class ScrapFromHandOrDiscard(Effect):
    min_cards: int = 0
    max_cards: int = 1


@dataclass(frozen=True)
class ScrapFromTradeRow(Effect):
    min_cards: int = 0
    max_cards: int = 1


@dataclass(frozen=True)
class DiscardFromHand(Effect):
    min_cards: int = 0
    max_cards: int = 1


@dataclass(frozen=True)
class DiscardThenDrawSameCount(Effect):
    max_cards: int


@dataclass(frozen=True)
class DrawThenDiscard(Effect):
    draw_amount: int
    discard_amount: int


@dataclass(frozen=True)
class DestroyTargetBase(Effect):
    optional: bool = True


@dataclass(frozen=True)
class ChooseOne(Effect):
    options: Tuple[Tuple[Effect, ...], ...]


@dataclass(frozen=True)
class AcquireFree(Effect):
    max_cost: int | None = None
    card_type: CardType | None = None
    destination: AcquireDestination = AcquireDestination.DISCARD


@dataclass(frozen=True)
class SetNextAcquireDestination(Effect):
    destination: AcquireDestination
    card_type: CardType | None = None
    uses: int = 1


@dataclass(frozen=True)
class PutSelfIntoHandOnAcquireIfFactionPlayed(Effect):
    faction: Faction


@dataclass(frozen=True)
class DrawPerFactionPlayed(Effect):
    faction: Faction
    include_self: bool = True


@dataclass(frozen=True)
class GainCombatIfOpponentHasBase(Effect):
    amount: int


@dataclass(frozen=True)
class GainAuthorityIfBaseCountAtLeast(Effect):
    base_count: int
    amount: int
    include_self: bool = True


@dataclass(frozen=True)
class DrawIfBaseCountAtLeast(Effect):
    base_count: int
    amount: int
    include_self: bool = True


@dataclass(frozen=True)
class GainCombatPerScrappedThisTurn(Effect):
    amount_per_card: int


@dataclass(frozen=True)
class DrawPerCardsScrappedByThisEffect(Effect):
    amount_per_card: int = 1


@dataclass(frozen=True)
class CountsAsAllFactions(Effect):
    pass


@dataclass(frozen=True)
class CopyPlayedShip(Effect):
    pass


@dataclass(frozen=True)
class CopyBaseUntilEndOfTurn(Effect):
    pass


@dataclass(frozen=True)
class OnPlayShipGainCombat(Effect):
    amount: int
    faction_filter: Faction | None = None


@dataclass(frozen=True)
class Sequence(Effect):
    effects: Tuple[Effect, ...]


@dataclass(frozen=True)
class Conditional(Effect):
    condition: object
    effect: Effect


# Add these to effects.py

@dataclass(frozen=True)
class MayDiscardThenDraw(Effect):
    draw_amount: int = 1
    max_discards: int = 1


@dataclass(frozen=True)
class DiscardUpToThenGainPerDiscardChoice(Effect):
    max_cards: int
    trade_per_card: int
    combat_per_card: int


@dataclass(frozen=True)
class ScrapUpToThenDrawSameCount(Effect):
    max_cards: int
    
EffectLike = Effect


__all__ = [
    "Effect",
    "GainTrade",
    "GainCombat",
    "GainAuthority",
    "DrawCards",
    "OpponentDiscards",
    "ScrapFromHand",
    "ScrapFromDiscard",
    "ScrapFromHandOrDiscard",
    "ScrapFromTradeRow",
    "DiscardFromHand",
    "DiscardThenDrawSameCount",
    "DrawThenDiscard",
    "DestroyTargetBase",
    "ChooseOne",
    "AcquireFree",
    "SetNextAcquireDestination",
    "PutSelfIntoHandOnAcquireIfFactionPlayed",
    "DrawPerFactionPlayed",
    "GainCombatIfOpponentHasBase",
    "GainAuthorityIfBaseCountAtLeast",
    "DrawIfBaseCountAtLeast",
    "GainCombatPerScrappedThisTurn",
    "DrawPerCardsScrappedByThisEffect",
    "CountsAsAllFactions",
    "CopyPlayedShip",
    "CopyBaseUntilEndOfTurn",
    "OnPlayShipGainCombat",
    "Sequence",
    "Conditional",
    "EffectLike",
    "MayDiscardThenDraw",
    "DiscardUpToThenGainPerDiscardChoice",
    "ScrapUpToThenDrawSameCount"
]