from __future__ import annotations

from data.card_defs import CardDef
from data.enums import DecisionType, Phase, Trigger
from data.state import GameState
from data.rules import current_player, opponent_player, get_card_def, _effective_card_def
from typing import Mapping

def _has_scrap_ability(card_def: CardDef) -> bool:
    return any(ability.trigger == Trigger.ON_SCRAP_FROM_PLAY for ability in card_def.abilities)


def _pending_actions(state: GameState) -> list[dict]:
    decision = state.pending[0]
    payload = decision.payload
    actions: list[dict] = []

    if decision.decision_type == DecisionType.CHOOSE_OPTION:
        options = payload["options"]
        for i in range(len(options)):
            actions.append({"type": "choose_option", "option_index": i})

    elif decision.decision_type in (DecisionType.CHOOSE_CARD, DecisionType.CHOOSE_TARGET):
        for card_id in payload.get("valid_card_ids", []):
            actions.append({"type": "choose_card", "card_id": card_id})
        if payload.get("optional", False):
            actions.append({"type": "decline"})

    return actions


def _action_phase_actions(state: GameState, card_registry: dict[str, CardDef]) -> list[dict]:
    actions: list[dict] = []
    player = current_player(state)

    for card_id in player.hand:
        actions.append({"type": "play_card", "card_id": card_id})

    for card_id in player.ships_in_play + player.bases_in_play:
        card_def = _effective_card_def(state, card_registry, card_id)
        if _has_scrap_ability(card_def):
            actions.append({"type": "use_scrap_ability", "card_id": card_id})

    actions.append({"type": "end_action_phase"})
    return actions


def _buy_phase_actions(state: GameState, card_registry: dict[str, CardDef]) -> list[dict]:
    actions: list[dict] = []

    for card_id in state.trade_row:
        card_def = get_card_def(state, card_registry, card_id)
        if card_def.cost is not None and card_def.cost <= state.turn.trade:
            actions.append({"type": "buy_trade_row_card", "card_id": card_id})

    if state.explorer_pile_count > 0 and state.turn.trade >= 2:
        actions.append({"type": "buy_explorer"})

    actions.append({"type": "end_buy_phase"})
    return actions


def _opponent_outposts(state: GameState, card_registry: dict[str, CardDef]) -> list[int]:
    outposts: list[int] = []
    for card_id in opponent_player(state).bases_in_play:
        card_def = _effective_card_def(state, card_registry, card_id)
        if getattr(card_def, "is_outpost", False):
            outposts.append(card_id)
    return outposts


def _attack_phase_actions(state: GameState, card_registry: dict[str, CardDef]) -> list[dict]:
    actions: list[dict] = []
    if state.turn.combat > 0:
        outposts = _opponent_outposts(state, card_registry)
        candidate_bases = outposts if outposts else list(opponent_player(state).bases_in_play)

        for card_id in candidate_bases:
            card_def = _effective_card_def(state, card_registry, card_id)
            defense = card_def.defense
            if defense is not None and defense <= state.turn.combat:
                actions.append({"type": "attack_base", "card_id": card_id})

        if not outposts:
            actions.append({"type": "attack_player"})

    actions.append({"type": "end_attack_phase"})
    return actions


def get_legal_actions(state: GameState, card_registry: dict[str, CardDef]) -> list[dict]:
    if state.winner is not None:
        return []

    if state.pending:
        return _pending_actions(state)

    if state.turn.phase == Phase.ACTION:
        return _action_phase_actions(state, card_registry)

    if state.turn.phase == Phase.BUY:
        return _buy_phase_actions(state, card_registry)

    if state.turn.phase == Phase.ATTACK:
        return _attack_phase_actions(state, card_registry)

    if state.turn.phase == Phase.CLEANUP:
        return [{"type": "cleanup_and_pass_turn"}]

    raise ValueError(f"Unknown phase: {state.turn.phase}")