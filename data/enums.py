from enum import Enum


class _BaseStrEnum(str, Enum):
    """String-valued enum base for easy serialization and comparisons."""


class Faction(_BaseStrEnum):
    BLOB = "BLOB"
    MACHINE_CULT = "MACHINE_CULT"
    STAR_EMPIRE = "STAR_EMPIRE"
    TRADE_FEDERATION = "TRADE_FEDERATION"
    UNALIGNED = "UNALIGNED"


class CardType(_BaseStrEnum):
    SHIP = "SHIP"
    BASE = "BASE"


# To distinguish where the card is currently
class Zone(_BaseStrEnum):
    HAND = "HAND"
    DRAW = "DRAW"
    DISCARD = "DISCARD"
    TRADE_ROW = "TRADE_ROW"
    SCRAP_HEAP = "SCRAP_HEAP"
    IN_PLAY_SHIPS = "IN_PLAY_SHIPS"
    IN_BASE_SHIPS = "IN_BASE_SHIPS"

# What is the phase we are in currently
class Phase(_BaseStrEnum):
    ACTION = "ACTION"
    BUY = "BUY"
    ATTACK = "ATTACK"
    CLEANUP = "CLEANUP"


# How we interact with the card
class Trigger(_BaseStrEnum):
    ON_PLAY = "ON_PLAY"
    ON_SCRAP_FROM_PLAY = "ON_SCRAP_FROM_PLAY"
    ON_ACQUIRE = "ON_ACQUIRE"
    PASSIVE = "PASSIVE"


# Decision types for each action
class DecisionType(_BaseStrEnum):
    CHOOSE_OPTION = "CHOOSE_OPTION"
    CHOOSE_CARD = "CHOOSE_CARD"
    CHOOSE_TARGET = "CHOOSE_TARGET"
    MAY_CHOOSE_CARD = "MAY_CHOOSE_CARD"
    MAY_CHOOSE_TARGET = "MAY_CHOOSE_TARGET"


# Where the card goes after acquiring
class AcquireDestination(_BaseStrEnum):
    DISCARD = "DISCARD"
    TOP_OF_DECK = "TOP_OF_DECK"
    HAND = "HAND"
    DIRECT_TO_PLAY = "DIRECT_TO_PLAY"


__all__ = [
    "Faction",
    "CardType",
    "Zone",
    "Phase",
    "Trigger",
    "DecisionType",
    "AcquireDestination",
]
