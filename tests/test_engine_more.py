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


def test_pending_decline_is_legal_after_trade_bot():
    state = create_game(CARDS, seed=1)
    trade_bot_id = add_card_to_hand(state, state.active_player, "trade_bot")

    apply_action(state, CARDS, "play_card", card_id=trade_bot_id)
    actions = get_legal_actions(state, CARDS)

    assert {"type": "decline"} in actions
    assert any(a["type"] == "choose_card" for a in actions)


def test_declining_trade_bot_scrap_clears_pending():
    state = create_game(CARDS, seed=1)
    trade_bot_id = add_card_to_hand(state, state.active_player, "trade_bot")

    apply_action(state, CARDS, "play_card", card_id=trade_bot_id)
    assert state.pending

    apply_action(state, CARDS, "decline")

    assert state.pending == []


def test_trade_bot_can_scrap_card_from_hand():
    state = create_game(CARDS, seed=1)
    clear_hand(state, state.active_player)

    trade_bot_id = add_card_to_hand(state, state.active_player, "trade_bot")
    scout_id = add_card_to_hand(state, state.active_player, "scout")

    apply_action(state, CARDS, "play_card", card_id=trade_bot_id)
    apply_action(state, CARDS, "choose_card", card_id=scout_id)

    assert scout_id in state.scrap_heap
    assert scout_id not in state.players[state.active_player].hand
    assert state.turn.scrapped_from_hand_or_discard_this_turn == 1


def test_repair_bot_can_scrap_card_from_discard():
    state = create_game(CARDS, seed=1)
    clear_hand(state, state.active_player)

    repair_bot_id = add_card_to_hand(state, state.active_player, "repair_bot")
    scout_id = add_card_to_discard(state, state.active_player, "scout")

    apply_action(state, CARDS, "play_card", card_id=repair_bot_id)
    apply_action(state, CARDS, "choose_card", card_id=scout_id)

    assert scout_id in state.scrap_heap
    assert scout_id not in state.players[state.active_player].discard_pile
    assert state.turn.trade == 2
    assert state.turn.scrapped_from_hand_or_discard_this_turn == 1


def test_battle_pod_can_scrap_trade_row_card():
    state = create_game(CARDS, seed=1)
    clear_hand(state, state.active_player)
    clear_trade_row(state)

    battle_pod_id = add_card_to_hand(state, state.active_player, "battle_pod")
    target_id = state.new_instance("trade_hauler", owner=None)
    state.trade_row.append(target_id)

    apply_action(state, CARDS, "play_card", card_id=battle_pod_id)
    apply_action(state, CARDS, "choose_card", card_id=target_id)

    assert target_id in state.scrap_heap
    assert target_id not in state.trade_row
    assert state.turn.combat == 4


def test_battle_pod_decline_trade_row_scrap_keeps_card():
    state = create_game(CARDS, seed=1)
    clear_hand(state, state.active_player)
    clear_trade_row(state)

    battle_pod_id = add_card_to_hand(state, state.active_player, "battle_pod")
    target_id = state.new_instance("trade_hauler", owner=None)
    state.trade_row.append(target_id)

    apply_action(state, CARDS, "play_card", card_id=battle_pod_id)
    apply_action(state, CARDS, "decline")

    assert target_id not in state.scrap_heap
    assert target_id in state.trade_row


def test_battle_station_scrap_ability_gains_combat():
    state = create_game(CARDS, seed=1)
    base_id = add_base_to_play(state, state.active_player, "battle_station")

    apply_action(state, CARDS, "use_scrap_ability", card_id=base_id)

    assert state.turn.combat == 5
    assert base_id in state.scrap_heap
    assert base_id not in state.players[state.active_player].bases_in_play


def test_patrol_mech_choose_trade_branch():
    state = create_game(CARDS, seed=1)
    clear_hand(state, state.active_player)
    mech_id = add_card_to_hand(state, state.active_player, "patrol_mech")

    apply_action(state, CARDS, "play_card", card_id=mech_id)
    apply_action(state, CARDS, "choose_option", option_index=0)

    assert state.turn.trade == 3
    assert state.turn.combat == 0


def test_patrol_mech_choose_combat_branch():
    state = create_game(CARDS, seed=1)
    clear_hand(state, state.active_player)
    mech_id = add_card_to_hand(state, state.active_player, "patrol_mech")

    apply_action(state, CARDS, "play_card", card_id=mech_id)
    apply_action(state, CARDS, "choose_option", option_index=1)

    assert state.turn.trade == 0
    assert state.turn.combat == 5


def test_recycling_station_choose_trade_branch():
    state = create_game(CARDS, seed=1)
    base_id = add_card_to_hand(state, state.active_player, "recycling_station")

    apply_action(state, CARDS, "play_card", card_id=base_id)
    apply_action(state, CARDS, "choose_option", option_index=0)

    assert state.turn.trade == 1


def test_recycling_station_discard_then_draw_same_count():
    state = create_game(CARDS, seed=1)
    clear_hand(state, state.active_player)

    base_id = add_card_to_hand(state, state.active_player, "recycling_station")
    scout1 = add_card_to_hand(state, state.active_player, "scout")
    scout2 = add_card_to_hand(state, state.active_player, "scout")
    state.players[state.active_player].draw_pile = [
        state.new_instance("viper", owner=state.active_player),
        state.new_instance("explorer", owner=state.active_player),
    ]

    apply_action(state, CARDS, "play_card", card_id=base_id)
    apply_action(state, CARDS, "choose_option", option_index=1)
    apply_action(state, CARDS, "choose_card", card_id=scout1)
    apply_action(state, CARDS, "choose_card", card_id=scout2)

    hand_def_ids = [state.cards[cid].card_def_id for cid in state.players[state.active_player].hand]
    assert "viper" in hand_def_ids
    assert "explorer" in hand_def_ids
    assert scout1 in state.players[state.active_player].discard_pile
    assert scout2 in state.players[state.active_player].discard_pile


def test_central_office_only_moves_ship_to_top_of_deck():
    state = create_game(CARDS, seed=1)
    clear_hand(state, state.active_player)
    clear_trade_row(state)

    office_id = add_card_to_hand(state, state.active_player, "central_office")
    base_to_buy = state.new_instance("trading_post", owner=None)
    state.trade_row.append(base_to_buy)

    apply_action(state, CARDS, "play_card", card_id=office_id)
    apply_action(state, CARDS, "end_action_phase")
    state.turn.trade = 99
    apply_action(state, CARDS, "buy_trade_row_card", card_id=base_to_buy)

    assert base_to_buy in state.players[state.active_player].discard_pile
    assert state.players[state.active_player].draw_pile[-1] != base_to_buy


def test_freighter_moves_next_ship_to_top_of_deck_with_trade_federation_ally():
    state = create_game(CARDS, seed=1)
    clear_hand(state, state.active_player)
    clear_trade_row(state)

    shuttle_id = add_card_to_hand(state, state.active_player, "federation_shuttle")
    freighter_id = add_card_to_hand(state, state.active_player, "freighter")
    target_ship = state.new_instance("trade_hauler", owner=None)
    state.trade_row.append(target_ship)

    apply_action(state, CARDS, "play_card", card_id=shuttle_id)
    apply_action(state, CARDS, "play_card", card_id=freighter_id)
    apply_action(state, CARDS, "end_action_phase")
    state.turn.trade = 99
    apply_action(state, CARDS, "buy_trade_row_card", card_id=target_ship)

    assert state.players[state.active_player].draw_pile[-1] == target_ship


def test_factory_world_puts_next_acquired_card_into_hand():
    state = create_game(CARDS, seed=1)
    clear_hand(state, state.active_player)
    clear_trade_row(state)

    factory_id = add_card_to_hand(state, state.active_player, "factory_world")
    target_id = state.new_instance("trade_hauler", owner=None)
    state.trade_row.append(target_id)

    apply_action(state, CARDS, "play_card", card_id=factory_id)
    apply_action(state, CARDS, "end_action_phase")
    state.turn.trade = 99
    apply_action(state, CARDS, "buy_trade_row_card", card_id=target_id)

    assert target_id in state.players[state.active_player].hand


def test_warning_beacon_on_acquire_without_machine_cult_goes_to_discard():
    state = create_game(CARDS, seed=1)
    state.turn.phase = Phase.BUY
    state.turn.trade = 99
    clear_trade_row(state)

    beacon_id = state.new_instance("warning_beacon", owner=None)
    state.trade_row.append(beacon_id)

    apply_action(state, CARDS, "buy_trade_row_card", card_id=beacon_id)

    assert beacon_id in state.players[state.active_player].discard_pile
    assert beacon_id not in state.players[state.active_player].hand


def test_command_center_passive_adds_combat_when_star_empire_ship_played():
    state = create_game(CARDS, seed=1)
    clear_hand(state, state.active_player)

    center_id = add_card_to_hand(state, state.active_player, "command_center")
    barge_id = add_card_to_hand(state, state.active_player, "star_barge")

    apply_action(state, CARDS, "play_card", card_id=center_id)
    apply_action(state, CARDS, "play_card", card_id=barge_id)

    assert state.turn.trade == 4
    assert state.turn.combat == 4


def test_fleet_hq_passive_adds_combat_for_any_ship():
    state = create_game(CARDS, seed=1)
    clear_hand(state, state.active_player)

    hq_id = add_card_to_hand(state, state.active_player, "fleet_hq")
    scout_id = add_card_to_hand(state, state.active_player, "scout")

    apply_action(state, CARDS, "play_card", card_id=hq_id)
    apply_action(state, CARDS, "play_card", card_id=scout_id)

    assert state.turn.trade == 1
    assert state.turn.combat == 1


def test_blob_world_draw_branch_draws_per_blob_played():
    state = create_game(CARDS, seed=1)
    clear_hand(state, state.active_player)

    fighter_id = add_card_to_hand(state, state.active_player, "blob_fighter")
    world_id = add_card_to_hand(state, state.active_player, "blob_world")
    state.players[state.active_player].draw_pile = [
        state.new_instance("scout", owner=state.active_player),
        state.new_instance("viper", owner=state.active_player),
    ]

    apply_action(state, CARDS, "play_card", card_id=fighter_id)
    hand_before = len(state.players[state.active_player].hand)
    apply_action(state, CARDS, "play_card", card_id=world_id)
    apply_action(state, CARDS, "choose_option", option_index=1)

    assert len(state.players[state.active_player].hand) == 2


def test_blob_world_combat_branch_gains_five_combat():
    state = create_game(CARDS, seed=1)
    clear_hand(state, state.active_player)

    world_id = add_card_to_hand(state, state.active_player, "blob_world")
    apply_action(state, CARDS, "play_card", card_id=world_id)
    apply_action(state, CARDS, "choose_option", option_index=0)

    assert state.turn.combat == 5


def test_embassy_yacht_draws_two_if_two_bases_in_play():
    state = create_game(CARDS, seed=1)
    clear_hand(state, state.active_player)

    add_base_to_play(state, state.active_player, "trading_post")
    add_base_to_play(state, state.active_player, "storage_silo")
    yacht_id = add_card_to_hand(state, state.active_player, "embassy_yacht")
    state.players[state.active_player].draw_pile = [
        state.new_instance("scout", owner=state.active_player),
        state.new_instance("viper", owner=state.active_player),
    ]

    apply_action(state, CARDS, "play_card", card_id=yacht_id)

    hand_def_ids = [state.cards[cid].card_def_id for cid in state.players[state.active_player].hand]
    assert "scout" in hand_def_ids
    assert "viper" in hand_def_ids


def test_central_station_bonus_requires_three_bases():
    state = create_game(CARDS, seed=1)
    clear_hand(state, state.active_player)

    add_base_to_play(state, state.active_player, "trading_post")
    add_base_to_play(state, state.active_player, "storage_silo")
    station_id = add_card_to_hand(state, state.active_player, "central_station")
    state.players[state.active_player].draw_pile = [state.new_instance("scout", owner=state.active_player)]
    authority_before = state.players[state.active_player].authority

    apply_action(state, CARDS, "play_card", card_id=station_id)

    assert state.turn.trade == 2
    assert state.players[state.active_player].authority == authority_before + 4
    assert len(state.players[state.active_player].hand) == 1


def test_lancer_bonus_combat_if_opponent_has_base():
    state = create_game(CARDS, seed=1)
    clear_hand(state, state.active_player)

    lancer_id = add_card_to_hand(state, state.active_player, "lancer")
    add_base_to_play(state, 1 - state.active_player, "trading_post")

    apply_action(state, CARDS, "play_card", card_id=lancer_id)

    assert state.turn.combat == 6


def test_destroy_target_base_effect_removes_enemy_base():
    state = create_game(CARDS, seed=1)
    clear_hand(state, state.active_player)

    mech_id = add_card_to_hand(state, state.active_player, "missile_mech")
    target_base = add_base_to_play(state, 1 - state.active_player, "trading_post")

    apply_action(state, CARDS, "play_card", card_id=mech_id)
    apply_action(state, CARDS, "choose_card", card_id=target_base)

    assert target_base not in state.players[1 - state.active_player].bases_in_play
    assert target_base in state.scrap_heap


def test_destroy_target_base_can_be_declined_when_optional():
    state = create_game(CARDS, seed=1)
    clear_hand(state, state.active_player)

    mech_id = add_card_to_hand(state, state.active_player, "missile_mech")
    target_base = add_base_to_play(state, 1 - state.active_player, "trading_post")

    apply_action(state, CARDS, "play_card", card_id=mech_id)
    apply_action(state, CARDS, "decline")

    assert target_base in state.players[1 - state.active_player].bases_in_play
    assert target_base not in state.scrap_heap


def test_attack_player_reduces_authority_when_no_outpost():
    state = create_game(CARDS, seed=1)
    state.turn.phase = Phase.ATTACK
    state.turn.combat = 7
    before = state.players[1 - state.active_player].authority

    apply_action(state, CARDS, "attack_player")

    assert state.players[1 - state.active_player].authority == before - 7
    assert state.turn.combat == 0


def test_cleanup_discards_ships_but_keeps_bases():
    state = create_game(CARDS, seed=1)
    clear_hand(state, state.active_player)

    scout_id = add_card_to_hand(state, state.active_player, "scout")
    base_id = add_card_to_hand(state, state.active_player, "trading_post")

    apply_action(state, CARDS, "play_card", card_id=scout_id)
    apply_action(state, CARDS, "play_card", card_id=base_id)
    apply_action(state, CARDS, "choose_option", option_index=0)
    apply_action(state, CARDS, "end_action_phase")
    apply_action(state, CARDS, "end_buy_phase")
    apply_action(state, CARDS, "end_attack_phase")
    apply_action(state, CARDS, "cleanup_and_pass_turn")

    prev_player = 1 - state.active_player
    assert scout_id in state.players[prev_player].discard_pile
    assert base_id in state.players[prev_player].bases_in_play