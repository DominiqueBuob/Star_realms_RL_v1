import pytest

from data.colony_wars_cards import CARDS
from data.enums import DecisionType
from data.legal_actions import get_legal_actions
from data.pending import PendingDecision
from data.rules import apply_action
from data.setup import create_game


def add_card_to_hand(state, player_idx, card_def_id):
    instance_id = state.new_instance(card_def_id, owner=player_idx)
    state.players[player_idx].hand.append(instance_id)
    return instance_id


def add_card_to_discard(state, player_idx, card_def_id):
    instance_id = state.new_instance(card_def_id, owner=player_idx)
    state.players[player_idx].discard_pile.append(instance_id)
    return instance_id


def clear_hand(state, player_idx):
    state.players[player_idx].hand.clear()


def test_stale_scrap_hand_or_discard_pending_is_not_offered_as_legal_action():
    state = create_game(CARDS, seed=1)
    clear_hand(state, state.active_player)

    stale_id = state.new_instance("scout", owner=state.active_player)

    state.pending.append(
        PendingDecision(
            decision_type=DecisionType.CHOOSE_CARD,
            player=state.active_player,
            source_card_id=None,
            payload={
                "kind": "scrap_hand_or_discard",
                "selected": [],
                "remaining": 1,
                "min_cards": 0,
                "valid_card_ids": [stale_id],
                "optional": True,
            },
        )
    )

    actions = get_legal_actions(state, CARDS)

    assert {"type": "choose_card", "card_id": stale_id} not in actions
    assert {"type": "decline"} in actions


def test_stale_scrap_hand_or_discard_choice_raises_invalid_choice_not_list_remove_error():
    state = create_game(CARDS, seed=1)
    clear_hand(state, state.active_player)

    stale_id = state.new_instance("scout", owner=state.active_player)

    state.pending.append(
        PendingDecision(
            decision_type=DecisionType.CHOOSE_CARD,
            player=state.active_player,
            source_card_id=None,
            payload={
                "kind": "scrap_hand_or_discard",
                "selected": [],
                "remaining": 1,
                "min_cards": 0,
                "valid_card_ids": [stale_id],
                "optional": True,
            },
        )
    )

    with pytest.raises(ValueError, match="Invalid choice"):
        apply_action(state, CARDS, "choose_card", card_id=stale_id)


def test_iterative_scrap_hand_or_discard_does_not_reoffer_already_scrapped_card():
    state = create_game(CARDS, seed=1)
    clear_hand(state, state.active_player)

    wrecker_id = add_card_to_hand(state, state.active_player, "the_wrecker")
    hand_card = add_card_to_hand(state, state.active_player, "scout")
    discard_card = add_card_to_discard(state, state.active_player, "viper")

    apply_action(state, CARDS, "play_card", card_id=wrecker_id)
    apply_action(state, CARDS, "choose_card", card_id=hand_card)

    actions = get_legal_actions(state, CARDS)

    assert {"type": "choose_card", "card_id": hand_card} not in actions
    assert {"type": "choose_card", "card_id": discard_card} in actions


def test_stale_destroy_base_pending_is_not_offered_as_legal_action():
    state = create_game(CARDS, seed=1)

    stale_base_id = state.new_instance("trading_post", owner=1 - state.active_player)

    state.pending.append(
        PendingDecision(
            decision_type=DecisionType.CHOOSE_TARGET,
            player=state.active_player,
            source_card_id=None,
            payload={
                "kind": "destroy_base",
                "valid_card_ids": [stale_base_id],
                "optional": True,
                "free_destroy": True,
            },
        )
    )

    actions = get_legal_actions(state, CARDS)

    assert {"type": "choose_card", "card_id": stale_base_id} not in actions
    assert {"type": "decline"} in actions