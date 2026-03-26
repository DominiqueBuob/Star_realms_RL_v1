from __future__ import annotations

from typing import Mapping
from dataclasses import replace

from data.card_defs import CardDef
from data.conditions import AllyCondition
from data.effects import (
    AcquireFree,
    ChooseOne,
    # CopyBaseUntilEndOfTurn,
    # CopyPlayedShip,
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
from data.enums import AcquireDestination, CardType, DecisionType, Phase, Trigger
from data.pending import PendingDecision
from data.state import GameState
from data.turn_state import PendingAcquireModifier, TurnState



def current_player(state: GameState):
    return state.players[state.active_player]


def opponent_player(state: GameState):
    return state.players[1 - state.active_player]


def get_card_def(state: GameState, card_registry: Mapping[str, CardDef], instance_id: int) -> CardDef:
    return card_registry[state.cards[instance_id].card_def_id]


def _fill_trade_row(state: GameState) -> None:
    while len(state.trade_row) < 5 and state.trade_deck:
        state.trade_row.append(state.trade_deck.pop())


def _move_to_scrap_heap(state: GameState, instance_id: int) -> None:
    state.scrap_heap.append(instance_id)


def _remove_from_list(lst: list[int], instance_id: int) -> None:
    if instance_id in lst:
        lst.remove(instance_id)

def _effective_card_def(state: GameState, card_registry: Mapping[str, CardDef], instance_id: int) -> CardDef:
    return get_card_def(state, card_registry, instance_id)


def _card_counts_as_all_factions(card_def: CardDef) -> bool:
    for ability in card_def.abilities:
        if ability.trigger == Trigger.PASSIVE:
            for effect in ability.effects:
                if isinstance(effect, CountsAsAllFactions):
                    return True
    return False


def _all_faction_bonus_in_play(state: GameState, card_registry: Mapping[str, CardDef]) -> int:
    total = 0
    for card_id in current_player(state).bases_in_play + current_player(state).ships_in_play:
        card_def = _effective_card_def(state, card_registry, card_id)
        if _card_counts_as_all_factions(card_def):
            total += 1
    return total


def _evaluate_condition(state: GameState, card_registry: Mapping[str, CardDef], condition) -> bool:
    if condition is None:
        return True

    if isinstance(condition, AllyCondition):
        return state.turn.count_faction(condition.faction) + _all_faction_bonus_in_play(state, card_registry) >= 2

    raise NotImplementedError(f"Unsupported condition: {type(condition).__name__}")


def draw_card(state: GameState, player_idx: int) -> int | None:
    player = state.players[player_idx]
    if not player.draw_pile:
        if not player.discard_pile:
            return None
        player.draw_pile = list(player.discard_pile)
        player.discard_pile.clear()
        state.rng.shuffle(player.draw_pile)

    card_id = player.draw_pile.pop()
    player.hand.append(card_id)
    return card_id


def draw_cards(state: GameState, player_idx: int, amount: int) -> None:
    for _ in range(amount):
        draw_card(state, player_idx)


def _start_turn(state: GameState) -> None:
    state.turn = TurnState(phase=Phase.ACTION)
    player = current_player(state)

    discard_count = min(player.forced_discards_next_turn, len(player.hand))
    player.forced_discards_next_turn = 0

    if discard_count > 0:
        state.pending.append(
            PendingDecision(
                decision_type=DecisionType.CHOOSE_CARD,
                player=state.active_player,
                payload={
                    "kind": "forced_discard",
                    "remaining": discard_count,
                    "valid_card_ids": list(player.hand),
                    "optional": False,
                },
            )
        )


def _apply_ship_play_passives(state: GameState, card_registry: Mapping[str, CardDef], played_ship_id: int) -> None:
    played_ship_def = _effective_card_def(state, card_registry, played_ship_id)
    for base_id in list(current_player(state).bases_in_play):
        base_def = _effective_card_def(state, card_registry, base_id)
        for ability in base_def.abilities:
            if ability.trigger != Trigger.PASSIVE:
                continue
            for effect in ability.effects:
                if isinstance(effect, OnPlayShipGainCombat):
                    if effect.faction_filter is None or effect.faction_filter in played_ship_def.factions:
                        state.turn.combat += effect.amount


def _resolve_on_play_abilities(state: GameState, card_registry: Mapping[str, CardDef], instance_id: int) -> None:
    card_def = _effective_card_def(state, card_registry, instance_id)
    for ability in card_def.abilities:
        if ability.trigger != Trigger.ON_PLAY:
            continue
        if not _evaluate_condition(state, card_registry, ability.condition):
            continue
        for effect in ability.effects:
            _apply_effect(state, card_registry, instance_id, effect)


def _resolve_on_acquire_abilities(state: GameState, card_registry: Mapping[str, CardDef], instance_id: int) -> None:
    card_def = _effective_card_def(state, card_registry, instance_id)
    for ability in card_def.abilities:
        if ability.trigger != Trigger.ON_ACQUIRE:
            continue
        if not _evaluate_condition(state, card_registry, ability.condition):
            continue
        for effect in ability.effects:
            _apply_effect(state, card_registry, instance_id, effect)


def _apply_effect(state: GameState, card_registry: Mapping[str, CardDef], source_id: int | None, effect) -> None:
    if isinstance(effect, GainTrade):
        state.turn.trade += effect.amount
        return

    if isinstance(effect, GainCombat):
        state.turn.combat += effect.amount
        return

    if isinstance(effect, GainAuthority):
        current_player(state).authority += effect.amount
        return

    if isinstance(effect, DrawCards):
        draw_cards(state, state.active_player, effect.amount)
        return

    if isinstance(effect, OpponentDiscards):
        opponent_player(state).forced_discards_next_turn += effect.amount
        return

    if isinstance(effect, ScrapFromHand):
        _enqueue_choose_cards_from_zone(
            state, "scrap_hand", current_player(state).hand, effect.min_cards, effect.max_cards, source_id
        )
        return

    if isinstance(effect, ScrapFromDiscard):
        _enqueue_choose_cards_from_zone(
            state, "scrap_discard", current_player(state).discard_pile, effect.min_cards, effect.max_cards, source_id
        )
        return

    if isinstance(effect, ScrapFromHandOrDiscard):
        _enqueue_choose_cards_from_multiple_zones(
            state,
            "scrap_hand_or_discard",
            current_player(state).hand,
            current_player(state).discard_pile,
            effect.min_cards,
            effect.max_cards,
            source_id,
        )
        return

    if isinstance(effect, ScrapFromTradeRow):
        _enqueue_choose_trade_row_cards(state, effect.min_cards, effect.max_cards, source_id)
        return

    if isinstance(effect, DestroyTargetBase):
        _enqueue_choose_target_base(state, source_id, optional=effect.optional, free_destroy=True)
        return

    if isinstance(effect, ChooseOne):
        state.pending.append(
            PendingDecision(
                decision_type=DecisionType.CHOOSE_OPTION,
                player=state.active_player,
                source_card_id=source_id,
                payload={"kind": "choose_one", "options": effect.options},
            )
        )
        return

    if isinstance(effect, AcquireFree):
        valid = []
        for card_id in state.trade_row:
            cdef = get_card_def(state, card_registry, card_id)
            if effect.max_cost is not None and (cdef.cost is None or cdef.cost > effect.max_cost):
                continue
            if effect.card_type is not None and cdef.card_type != effect.card_type:
                continue
            valid.append(card_id)
        state.pending.append(
            PendingDecision(
                decision_type=DecisionType.CHOOSE_CARD,
                player=state.active_player,
                source_card_id=source_id,
                payload={
                    "kind": "acquire_free",
                    "valid_card_ids": valid,
                    "destination": effect.destination,
                    "optional": True,
                },
            )
        )
        return

    if isinstance(effect, SetNextAcquireDestination):
        state.turn.pending_acquire_modifiers.append(
            PendingAcquireModifier(
                destination=effect.destination,
                card_type=effect.card_type,
                uses=effect.uses,
            )
        )
        return

    if isinstance(effect, PutSelfIntoHandOnAcquireIfFactionPlayed):
        if state.turn.count_faction(effect.faction) + _all_faction_bonus_in_play(state, card_registry) >= 1 and source_id is not None:
            p = current_player(state)
            if source_id in p.discard_pile:
                p.discard_pile.remove(source_id)
                p.hand.append(source_id)
        return

    if isinstance(effect, DrawPerFactionPlayed):
        draw_cards(state, state.active_player, state.turn.count_faction(effect.faction))
        return

    if isinstance(effect, GainCombatIfOpponentHasBase):
        if opponent_player(state).bases_in_play:
            state.turn.combat += effect.amount
        return

    if isinstance(effect, GainAuthorityIfBaseCountAtLeast):
        total = len(current_player(state).bases_in_play)
        if total >= effect.base_count:
            current_player(state).authority += effect.amount
        return

    if isinstance(effect, DrawIfBaseCountAtLeast):
        total = len(current_player(state).bases_in_play)
        if total >= effect.base_count:
            draw_cards(state, state.active_player, effect.amount)
        return

    if isinstance(effect, GainCombatPerScrappedThisTurn):
        state.turn.combat += effect.amount_per_card * state.turn.scrapped_from_hand_or_discard_this_turn
        return

    if isinstance(effect, CountsAsAllFactions):
        return

    # if isinstance(effect, CopyPlayedShip):
    #     valid = [cid for cid in state.turn.ships_played_this_turn if cid != source_id]
    #     state.pending.append(
    #         PendingDecision(
    #             decision_type=DecisionType.CHOOSE_CARD,
    #             player=state.active_player,
    #             source_card_id=source_id,
    #             payload={"kind": "copy_played_ship", "valid_card_ids": valid, "optional": False},
    #         )
    #     )
    #     return

    # if isinstance(effect, CopyBaseUntilEndOfTurn):
    #     valid = current_player(state).bases_in_play + opponent_player(state).bases_in_play
    #     valid = [cid for cid in valid if cid != source_id]
    #     state.pending.append(
    #         PendingDecision(
    #             decision_type=DecisionType.CHOOSE_TARGET,
    #             player=state.active_player,
    #             source_card_id=source_id,
    #             payload={"kind": "copy_base_until_end", "valid_card_ids": valid, "optional": False},
    #         )
    #     )
    #     return

    if isinstance(effect, OnPlayShipGainCombat):
        return

    if isinstance(effect, Sequence):
        for sub in effect.effects:
            _apply_effect(state, card_registry, source_id, sub)
        return

    if isinstance(effect, DiscardThenDrawSameCount):
        _enqueue_choose_cards_from_zone(
            state, "discard_then_draw_same_count", current_player(state).hand, 0, effect.max_cards, source_id
        )
        return

    if isinstance(effect, MayDiscardThenDraw):
        _enqueue_choose_cards_from_zone(
            state, "may_discard_then_draw", current_player(state).hand, 0, effect.max_discards, source_id, extra={"draw_amount": effect.draw_amount}
        )
        return

    if isinstance(effect, DiscardUpToThenGainPerDiscardChoice):
        _enqueue_choose_cards_from_zone(
            state,
            "discard_up_to_then_gain_per_discard_choice",
            current_player(state).hand,
            0,
            effect.max_cards,
            source_id,
            extra={"trade_per_card": effect.trade_per_card, "combat_per_card": effect.combat_per_card},
        )
        return

    if isinstance(effect, ScrapUpToThenDrawSameCount):
        _enqueue_choose_cards_from_multiple_zones(
            state,
            "scrap_up_to_then_draw_same_count",
            current_player(state).hand,
            current_player(state).discard_pile,
            0,
            effect.max_cards,
            source_id,
        )
        return

    raise NotImplementedError(f"Unsupported effect: {type(effect).__name__}")


def _enqueue_choose_cards_from_zone(
    state: GameState,
    kind: str,
    zone_cards: list[int],
    min_cards: int,
    max_cards: int,
    source_id: int | None,
    extra: dict | None = None,
) -> None:
    valid = list(zone_cards)

    if not valid:
        return

    actual_min = min(min_cards, len(valid))
    actual_max = min(max_cards, len(valid))

    if actual_max <= 0:
        return

    payload = {
        "kind": kind,
        "selected": [],
        "remaining": actual_max,
        "min_cards": actual_min,
        "valid_card_ids": valid,
        "optional": actual_min == 0,
    }
    if extra:
        payload.update(extra)

    state.pending.append(
        PendingDecision(
            decision_type=DecisionType.CHOOSE_CARD,
            player=state.active_player,
            source_card_id=source_id,
            payload=payload,
        )
    )


def _enqueue_choose_cards_from_multiple_zones(
    state: GameState,
    kind: str,
    zone_a: list[int],
    zone_b: list[int],
    min_cards: int,
    max_cards: int,
    source_id: int | None,
) -> None:
    valid = list(zone_a) + [cid for cid in zone_b if cid not in zone_a]

    if not valid:
        return

    actual_min = min(min_cards, len(valid))
    actual_max = min(max_cards, len(valid))

    if actual_max <= 0:
        return

    state.pending.append(
        PendingDecision(
            decision_type=DecisionType.CHOOSE_CARD,
            player=state.active_player,
            source_card_id=source_id,
            payload={
                "kind": kind,
                "selected": [],
                "remaining": actual_max,
                "min_cards": actual_min,
                "valid_card_ids": valid,
                "optional": actual_min == 0,
            },
        )
    )

def _enqueue_choose_trade_row_cards(state: GameState, min_cards: int, max_cards: int, source_id: int | None) -> None:
    valid = list(state.trade_row)

    if not valid:
        return

    actual_min = min(min_cards, len(valid))
    actual_max = min(max_cards, len(valid))

    if actual_max <= 0:
        return

    state.pending.append(
        PendingDecision(
            decision_type=DecisionType.CHOOSE_CARD,
            player=state.active_player,
            source_card_id=source_id,
            payload={
                "kind": "scrap_trade_row",
                "selected": [],
                "remaining": actual_max,
                "min_cards": actual_min,
                "valid_card_ids": valid,
                "optional": actual_min == 0,
            },
        )
    )


def _enqueue_choose_target_base(state: GameState, source_id: int | None, optional: bool, free_destroy: bool) -> None:
    valid = list(opponent_player(state).bases_in_play)

    if not valid:
        return

    state.pending.append(
        PendingDecision(
            decision_type=DecisionType.CHOOSE_TARGET,
            player=state.active_player,
            source_card_id=source_id,
            payload={
                "kind": "destroy_base",
                "valid_card_ids": valid,
                "optional": optional,
                "free_destroy": free_destroy,
            },
        )
    )


def _move_played_card(state: GameState, card_registry: Mapping[str, CardDef], card_id: int,  card_def: CardDef) -> None:
    player = current_player(state)
    player.hand.remove(card_id)

    if card_def.card_type == CardType.SHIP:
        player.ships_in_play.append(card_id)
        state.turn.ships_played_this_turn.append(card_id)
    else:
        player.bases_in_play.append(card_id)
        state.turn.bases_played_this_turn.append(card_id)

    state.turn.cards_played_this_turn.append(card_id)
    state.turn.register_factions(card_def.factions)

    if card_def.card_type == CardType.SHIP:
        _apply_ship_play_passives(state, card_registry, card_id)


def can_play_card(state: GameState, card_id: int) -> bool:
    return state.turn.phase == Phase.ACTION and card_id in current_player(state).hand and not state.pending


def play_card(state: GameState, card_registry: Mapping[str, CardDef], card_id: int) -> None:
    if not can_play_card(state, card_id):
        raise ValueError("Card is not playable right now.")
    card_def = get_card_def(state, card_registry, card_id)
    _move_played_card(state, card_registry, card_id, card_def)
    _resolve_on_play_abilities(state, card_registry, card_id)


def _resolve_scrap_abilities(state: GameState, card_registry: Mapping[str, CardDef], card_id: int) -> None:
    card_def = _effective_card_def(state, card_registry, card_id)
    for ability in card_def.abilities:
        if ability.trigger != Trigger.ON_SCRAP_FROM_PLAY:
            continue
        if not _evaluate_condition(state, card_registry, ability.condition):
            continue
        for effect in ability.effects:
            _apply_effect(state, card_registry, card_id, effect)


def use_scrap_ability(state: GameState, card_registry: Mapping[str, CardDef], card_id: int) -> None:
    if state.pending:
        raise ValueError("Cannot use scrap ability while a decision is pending.")
    player = current_player(state)
    if card_id in player.ships_in_play:
        player.ships_in_play.remove(card_id)
    elif card_id in player.bases_in_play:
        player.bases_in_play.remove(card_id)
    else:
        raise ValueError("Card is not in play.")
    _move_to_scrap_heap(state, card_id)
    _resolve_scrap_abilities(state, card_registry, card_id)

def _apply_pending_choice(state: GameState, card_registry: Mapping[str, CardDef], action: str, **kwargs) -> None:
    decision = state.pending[0]

    if action == "decline":
        if not decision.payload.get("optional", False):
            raise ValueError("This decision is not optional.")
        state.pending.pop(0)
        _continue_after_pending_resolution(state, card_registry, decision, None)
        return

    if decision.decision_type == DecisionType.CHOOSE_OPTION and action == "choose_option":
        idx = kwargs["option_index"]
        options = decision.payload["options"]
        state.pending.pop(0)
        for effect in options[idx]:
            _apply_effect(state, card_registry, decision.source_card_id, effect)
        return

    if decision.decision_type in (DecisionType.CHOOSE_CARD, DecisionType.CHOOSE_TARGET) and action in ("choose_card", "choose_target"):
        chosen_id = kwargs["card_id"]

        current_valid = _current_valid_ids_for_decision(state, decision)
        decision.payload["valid_card_ids"] = current_valid

        if chosen_id not in current_valid:
            raise ValueError("Invalid choice.")

        state.pending.pop(0)
        _continue_after_pending_resolution(state, card_registry, decision, chosen_id)
        return

    raise ValueError("Invalid action for pending decision.")

def _continue_after_pending_resolution(state: GameState, card_registry: Mapping[str, CardDef], decision: PendingDecision, chosen_id: int | None) -> None:
    kind = decision.payload["kind"]
    player = current_player(state)

    if kind == "forced_discard":
        if chosen_id is None:
            raise ValueError("Forced discard cannot be declined.")
        player.hand.remove(chosen_id)
        player.discard_pile.append(chosen_id)
        remaining = decision.payload["remaining"] - 1
        valid = list(player.hand)
        if remaining > 0 and valid:
            state.pending.insert(
                0,
                PendingDecision(
                    decision_type=DecisionType.CHOOSE_CARD,
                    player=state.active_player,
                    payload={"kind": "forced_discard", "remaining": remaining, "valid_card_ids": valid, "optional": False},
                ),
            )
        return

    if kind == "scrap_hand":
        _handle_iterative_single_zone_choice(state, decision, chosen_id, player.hand, count_scrap=True)
        return

    if kind == "scrap_discard":
        _handle_iterative_single_zone_choice(state, decision, chosen_id, player.discard_pile, count_scrap=True)
        return

    if kind == "scrap_hand_or_discard":
        _handle_iterative_hand_discard_choice(state, decision, chosen_id, count_scrap=True)
        return

    if kind == "scrap_trade_row":
        if chosen_id is not None:
            state.trade_row.remove(chosen_id)
            _move_to_scrap_heap(state, chosen_id)
            decision.payload["selected"].append(chosen_id)
        _requeue_iterative_choice(state, decision, state.trade_row)
        _fill_trade_row(state)
        return

    if kind == "discard_then_draw_same_count":
        if chosen_id is not None:
            player.hand.remove(chosen_id)
            player.discard_pile.append(chosen_id)
            decision.payload["selected"].append(chosen_id)
        if _requeue_iterative_choice(state, decision, player.hand):
            return
        draw_cards(state, state.active_player, len(decision.payload["selected"]))
        return

    if kind == "may_discard_then_draw":
        if chosen_id is not None:
            player.hand.remove(chosen_id)
            player.discard_pile.append(chosen_id)
            draw_cards(state, state.active_player, decision.payload["draw_amount"])
        return

    if kind == "discard_up_to_then_gain_per_discard_choice":
        if chosen_id is not None:
            player.hand.remove(chosen_id)
            player.discard_pile.append(chosen_id)
            decision.payload["selected"].append(chosen_id)
        if _requeue_iterative_choice(state, decision, player.hand):
            return
        count = len(decision.payload["selected"])
        for _ in range(count):
            state.pending.append(
                PendingDecision(
                    decision_type=DecisionType.CHOOSE_OPTION,
                    player=state.active_player,
                    payload={
                        "kind": "supply_depot_gain_choice",
                        "options": (
                            (GainTrade(decision.payload["trade_per_card"]),),
                            (GainCombat(decision.payload["combat_per_card"]),),
                        ),
                    },
                )
            )
        return

    if kind == "supply_depot_gain_choice":
        return

    if kind == "scrap_up_to_then_draw_same_count":
        if chosen_id is not None:
            if chosen_id in player.hand:
                player.hand.remove(chosen_id)
            else:
                player.discard_pile.remove(chosen_id)
            _move_to_scrap_heap(state, chosen_id)
            state.turn.scrapped_from_hand_or_discard_this_turn += 1
            decision.payload["selected"].append(chosen_id)
        valid = list(player.hand) + [cid for cid in player.discard_pile if cid not in player.hand]
        if _requeue_iterative_choice(state, decision, valid):
            return
        draw_cards(state, state.active_player, len(decision.payload["selected"]))
        return

    if kind == "destroy_base":
        if chosen_id is not None:
            _destroy_base_no_cost(state, chosen_id)
        return

    if kind == "acquire_free":
        if chosen_id is not None:
            _acquire_existing_card(state, card_registry, chosen_id, destination_override=decision.payload["destination"])
        return

    raise NotImplementedError(f"Unhandled pending kind: {kind}")


def _handle_iterative_single_zone_choice(state: GameState, decision: PendingDecision, chosen_id: int | None, zone: list[int], count_scrap: bool) -> None:
    if chosen_id is not None:
        zone.remove(chosen_id)
        _move_to_scrap_heap(state, chosen_id)
        if count_scrap:
            state.turn.scrapped_from_hand_or_discard_this_turn += 1
        decision.payload["selected"].append(chosen_id)
    _requeue_iterative_choice(state, decision, zone)


def _handle_iterative_hand_discard_choice(state: GameState, decision: PendingDecision, chosen_id: int | None, count_scrap: bool) -> None:
    player = current_player(state)
    if chosen_id is not None:
        if chosen_id in player.hand:
            player.hand.remove(chosen_id)
        else:
            player.discard_pile.remove(chosen_id)
        _move_to_scrap_heap(state, chosen_id)
        if count_scrap:
            state.turn.scrapped_from_hand_or_discard_this_turn += 1
        decision.payload["selected"].append(chosen_id)
    valid = list(player.hand) + [cid for cid in player.discard_pile if cid not in player.hand]
    _requeue_iterative_choice(state, decision, valid)


def _requeue_iterative_choice(state: GameState, decision: PendingDecision, valid_now: list[int]) -> bool:
    decision.payload["remaining"] -= 1
    decision.payload["valid_card_ids"] = list(valid_now)
    decision.payload["optional"] = len(decision.payload["selected"]) >= decision.payload["min_cards"]

    if decision.payload["remaining"] > 0 and valid_now:
        state.pending.insert(0, decision)
        return True
    return False


def _default_acquire_destination(state: GameState, card_def: CardDef) -> AcquireDestination:
    for modifier in list(state.turn.pending_acquire_modifiers):
        if modifier.card_type is None or modifier.card_type == card_def.card_type:
            modifier.uses -= 1
            destination = modifier.destination
            if modifier.uses <= 0:
                state.turn.pending_acquire_modifiers.remove(modifier)
            return destination
    return AcquireDestination.DISCARD


def _place_acquired_card(state: GameState, card_registry: Mapping[str, CardDef], card_id: int, destination: AcquireDestination) -> None:
    player = current_player(state)
    card_def = get_card_def(state, card_registry, card_id)
    if destination == AcquireDestination.DISCARD:
        player.discard_pile.append(card_id)
    elif destination == AcquireDestination.TOP_OF_DECK:
        player.draw_pile.append(card_id)
    elif destination == AcquireDestination.HAND:
        player.hand.append(card_id)
    elif destination == AcquireDestination.DIRECT_TO_PLAY:
        if card_def.card_type != CardType.BASE:
            raise ValueError("Only bases can be put directly into play.")
        player.bases_in_play.append(card_id)
    else:
        raise ValueError("Unknown acquire destination.")


def _acquire_existing_card(state: GameState, card_registry: Mapping[str, CardDef], card_id: int, destination_override: AcquireDestination | None = None) -> None:
    if card_id in state.trade_row:
        state.trade_row.remove(card_id)
        _fill_trade_row(state)
    card_def = get_card_def(state, card_registry, card_id)
    destination = destination_override or _default_acquire_destination(state, card_def)
    _place_acquired_card(state, card_registry, card_id, destination)
    _resolve_on_acquire_abilities(state, card_registry, card_id)


def buy_trade_row_card(state: GameState, card_registry: Mapping[str, CardDef], card_id: int) -> None:
    if state.turn.phase != Phase.BUY or state.pending:
        raise ValueError("Cannot buy right now.")
    if card_id not in state.trade_row:
        raise ValueError("Card is not in trade row.")
    card_def = get_card_def(state, card_registry, card_id)
    if card_def.cost is None or state.turn.trade < card_def.cost:
        raise ValueError("Cannot afford card.")
    state.turn.trade -= card_def.cost
    _acquire_existing_card(state, card_registry, card_id)


def buy_explorer(state: GameState, card_registry: Mapping[str, CardDef]) -> None:
    if state.turn.phase != Phase.BUY or state.pending:
        raise ValueError("Cannot buy explorer right now.")
    if state.turn.trade < 2 or state.explorer_pile_count <= 0:
        raise ValueError("Cannot buy explorer.")
    state.turn.trade -= 2
    state.explorer_pile_count -= 1
    explorer_id = state.new_instance("explorer", owner=state.active_player)
    _acquire_existing_card(state, card_registry, explorer_id)


def _opponent_outposts(state: GameState, card_registry: Mapping[str, CardDef]) -> list[int]:
    result = []
    for card_id in opponent_player(state).bases_in_play:
        card_def = _effective_card_def(state, card_registry, card_id)
        if getattr(card_def, "is_outpost", False):
            result.append(card_id)
    return result


def attack_player(state: GameState, card_registry: Mapping[str, CardDef], amount: int | None = None) -> None:
    if state.turn.phase != Phase.ATTACK or state.pending:
        raise ValueError("Cannot attack right now.")
    if _opponent_outposts(state, card_registry):
        raise ValueError("Cannot attack player while opponent controls an outpost.")
    dmg = state.turn.combat if amount is None else amount
    if dmg <= 0 or dmg > state.turn.combat:
        raise ValueError("Invalid damage amount.")
    opponent_player(state).authority -= dmg
    state.turn.combat -= dmg
    if opponent_player(state).authority <= 0:
        state.winner = state.active_player


def attack_base(state: GameState, card_registry: Mapping[str, CardDef], base_id: int) -> None:
    if state.turn.phase != Phase.ATTACK or state.pending:
        raise ValueError("Cannot attack right now.")
    if base_id not in opponent_player(state).bases_in_play:
        raise ValueError("Target is not an enemy base.")
    outposts = _opponent_outposts(state, card_registry)
    if outposts and base_id not in outposts:
        raise ValueError("Must attack outposts first.")
    base_def = _effective_card_def(state, card_registry, base_id)
    if base_def.defense is None or state.turn.combat < base_def.defense:
        raise ValueError("Not enough combat.")
    state.turn.combat -= base_def.defense
    _destroy_base_no_cost(state, base_id)


def _destroy_base_no_cost(state: GameState, base_id: int) -> None:
    _remove_from_list(opponent_player(state).bases_in_play, base_id)
    _move_to_scrap_heap(state, base_id)


def end_action_phase(state: GameState) -> None:
    if state.pending or state.turn.phase != Phase.ACTION:
        raise ValueError("Cannot end action phase.")
    state.turn.phase = Phase.BUY


def end_buy_phase(state: GameState) -> None:
    if state.pending or state.turn.phase != Phase.BUY:
        raise ValueError("Cannot end buy phase.")
    state.turn.phase = Phase.ATTACK


def end_attack_phase(state: GameState) -> None:
    if state.pending or state.turn.phase != Phase.ATTACK:
        raise ValueError("Cannot end attack phase.")
    state.turn.phase = Phase.CLEANUP


def cleanup_and_pass_turn(state: GameState) -> None:
    if state.pending or state.turn.phase != Phase.CLEANUP:
        raise ValueError("Cannot cleanup right now.")

    player = current_player(state)
    player.discard_pile.extend(player.hand)
    player.hand.clear()

    player.discard_pile.extend(player.ships_in_play)
    player.ships_in_play.clear()

    draw_cards(state, state.active_player, 5)

    state.active_player = 1 - state.active_player
    state.turn_number += 1
    _start_turn(state)

def _current_valid_ids_for_decision(state: GameState, decision: PendingDecision) -> list[int]:
    kind = decision.payload["kind"]
    player = current_player(state)

    if kind in {
        "scrap_hand",
        "discard_then_draw_same_count",
        "may_discard_then_draw",
        "discard_up_to_then_gain_per_discard_choice",
        "forced_discard",
    }:
        return list(player.hand)

    if kind == "scrap_discard":
        return list(player.discard_pile)

    if kind in {"scrap_hand_or_discard", "scrap_up_to_then_draw_same_count"}:
        return list(player.hand) + [cid for cid in player.discard_pile if cid not in player.hand]

    if kind == "scrap_trade_row":
        return list(state.trade_row)

    if kind == "destroy_base":
        return list(opponent_player(state).bases_in_play)

    if kind == "acquire_free":
        # original payload is the allowed subset by cost/type; keep only those still in trade row
        original_valid = decision.payload.get("valid_card_ids", [])
        return [cid for cid in original_valid if cid in state.trade_row]

    return list(decision.payload.get("valid_card_ids", []))


def apply_action(state: GameState, card_registry: Mapping[str, CardDef], action: str, **kwargs) -> None:

    if state.pending:
        _apply_pending_choice(state, card_registry, action, **kwargs)
        return

    if action == "play_card":
        play_card(state, card_registry, kwargs["card_id"])
    elif action == "use_scrap_ability":
        use_scrap_ability(state, card_registry, kwargs["card_id"])
    elif action == "buy_trade_row_card":
        buy_trade_row_card(state, card_registry, kwargs["card_id"])
    elif action == "buy_explorer":
        buy_explorer(state, card_registry)
    elif action == "attack_player":
        attack_player(state, card_registry, kwargs.get("amount"))
    elif action == "attack_base":
        attack_base(state, card_registry, kwargs["card_id"])
    elif action == "end_action_phase":
        end_action_phase(state)
    elif action == "end_buy_phase":
        end_buy_phase(state)
    elif action == "end_attack_phase":
        end_attack_phase(state)
    elif action == "cleanup_and_pass_turn":
        cleanup_and_pass_turn(state)
    else:
        raise ValueError(f"Unknown action: {action}")


