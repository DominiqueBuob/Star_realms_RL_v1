import pytest
import pytest

from data.colony_wars_cards import CARDS
from data.enums import CardType, Phase
from data.legal_actions import get_legal_actions
from data.rules import apply_action, get_card_def
from data.setup import create_game


def add_card_to_hand(state, player_idx, card_def_id):
    instance_id = state.new_instance(card_def_id, owner=player_idx)
    state.players[player_idx].hand.append(instance_id)
    return instance_id


def add_card_to_discard(state, player_idx, card_def_id):
    instance_id = state.new_instance(card_def_id, owner=player_idx)
    state.players[player_idx].discard_pile.append(instance_id)
    return instance_id


def add_base_to_play(state, player_idx, card_def_id):
    instance_id = state.new_instance(card_def_id, owner=player_idx)
    state.players[player_idx].bases_in_play.append(instance_id)
    return instance_id


def clear_hand(state, player_idx):
    state.players[player_idx].hand.clear()


def clear_trade_row(state):
    state.trade_row.clear()

def test_destroy_base_effect_with_no_targets_does_not_deadlock():
    state = create_game(CARDS, seed=1)
    clear_hand(state, state.active_player)

    mech_id = add_card_to_hand(state, state.active_player, "missile_mech")

    apply_action(state, CARDS, "play_card", card_id=mech_id)

    actions = get_legal_actions(state, CARDS)

    assert not state.pending
    assert len(actions) > 0
    assert {"type": "end_action_phase"} in actions

def test_command_ship_ally_destroy_base_with_no_targets_does_not_deadlock():
    state = create_game(CARDS, seed=1)
    clear_hand(state, state.active_player)

    shuttle_id = add_card_to_hand(state, state.active_player, "federation_shuttle")
    command_ship_id = add_card_to_hand(state, state.active_player, "command_ship")

    apply_action(state, CARDS, "play_card", card_id=shuttle_id)
    apply_action(state, CARDS, "play_card", card_id=command_ship_id)

    actions = get_legal_actions(state, CARDS)

    assert not state.pending
    assert len(actions) > 0
    assert {"type": "end_action_phase"} in actions
    

def test_forced_discard_with_empty_hand_does_not_deadlock():
    state = create_game(CARDS, seed=1)

    player = state.players[state.active_player]
    player.hand.clear()
    player.forced_discards_next_turn = 1

    from data.rules import _start_turn
    _start_turn(state)

    actions = get_legal_actions(state, CARDS)

    assert not state.pending
    assert len(actions) > 0

def test_forced_discard_with_partial_hand_only_discards_available_cards():
    state = create_game(CARDS, seed=1)

    player = state.players[state.active_player]
    player.hand.clear()
    scout_id = state.new_instance("scout", owner=state.active_player)
    player.hand.append(scout_id)
    player.forced_discards_next_turn = 3

    from data.rules import _start_turn
    _start_turn(state)

    assert len(state.pending) == 1
    decision = state.pending[0]
    assert decision.payload["kind"] == "forced_discard"
    assert decision.payload["remaining"] == 1
    assert decision.payload["valid_card_ids"] == [scout_id]

def test_mandatory_scrap_from_empty_hand_does_not_deadlock():
    state = create_game(CARDS, seed=1)
    clear_hand(state, state.active_player)

    oracle_id = add_card_to_hand(state, state.active_player, "the_oracle")
    clear_hand(state, state.active_player)
    state.players[state.active_player].hand.append(oracle_id)

    apply_action(state, CARDS, "play_card", card_id=oracle_id)

    actions = get_legal_actions(state, CARDS)

    assert not state.pending
    assert {"type": "end_action_phase"} in actions

