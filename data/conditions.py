# conditions.py

from __future__ import annotations

from dataclasses import dataclass

from enums import Faction, CardType


class Condition:
    pass


@dataclass(frozen=True)
class AllyCondition(Condition):
    faction: Faction


@dataclass(frozen=True)
class OpponentHasBaseCondition(Condition):
    pass


@dataclass(frozen=True)
class BaseCountAtLeastCondition(Condition):
    count: int
    include_self: bool = True


@dataclass(frozen=True)
class PlayedFactionThisTurnCondition(Condition):
    faction: Faction


@dataclass(frozen=True)
class PlayedShipOfFactionCondition(Condition):
    faction: Faction


@dataclass(frozen=True)
class PlayedBaseThisTurnCondition(Condition):
    pass


@dataclass(frozen=True)
class ScrappedFromHandOrDiscardThisTurnAtLeastCondition(Condition):
    count: int


@dataclass(frozen=True)
class CardTypePlayedThisTurnCondition(Condition):
    card_type: CardType


@dataclass(frozen=True)
class AlwaysCondition(Condition):
    pass


__all__ = [
    "Condition",
    "AllyCondition",
    "OpponentHasBaseCondition",
    "BaseCountAtLeastCondition",
    "PlayedFactionThisTurnCondition",
    "PlayedShipOfFactionCondition",
    "PlayedBaseThisTurnCondition",
    "ScrappedFromHandOrDiscardThisTurnAtLeastCondition",
    "CardTypePlayedThisTurnCondition",
    "AlwaysCondition",
]