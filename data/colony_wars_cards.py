from card_defs import CardDef, AbilityDef
from enums import Faction, CardType, Trigger, AcquireDestination
from effects import (
    AcquireFree,
    ChooseOne,
    CopyBaseUntilEndOfTurn,
    CopyPlayedShip,
    CountsAsAllFactions,
    DestroyTargetBase,
    DiscardThenDrawSameCount,
    DiscardUpToThenGainPerDiscardChoice,
    DrawCards,
    DrawIfBaseCountAtLeast,
    DrawPerFactionPlayed,
    GainAuthority,
    GainAuthorityIfBaseCountAtLeast,
    GainCombat,
    GainCombatIfOpponentHasBase,
    GainCombatPerScrappedThisTurn,
    GainTrade,
    MayDiscardThenDraw,
    OnPlayShipGainCombat,
    OpponentDiscards,
    PutSelfIntoHandOnAcquireIfFactionPlayed,
    ScrapFromDiscard,
    ScrapFromHand,
    ScrapFromHandOrDiscard,
    ScrapFromTradeRow,
    ScrapUpToThenDrawSameCount,
    Sequence,
    SetNextAcquireDestination,
)
from conditions import AllyCondition


def play(*effects, condition=None):
    return AbilityDef(trigger=Trigger.ON_PLAY, condition=condition, effects=tuple(effects))


def scrap(*effects, condition=None):
    return AbilityDef(trigger=Trigger.ON_SCRAP_FROM_PLAY, condition=condition, effects=tuple(effects))


def on_acquire(*effects, condition=None):
    return AbilityDef(trigger=Trigger.ON_ACQUIRE, condition=condition, effects=tuple(effects))


def passive(*effects, condition=None):
    return AbilityDef(trigger=Trigger.PASSIVE, condition=condition, effects=tuple(effects))


def ship(id, name, cost, factions, *abilities):
    return CardDef(
        id=id,
        name=name,
        cost=cost,
        factions=tuple(factions),
        card_type=CardType.SHIP,
        abilities=tuple(abilities),
    )


def base(id, name, cost, factions, defense, *abilities, is_outpost=False):
    return CardDef(
        id=id,
        name=name,
        cost=cost,
        factions=tuple(factions),
        card_type=CardType.BASE,
        defense=defense,
        is_outpost=is_outpost,
        abilities=tuple(abilities),
    )


# =========================
# Colony Wars
# =========================

BIOFORMER = base(
    "bioformer", "Bioformer", 4, (Faction.BLOB,), 4,
    play(GainCombat(3)),
    scrap(GainTrade(3)),
)

CARGO_POD = ship(
    "cargo_pod", "Cargo Pod", 3, (Faction.BLOB,),
    play(GainTrade(3)),
    play(GainCombat(3), condition=AllyCondition(Faction.BLOB)),
    scrap(GainCombat(3)),
)

LEVIATHAN = ship(
    "leviathan", "Leviathan", 8, (Faction.BLOB,),
    play(GainCombat(9), DrawCards(1), DestroyTargetBase(optional=True)),
    play(
        AcquireFree(max_cost=3, destination=AcquireDestination.HAND),
        condition=AllyCondition(Faction.BLOB),
    ),
)

MOONWURM = ship(
    "moonwurm", "Moonwurm", 7, (Faction.BLOB,),
    play(GainCombat(8), DrawCards(1)),
    play(
        AcquireFree(max_cost=2, destination=AcquireDestination.HAND),
        condition=AllyCondition(Faction.BLOB),
    ),
)

PARASITE = ship(
    "parasite", "Parasite", 5, (Faction.BLOB,),
    play(
        ChooseOne(
            options=(
                (GainCombat(6),),
                (AcquireFree(max_cost=6),),
            )
        )
    ),
    play(DrawCards(1), condition=AllyCondition(Faction.BLOB)),
)

PLASMA_VENT = base(
    "plasma_vent", "Plasma Vent", 6, (Faction.BLOB,), 5,
    play(GainCombat(4)),
    on_acquire(PutSelfIntoHandOnAcquireIfFactionPlayed(Faction.BLOB)),
    scrap(DestroyTargetBase(optional=False)),
)

PREDATOR = ship(
    "predator", "Predator", 2, (Faction.BLOB,),
    play(GainCombat(4)),
    play(DrawCards(1), condition=AllyCondition(Faction.BLOB)),
)

RAVAGER = ship(
    "ravager", "Ravager", 3, (Faction.BLOB,),
    play(GainCombat(6), ScrapFromTradeRow(min_cards=0, max_cards=2)),
)

STELLAR_REEF = base(
    "stellar_reef", "Stellar Reef", 2, (Faction.BLOB,), 3,
    play(GainTrade(1)),
    scrap(GainCombat(3)),
)

SWARMER = ship(
    "swarmer", "Swarmer", 1, (Faction.BLOB,),
    play(GainCombat(3), ScrapFromTradeRow(min_cards=0, max_cards=1)),
    play(GainCombat(2), condition=AllyCondition(Faction.BLOB)),
)

BATTLE_BOT = ship(
    "battle_bot", "Battle Bot", 1, (Faction.MACHINE_CULT,),
    play(GainCombat(2), ScrapFromHand(min_cards=0, max_cards=1)),
    play(GainCombat(2), condition=AllyCondition(Faction.MACHINE_CULT)),
)

CONVOY_BOT = ship(
    "convoy_bot", "Convoy Bot", 3, (Faction.MACHINE_CULT,),
    play(GainCombat(4), ScrapFromHandOrDiscard(min_cards=0, max_cards=1)),
    play(GainCombat(2), condition=AllyCondition(Faction.MACHINE_CULT)),
)

FRONTIER_STATION = base(
    "frontier_station", "Frontier Station", 6, (Faction.MACHINE_CULT,), 6,
    play(
        ChooseOne(
            options=(
                (GainTrade(2),),
                (GainCombat(3),),
            )
        )
    ),
    is_outpost=True,
)

MECH_CRUISER = ship(
    "mech_cruiser", "Mech Cruiser", 5, (Faction.MACHINE_CULT,),
    play(GainCombat(6), ScrapFromHandOrDiscard(min_cards=0, max_cards=1)),
    play(DestroyTargetBase(optional=False), condition=AllyCondition(Faction.MACHINE_CULT)),
)

MINING_MECH = ship(
    "mining_mech", "Mining Mech", 4, (Faction.MACHINE_CULT,),
    play(GainTrade(3), ScrapFromHandOrDiscard(min_cards=0, max_cards=1)),
    play(GainCombat(3), condition=AllyCondition(Faction.MACHINE_CULT)),
)

REPAIR_BOT = ship(
    "repair_bot", "Repair Bot", 2, (Faction.MACHINE_CULT,),
    play(GainTrade(2), ScrapFromDiscard(min_cards=0, max_cards=1)),
    scrap(GainCombat(2)),
)

STEALTH_TOWER = base(
    "stealth_tower", "Stealth Tower", 5, (Faction.MACHINE_CULT,), 5,
    play(CopyBaseUntilEndOfTurn()),
    is_outpost=True,
)

THE_INCINERATOR = base(
    "the_incinerator", "The Incinerator", 8, (Faction.MACHINE_CULT,), 6,
    play(ScrapFromHandOrDiscard(min_cards=0, max_cards=2)),
    play(GainCombatPerScrappedThisTurn(amount_per_card=2), condition=AllyCondition(Faction.MACHINE_CULT)),
    is_outpost=True,
)

THE_ORACLE = base(
    "the_oracle", "The Oracle", 4, (Faction.MACHINE_CULT,), 5,
    play(ScrapFromHand(min_cards=1, max_cards=1)),
    play(GainCombat(3), condition=AllyCondition(Faction.MACHINE_CULT)),
    is_outpost=True,
)

THE_WRECKER = ship(
    "the_wrecker", "The Wrecker", 7, (Faction.MACHINE_CULT,),
    play(GainCombat(6), ScrapFromHandOrDiscard(min_cards=0, max_cards=2)),
    play(DrawCards(1), condition=AllyCondition(Faction.MACHINE_CULT)),
)

WARNING_BEACON = base(
    "warning_beacon", "Warning Beacon", 2, (Faction.MACHINE_CULT,), 2,
    play(GainCombat(2)),
    on_acquire(PutSelfIntoHandOnAcquireIfFactionPlayed(Faction.MACHINE_CULT)),
    is_outpost=True,
)

AGING_BATTLESHIP = ship(
    "aging_battleship", "Aging Battleship", 5, (Faction.STAR_EMPIRE,),
    play(GainCombat(5)),
    play(DrawCards(1), condition=AllyCondition(Faction.STAR_EMPIRE)),
    scrap(GainCombat(2), DrawCards(2)),
)

COMMAND_CENTER = base(
    "command_center", "Command Center", 4, (Faction.STAR_EMPIRE,), 4,
    play(GainTrade(2)),
    passive(OnPlayShipGainCombat(amount=2, faction_filter=Faction.STAR_EMPIRE)),
    is_outpost=True,
)

EMPERORS_DREADNAUGHT = ship(
    "emperors_dreadnaught", "Emperor's Dreadnaught", 8, (Faction.STAR_EMPIRE,),
    play(GainCombat(8), DrawCards(1), OpponentDiscards(1)),
    on_acquire(PutSelfIntoHandOnAcquireIfFactionPlayed(Faction.STAR_EMPIRE)),
)

FALCON = ship(
    "falcon", "Falcon", 3, (Faction.STAR_EMPIRE,),
    play(GainCombat(2), DrawCards(1)),
    scrap(OpponentDiscards(1)),
)

GUNSHIP = ship(
    "gunship", "Gunship", 4, (Faction.STAR_EMPIRE,),
    play(GainCombat(5), OpponentDiscards(1)),
    scrap(GainTrade(4)),
)

HEAVY_CRUISER = ship(
    "heavy_cruiser", "Heavy Cruiser", 5, (Faction.STAR_EMPIRE,),
    play(GainCombat(4), DrawCards(1)),
    play(DrawCards(1), condition=AllyCondition(Faction.STAR_EMPIRE)),
)

IMPERIAL_PALACE = base(
    "imperial_palace", "Imperial Palace", 7, (Faction.STAR_EMPIRE,), 6,
    play(DrawCards(1), OpponentDiscards(1)),
    play(GainCombat(4), condition=AllyCondition(Faction.STAR_EMPIRE)),
    is_outpost=True,
)

LANCER = ship(
    "lancer", "Lancer", 2, (Faction.STAR_EMPIRE,),
    play(GainCombat(4), GainCombatIfOpponentHasBase(2)),
    play(OpponentDiscards(1), condition=AllyCondition(Faction.STAR_EMPIRE)),
)

ORBITAL_PLATFORM = base(
    "orbital_platform", "Orbital Platform", 3, (Faction.STAR_EMPIRE,), 4,
    play(MayDiscardThenDraw(draw_amount=1)),
    play(GainCombat(3), condition=AllyCondition(Faction.STAR_EMPIRE)),
)

STAR_BARGE = ship(
    "star_barge", "Star Barge", 1, (Faction.STAR_EMPIRE,),
    play(GainTrade(2)),
    play(Sequence((GainCombat(2), OpponentDiscards(1))), condition=AllyCondition(Faction.STAR_EMPIRE)),
)

SUPPLY_DEPOT = base(
    "supply_depot", "Supply Depot", 6, (Faction.STAR_EMPIRE,), 5,
    play(DiscardUpToThenGainPerDiscardChoice(max_cards=2, trade_per_card=2, combat_per_card=2)),
    play(DrawCards(1), condition=AllyCondition(Faction.STAR_EMPIRE)),
    is_outpost=True,
)

CENTRAL_STATION = base(
    "central_station", "Central Station", 4, (Faction.TRADE_FEDERATION,), 5,
    play(GainTrade(2), GainAuthorityIfBaseCountAtLeast(base_count=3, amount=4), DrawIfBaseCountAtLeast(base_count=3, amount=1)),
)

COLONY_SEED_SHIP = ship(
    "colony_seed_ship", "Colony Seed Ship", 5, (Faction.TRADE_FEDERATION,),
    play(GainTrade(3), GainCombat(3), GainAuthority(3)),
    on_acquire(PutSelfIntoHandOnAcquireIfFactionPlayed(Faction.TRADE_FEDERATION)),
)

FACTORY_WORLD = base(
    "factory_world", "Factory World", 8, (Faction.TRADE_FEDERATION,), 6,
    play(GainTrade(3), SetNextAcquireDestination(destination=AcquireDestination.HAND, card_type=None, uses=1)),
    is_outpost=True,
)

FEDERATION_SHIPYARD = base(
    "federation_shipyard", "Federation Shipyard", 6, (Faction.TRADE_FEDERATION,), 6,
    play(GainTrade(2)),
    play(
        SetNextAcquireDestination(destination=AcquireDestination.TOP_OF_DECK, card_type=None, uses=1),
        condition=AllyCondition(Faction.TRADE_FEDERATION),
    ),
    is_outpost=True,
)

FRONTIER_FERRY = ship(
    "frontier_ferry", "Frontier Ferry", 4, (Faction.TRADE_FEDERATION,),
    play(GainTrade(3), GainAuthority(4)),
    scrap(DestroyTargetBase(optional=False)),
)

LOYAL_COLONY = base(
    "loyal_colony", "Loyal Colony", 7, (Faction.TRADE_FEDERATION,), 6,
    play(GainTrade(3), GainCombat(3), GainAuthority(3)),
)

PATROL_CUTTER = ship(
    "patrol_cutter", "Patrol Cutter", 3, (Faction.TRADE_FEDERATION,),
    play(GainTrade(2), GainCombat(3)),
    play(GainAuthority(4), condition=AllyCondition(Faction.TRADE_FEDERATION)),
)

PEACEKEEPER = ship(
    "peacekeeper", "Peacekeeper", 6, (Faction.TRADE_FEDERATION,),
    play(GainCombat(6), GainAuthority(6)),
    play(DrawCards(1), condition=AllyCondition(Faction.TRADE_FEDERATION)),
)

SOLAR_SKIFF = ship(
    "solar_skiff", "Solar Skiff", 1, (Faction.TRADE_FEDERATION,),
    play(GainTrade(2)),
    play(DrawCards(1), condition=AllyCondition(Faction.TRADE_FEDERATION)),
)

STORAGE_SILO = base(
    "storage_silo", "Storage Silo", 2, (Faction.TRADE_FEDERATION,), 3,
    play(GainAuthority(2)),
    play(GainTrade(2), condition=AllyCondition(Faction.TRADE_FEDERATION)),
)

TRADE_HAULER = ship(
    "trade_hauler", "Trade Hauler", 2, (Faction.TRADE_FEDERATION,),
    play(GainTrade(3)),
    play(GainAuthority(3), condition=AllyCondition(Faction.TRADE_FEDERATION)),
)

EXPLORER_CW = ship(
    "explorer", "Explorer", 2, (Faction.UNALIGNED,),
    play(GainTrade(2)),
    scrap(GainCombat(2)),
)

SCOUT_CW = ship(
    "scout", "Scout", None, (Faction.UNALIGNED,),
    play(GainTrade(1)),
)

VIPER_CW = ship(
    "viper", "Viper", None, (Faction.UNALIGNED,),
    play(GainCombat(1)),
)

# =========================
# Core Set
# =========================

BATTLE_BLOB = ship(
    "battle_blob", "Battle Blob", 6, (Faction.BLOB,),
    play(GainCombat(8)),
    play(DrawCards(1), condition=AllyCondition(Faction.BLOB)),
    scrap(GainCombat(4)),
)

BATTLE_POD = ship(
    "battle_pod", "Battle Pod", 2, (Faction.BLOB,),
    play(GainCombat(4), ScrapFromTradeRow(min_cards=0, max_cards=1)),
    play(GainCombat(2), condition=AllyCondition(Faction.BLOB)),
)

BLOB_CARRIER = ship(
    "blob_carrier", "Blob Carrier", 6, (Faction.BLOB,),
    play(GainCombat(7)),
    play(
        AcquireFree(max_cost=None, card_type=CardType.SHIP, destination=AcquireDestination.TOP_OF_DECK),
        condition=AllyCondition(Faction.BLOB),
    ),
)

BLOB_DESTROYER = ship(
    "blob_destroyer", "Blob Destroyer", 4, (Faction.BLOB,),
    play(GainCombat(6)),
    play(
        Sequence((DestroyTargetBase(optional=True), ScrapFromTradeRow(min_cards=0, max_cards=1))),
        condition=AllyCondition(Faction.BLOB),
    ),
)

BLOB_FIGHTER = ship(
    "blob_fighter", "Blob Fighter", 1, (Faction.BLOB,),
    play(GainCombat(3)),
    play(DrawCards(1), condition=AllyCondition(Faction.BLOB)),
)

BLOB_WHEEL = base(
    "blob_wheel", "Blob Wheel", 3, (Faction.BLOB,), 5,
    play(GainCombat(1)),
    scrap(GainTrade(3)),
)

BLOB_WORLD = base(
    "blob_world", "Blob World", 8, (Faction.BLOB,), None,
    play(
        ChooseOne(
            options=(
                (GainCombat(5),),
                (DrawPerFactionPlayed(faction=Faction.BLOB, include_self=True),),
            )
        )
    ),
)

MOTHERSHIP = ship(
    "mothership", "Mothership", 7, (Faction.BLOB,),
    play(GainCombat(6), DrawCards(1)),
    play(DrawCards(1), condition=AllyCondition(Faction.BLOB)),
)

RAM = ship(
    "ram", "Ram", 3, (Faction.BLOB,),
    play(GainCombat(5)),
    play(GainCombat(2), condition=AllyCondition(Faction.BLOB)),
    scrap(GainTrade(3)),
)

THE_HIVE = base(
    "the_hive", "The Hive", 5, (Faction.BLOB,), 5,
    play(GainCombat(3)),
    play(DrawCards(1), condition=AllyCondition(Faction.BLOB)),
)

TRADE_POD = ship(
    "trade_pod", "Trade Pod", 2, (Faction.BLOB,),
    play(GainTrade(3)),
    play(GainCombat(2), condition=AllyCondition(Faction.BLOB)),
)

BATTLE_MECH = ship(
    "battle_mech", "Battle Mech", 5, (Faction.MACHINE_CULT,),
    play(GainCombat(4), ScrapFromHandOrDiscard(min_cards=0, max_cards=1)),
    play(DrawCards(1), condition=AllyCondition(Faction.MACHINE_CULT)),
)

BATTLE_STATION = base(
    "battle_station", "Battle Station", 3, (Faction.MACHINE_CULT,), 5,
    scrap(GainCombat(5)),
    is_outpost=True,
)

BRAIN_WORLD = base(
    "brain_world", "Brain World", 8, (Faction.MACHINE_CULT,), 6,
    play(ScrapUpToThenDrawSameCount(max_cards=2)),
    is_outpost=True,
)

JUNKYARD = base(
    "junkyard", "Junkyard", 6, (Faction.MACHINE_CULT,), 5,
    play(ScrapFromHandOrDiscard(min_cards=1, max_cards=1)),
    is_outpost=True,
)

MACHINE_BASE = base(
    "machine_base", "Machine Base", 7, (Faction.MACHINE_CULT,), 6,
    play(DrawCards(1), ScrapFromHand(min_cards=1, max_cards=1)),
    is_outpost=True,
)

MECH_WORLD = base(
    "mech_world", "Mech World", 5, (Faction.MACHINE_CULT,), 6,
    passive(CountsAsAllFactions()),
    is_outpost=True,
)

MISSILE_BOT = ship(
    "missile_bot", "Missile Bot", 2, (Faction.MACHINE_CULT,),
    play(GainCombat(2), ScrapFromHandOrDiscard(min_cards=0, max_cards=1)),
    play(GainCombat(2), condition=AllyCondition(Faction.MACHINE_CULT)),
)

MISSILE_MECH = ship(
    "missile_mech", "Missile Mech", 6, (Faction.MACHINE_CULT,),
    play(GainCombat(6), DestroyTargetBase(optional=True)),
    play(DrawCards(1), condition=AllyCondition(Faction.MACHINE_CULT)),
)

PATROL_MECH = ship(
    "patrol_mech", "Patrol Mech", 4, (Faction.MACHINE_CULT,),
    play(
        ChooseOne(
            options=(
                (GainTrade(3),),
                (GainCombat(5),),
            )
        )
    ),
    play(ScrapFromHandOrDiscard(min_cards=0, max_cards=1), condition=AllyCondition(Faction.MACHINE_CULT)),
)

STEALTH_NEEDLE = ship(
    "stealth_needle", "Stealth Needle", 4, (Faction.MACHINE_CULT,),
    play(CopyPlayedShip()),
)

SUPPLY_BOT = ship(
    "supply_bot", "Supply Bot", 3, (Faction.MACHINE_CULT,),
    play(GainTrade(2), ScrapFromHandOrDiscard(min_cards=0, max_cards=1)),
    play(GainCombat(2), condition=AllyCondition(Faction.MACHINE_CULT)),
)

TRADE_BOT = ship(
    "trade_bot", "Trade Bot", 1, (Faction.MACHINE_CULT,),
    play(GainTrade(1), ScrapFromHandOrDiscard(min_cards=0, max_cards=1)),
    play(GainCombat(2), condition=AllyCondition(Faction.MACHINE_CULT)),
)

BATTLECRUISER = ship(
    "battlecruiser", "Battlecruiser", 6, (Faction.STAR_EMPIRE,),
    play(GainCombat(5), DrawCards(1)),
    play(OpponentDiscards(1), condition=AllyCondition(Faction.STAR_EMPIRE)),
    scrap(DrawCards(1), DestroyTargetBase(optional=True)),
)

CORVETTE = ship(
    "corvette", "Corvette", 2, (Faction.STAR_EMPIRE,),
    play(GainCombat(1), DrawCards(1)),
    play(GainCombat(2), condition=AllyCondition(Faction.STAR_EMPIRE)),
)

DREADNAUGHT = ship(
    "dreadnaught", "Dreadnaught", 7, (Faction.STAR_EMPIRE,),
    play(GainCombat(7), DrawCards(1)),
    scrap(GainCombat(5)),
)

FLEET_HQ = base(
    "fleet_hq", "Fleet HQ", 8, (Faction.STAR_EMPIRE,), 8,
    passive(OnPlayShipGainCombat(amount=1, faction_filter=None)),
)

IMPERIAL_FIGHTER = ship(
    "imperial_fighter", "Imperial Fighter", 1, (Faction.STAR_EMPIRE,),
    play(GainCombat(2), OpponentDiscards(1)),
    play(GainCombat(2), condition=AllyCondition(Faction.STAR_EMPIRE)),
)

IMPERIAL_FRIGATE = ship(
    "imperial_frigate", "Imperial Frigate", 3, (Faction.STAR_EMPIRE,),
    play(GainCombat(4), OpponentDiscards(1)),
    play(GainCombat(2), condition=AllyCondition(Faction.STAR_EMPIRE)),
    scrap(DrawCards(1)),
)

RECYCLING_STATION = base(
    "recycling_station", "Recycling Station", 4, (Faction.STAR_EMPIRE,), 4,
    play(
        ChooseOne(
            options=(
                (GainTrade(1),),
                (DiscardThenDrawSameCount(max_cards=2),),
            )
        )
    ),
    is_outpost=True,
)

ROYAL_REDOUBT = base(
    "royal_redoubt", "Royal Redoubt", 6, (Faction.STAR_EMPIRE,), 6,
    play(GainCombat(3)),
    play(OpponentDiscards(1), condition=AllyCondition(Faction.STAR_EMPIRE)),
    is_outpost=True,
)

SPACE_STATION = base(
    "space_station", "Space Station", 4, (Faction.STAR_EMPIRE,), 4,
    play(GainCombat(2)),
    play(GainCombat(2), condition=AllyCondition(Faction.STAR_EMPIRE)),
    scrap(GainTrade(4)),
    is_outpost=True,
)

SURVEY_SHIP = ship(
    "survey_ship", "Survey Ship", 3, (Faction.STAR_EMPIRE,),
    play(GainTrade(1), DrawCards(1)),
    scrap(OpponentDiscards(1)),
)

WAR_WORLD = base(
    "war_world", "War World", 5, (Faction.STAR_EMPIRE,), 4,
    play(GainCombat(3)),
    play(GainCombat(4), condition=AllyCondition(Faction.STAR_EMPIRE)),
    is_outpost=True,
)

BARTER_WORLD = base(
    "barter_world", "Barter World", 4, (Faction.TRADE_FEDERATION,), 4,
    play(
        ChooseOne(
            options=(
                (GainAuthority(2),),
                (GainTrade(2),),
            )
        )
    ),
    scrap(GainCombat(5)),
)

CENTRAL_OFFICE = base(
    "central_office", "Central Office", 7, (Faction.TRADE_FEDERATION,), 6,
    play(GainTrade(2), SetNextAcquireDestination(destination=AcquireDestination.TOP_OF_DECK, card_type=CardType.SHIP, uses=1)),
    play(DrawCards(1), condition=AllyCondition(Faction.TRADE_FEDERATION)),
)

COMMAND_SHIP = ship(
    "command_ship", "Command Ship", 8, (Faction.TRADE_FEDERATION,),
    play(GainAuthority(4), GainCombat(5), DrawCards(2)),
    play(DestroyTargetBase(optional=False), condition=AllyCondition(Faction.TRADE_FEDERATION)),
)

CUTTER = ship(
    "cutter", "Cutter", 2, (Faction.TRADE_FEDERATION,),
    play(GainAuthority(4), GainTrade(2)),
    play(GainCombat(4), condition=AllyCondition(Faction.TRADE_FEDERATION)),
)

DEFENSE_CENTER = base(
    "defense_center", "Defense Center", 5, (Faction.TRADE_FEDERATION,), 5,
    play(
        ChooseOne(
            options=(
                (GainAuthority(3),),
                (GainCombat(2),),
            )
        )
    ),
    play(GainCombat(2), condition=AllyCondition(Faction.TRADE_FEDERATION)),
    is_outpost=True,
)

EMBASSY_YACHT = ship(
    "embassy_yacht", "Embassy Yacht", 3, (Faction.TRADE_FEDERATION,),
    play(GainAuthority(3), GainTrade(2), DrawIfBaseCountAtLeast(base_count=2, amount=2)),
)

FEDERATION_SHUTTLE = ship(
    "federation_shuttle", "Federation Shuttle", 1, (Faction.TRADE_FEDERATION,),
    play(GainTrade(2)),
    play(GainAuthority(4), condition=AllyCondition(Faction.TRADE_FEDERATION)),
)

FLAGSHIP = ship(
    "flagship", "Flagship", 6, (Faction.TRADE_FEDERATION,),
    play(GainCombat(5), DrawCards(1)),
    play(GainAuthority(5), condition=AllyCondition(Faction.TRADE_FEDERATION)),
)

FREIGHTER = ship(
    "freighter", "Freighter", 4, (Faction.TRADE_FEDERATION,),
    play(GainTrade(4)),
    play(
        SetNextAcquireDestination(destination=AcquireDestination.TOP_OF_DECK, card_type=CardType.SHIP, uses=1),
        condition=AllyCondition(Faction.TRADE_FEDERATION),
    ),
)

PORT_OF_CALL = base(
    "port_of_call", "Port of Call", 6, (Faction.TRADE_FEDERATION,), 6,
    play(GainTrade(3)),
    scrap(DrawCards(1), DestroyTargetBase(optional=True)),
    is_outpost=True,
)

TRADE_ESCORT = ship(
    "trade_escort", "Trade Escort", 5, (Faction.TRADE_FEDERATION,),
    play(GainAuthority(4), GainCombat(4)),
    play(DrawCards(1), condition=AllyCondition(Faction.TRADE_FEDERATION)),
)

TRADING_POST = base(
    "trading_post", "Trading Post", 3, (Faction.TRADE_FEDERATION,), 4,
    play(
        ChooseOne(
            options=(
                (GainAuthority(1),),
                (GainTrade(1),),
            )
        )
    ),
    scrap(GainCombat(3)),
    is_outpost=True,
)

EXPLORER = ship(
    "explorer", "Explorer", 2, (Faction.UNALIGNED,),
    play(GainTrade(2)),
    scrap(GainCombat(2)),
)

SCOUT = ship(
    "scout", "Scout", None, (Faction.UNALIGNED,),
    play(GainTrade(1)),
)

VIPER = ship(
    "viper", "Viper", None, (Faction.UNALIGNED,),
    play(GainCombat(1)),
)

CARDS = {
    card.id: card
    for card in (
        BIOFORMER,
        CARGO_POD,
        LEVIATHAN,
        MOONWURM,
        PARASITE,
        PLASMA_VENT,
        PREDATOR,
        RAVAGER,
        STELLAR_REEF,
        SWARMER,
        BATTLE_BOT,
        CONVOY_BOT,
        FRONTIER_STATION,
        MECH_CRUISER,
        MINING_MECH,
        REPAIR_BOT,
        # STEALTH_TOWER,
        THE_INCINERATOR,
        THE_ORACLE,
        THE_WRECKER,
        WARNING_BEACON,
        AGING_BATTLESHIP,
        COMMAND_CENTER,
        EMPERORS_DREADNAUGHT,
        FALCON,
        GUNSHIP,
        HEAVY_CRUISER,
        IMPERIAL_PALACE,
        LANCER,
        ORBITAL_PLATFORM,
        STAR_BARGE,
        SUPPLY_DEPOT,
        CENTRAL_STATION,
        COLONY_SEED_SHIP,
        FACTORY_WORLD,
        FEDERATION_SHIPYARD,
        FRONTIER_FERRY,
        LOYAL_COLONY,
        PATROL_CUTTER,
        PEACEKEEPER,
        SOLAR_SKIFF,
        STORAGE_SILO,
        TRADE_HAULER,
        BATTLE_BLOB,
        BATTLE_POD,
        BLOB_CARRIER,
        BLOB_DESTROYER,
        BLOB_FIGHTER,
        BLOB_WHEEL,
        BLOB_WORLD,
        MOTHERSHIP,
        RAM,
        THE_HIVE,
        TRADE_POD,
        BATTLE_MECH,
        BATTLE_STATION,
        BRAIN_WORLD,
        JUNKYARD,
        MACHINE_BASE,
        MECH_WORLD,
        MISSILE_BOT,
        MISSILE_MECH,
        PATROL_MECH,
        # STEALTH_NEEDLE,
        SUPPLY_BOT,
        TRADE_BOT,
        BATTLECRUISER,
        CORVETTE,
        DREADNAUGHT,
        FLEET_HQ,
        IMPERIAL_FIGHTER,
        IMPERIAL_FRIGATE,
        RECYCLING_STATION,
        ROYAL_REDOUBT,
        SPACE_STATION,
        SURVEY_SHIP,
        WAR_WORLD,
        BARTER_WORLD,
        CENTRAL_OFFICE,
        COMMAND_SHIP,
        CUTTER,
        DEFENSE_CENTER,
        EMBASSY_YACHT,
        FEDERATION_SHUTTLE,
        FLAGSHIP,
        FREIGHTER,
        PORT_OF_CALL,
        TRADE_ESCORT,
        TRADING_POST,
        EXPLORER,
        SCOUT,
        VIPER,
    )
}