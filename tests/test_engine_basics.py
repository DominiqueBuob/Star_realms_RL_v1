import pytest
from typing import Mapping

from data.colony_wars_cards import CARDS
from data.enums import Phase
from data.legal_actions import get_legal_actions
from data.rules import apply_action
from data.setup import create_game
from data.enums import CardType
from data.rules import get_card_def


def find_card_in_hand(state, player_idx, card_registry, card_def_id):
    player = state.players[player_idx]
    for instance_id in player.hand:
        if state.cards[instance_id].card_def_id == card_def_id:
            return instance_id
    return None


def add_card_to_hand(state, player_idx, card_def_id):
    instance_id = state.new_instance(card_def_id, owner=player_idx)
    state.players[player_idx].hand.append(instance_id)
    return instance_id


def add_base_to_play(state, player_idx, card_def_id):
    instance_id = state.new_instance(card_def_id, owner=player_idx)
    state.players[player_idx].bases_in_play.append(instance_id)
    return instance_id


def test_initial_legal_actions_contains_playable_hand_cards_and_end_phase():
    state = create_game(CARDS, seed=1)
    actions = get_legal_actions(state, CARDS)

    play_actions = [a for a in actions if a["type"] == "play_card"]
    assert len(play_actions) == 5
    assert {"type": "end_action_phase"} in actions


def test_playing_scout_adds_trade():
    state = create_game(CARDS, seed=1)
    scout_id = add_card_to_hand(state, state.active_player, "scout")

    apply_action(state, CARDS, "play_card", card_id=scout_id)

    assert state.turn.trade == 1
    assert scout_id in state.players[state.active_player].ships_in_play
    assert scout_id not in state.players[state.active_player].hand


def test_playing_viper_adds_combat():
    state = create_game(CARDS, seed=1)
    viper_id = add_card_to_hand(state, state.active_player, "viper")

    apply_action(state, CARDS, "play_card", card_id=viper_id)

    assert state.turn.combat == 1


def test_end_action_phase_moves_to_buy():
    state = create_game(CARDS, seed=1)

    apply_action(state, CARDS, "end_action_phase")

    assert state.turn.phase == Phase.BUY


def test_buy_explorer_when_affordable():
    state = create_game(CARDS, seed=1)
    state.turn.phase = Phase.BUY
    state.turn.trade = 2
    before = state.explorer_pile_count

    apply_action(state, CARDS, "buy_explorer")

    assert state.explorer_pile_count == before - 1
    assert state.turn.trade == 0
    assert any(state.cards[cid].card_def_id == "explorer" for cid in state.players[state.active_player].discard_pile)


def test_blob_ally_triggers_after_first_blob_played():
    state = create_game(CARDS, seed=1)
    fighter_id = add_card_to_hand(state, state.active_player, "blob_fighter")
    predator_id = add_card_to_hand(state, state.active_player, "predator")

    apply_action(state, CARDS, "play_card", card_id=fighter_id)
    hand_size_before = len(state.players[state.active_player].hand)
    apply_action(state, CARDS, "play_card", card_id=predator_id)

    assert state.turn.combat >= 7
    assert len(state.players[state.active_player].hand) == hand_size_before


def test_scrap_from_play_action_is_legal_for_explorer_in_play():
    state = create_game(CARDS, seed=1)
    explorer_id = add_card_to_hand(state, state.active_player, "explorer")
    apply_action(state, CARDS, "play_card", card_id=explorer_id)

    actions = get_legal_actions(state, CARDS)

    assert {"type": "use_scrap_ability", "card_id": explorer_id} in actions


def test_using_explorer_scrap_ability_moves_it_to_scrap_heap_and_gains_combat():
    state = create_game(CARDS, seed=1)
    explorer_id = add_card_to_hand(state, state.active_player, "explorer")
    apply_action(state, CARDS, "play_card", card_id=explorer_id)

    trade_before = state.turn.trade
    apply_action(state, CARDS, "use_scrap_ability", card_id=explorer_id)

    assert explorer_id in state.scrap_heap
    assert explorer_id not in state.players[state.active_player].ships_in_play
    assert state.turn.trade == trade_before
    assert state.turn.combat == 2


def test_outpost_blocks_attacking_player():
    state = create_game(CARDS, seed=1)
    state.turn.phase = Phase.ATTACK
    state.turn.combat = 10

    outpost_id = add_base_to_play(state, 1 - state.active_player, "battle_station")

    actions = get_legal_actions(state, CARDS)

    assert {"type": "attack_player"} not in actions
    assert {"type": "attack_base", "card_id": outpost_id} in actions


def test_attacking_outpost_removes_it_and_spends_combat():
    state = create_game(CARDS, seed=1)
    state.turn.phase = Phase.ATTACK
    state.turn.combat = 10

    outpost_id = add_base_to_play(state, 1 - state.active_player, "battle_station")

    apply_action(state, CARDS, "attack_base", card_id=outpost_id)

    assert outpost_id not in state.players[1 - state.active_player].bases_in_play
    assert outpost_id in state.scrap_heap
    assert state.turn.combat == 5


def test_choose_one_creates_pending_decision():
    state = create_game(CARDS, seed=1)
    patrol_mech_id = add_card_to_hand(state, state.active_player, "patrol_mech")

    apply_action(state, CARDS, "play_card", card_id=patrol_mech_id)

    assert len(state.pending) == 1
    actions = get_legal_actions(state, CARDS)
    choose_actions = [a for a in actions if a["type"] == "choose_option"]
    assert len(choose_actions) == 2


def test_choose_one_resolution_changes_resources():
    state = create_game(CARDS, seed=1)
    patrol_mech_id = add_card_to_hand(state, state.active_player, "patrol_mech")

    apply_action(state, CARDS, "play_card", card_id=patrol_mech_id)
    apply_action(state, CARDS, "choose_option", option_index=0)

    assert state.turn.trade == 3
    assert state.turn.combat == 0

def test_on_acquire_puts_warning_beacon_into_hand_if_machine_cult_played():
    state = create_game(CARDS, seed=1)

    trade_bot_id = add_card_to_hand(state, state.active_player, "trade_bot")
    apply_action(state, CARDS, "play_card", card_id=trade_bot_id)

    apply_action(state, CARDS, "decline")
    apply_action(state, CARDS, "end_action_phase")

    state.turn.trade = 99

    beacon_id = None
    for cid in state.trade_row:
        if state.cards[cid].card_def_id == "warning_beacon":
            beacon_id = cid
            break
    if beacon_id is None:
        beacon_id = state.new_instance("warning_beacon", owner=None)
        state.trade_row[0] = beacon_id

    apply_action(state, CARDS, "buy_trade_row_card", card_id=beacon_id)

    assert beacon_id in state.players[state.active_player].hand


def test_next_acquire_destination_top_of_deck():
    state = create_game(CARDS, seed=1)
    office_id = add_card_to_hand(state, state.active_player, "central_office")

    apply_action(state, CARDS, "play_card", card_id=office_id)
    apply_action(state, CARDS, "end_action_phase")

    state.turn.trade = 99

    target_id = None
    for cid in state.trade_row:
        if get_card_def(state, CARDS, cid).card_type == CardType.SHIP:
            target_id = cid
            break

    if target_id is None:
        target_id = state.new_instance("trade_hauler", owner=None)
        state.trade_row[0] = target_id

    apply_action(state, CARDS, "buy_trade_row_card", card_id=target_id)

    assert state.players[state.active_player].draw_pile[-1] == target_id