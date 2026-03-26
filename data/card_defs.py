from dataclasses import dataclass, field
from typing import Optional, Tuple
from enums import CardType, Faction, Trigger

@dataclass(frozen=True)
class AbilityDef:
    trigger: Trigger
    condition: object | None = None
    effects: Tuple[object, ...] = ()

@dataclass(frozen=True)
class CardDef:
    id: str
    name: str
    cost: Optional[int]
    factions: Tuple[Faction, ...]
    card_type: CardType
    defense: Optional[int] = None
    is_outpost: bool = False
    abilities: Tuple[AbilityDef, ...] = ()