import pytest

from data.colony_wars_cards import CARDS
from data.legal_actions import get_legal_actions
from data.rules import apply_action
from data.setup import create_game


def add_card_to_hand(state, player_idx, card_def_id):
    instance_id = state.new_instance(card_def_id, owner=player_idx)
    state.players[player_idx].hand.append(instance_id)
    return instance_id


def clear_hand(state, player_idx):
    state.players[player_idx].hand.clear()


def test_the_oracle_with_empty_hand_does_not_create_dead_pending_choice():
    state = create_game(CARDS, seed=1)
    clear_hand(state, state.active_player)

    oracle_id = add_card_to_hand(state, state.active_player, "the_oracle")

    apply_action(state, CARDS, "play_card", card_id=oracle_id)

    actions = get_legal_actions(state, CARDS)

    assert not state.pending
    assert len(actions) > 0
    assert {"type": "end_action_phase"} in actions

def test_machine_base_draws_then_requires_scrap_from_hand():
    state = create_game(CARDS, seed=1)
    clear_hand(state, state.active_player)

    base_id = add_card_to_hand(state, state.active_player, "machine_base")
    drawn_id = state.new_instance("scout", owner=state.active_player)
    state.players[state.active_player].draw_pile = [drawn_id]

    apply_action(state, CARDS, "play_card", card_id=base_id)

    assert len(state.pending) == 1
    decision = state.pending[0]
    assert decision.payload["kind"] == "scrap_hand"
    assert decision.payload["valid_card_ids"] == [drawn_id]
    assert decision.payload["min_cards"] == 1

def test_machine_base_can_resolve_scrap_after_draw():
    state = create_game(CARDS, seed=1)
    clear_hand(state, state.active_player)

    base_id = add_card_to_hand(state, state.active_player, "machine_base")
    drawn_id = state.new_instance("scout", owner=state.active_player)
    state.players[state.active_player].draw_pile = [drawn_id]

    apply_action(state, CARDS, "play_card", card_id=base_id)
    apply_action(state, CARDS, "choose_card", card_id=drawn_id)

    assert drawn_id in state.scrap_heap
    assert not state.pending

def test_mandatory_scrap_from_empty_hand_currently_reproduces_deadlock_shape():
    state = create_game(CARDS, seed=1)
    clear_hand(state, state.active_player)

    oracle_id = add_card_to_hand(state, state.active_player, "the_oracle")

    apply_action(state, CARDS, "play_card", card_id=oracle_id)

    if state.pending:
        decision = state.pending[0]
        assert decision.payload["kind"] == "scrap_hand"
        assert decision.payload["valid_card_ids"] == []
        assert decision.payload["min_cards"] == 1