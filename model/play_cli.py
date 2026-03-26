from __future__ import annotations

import random

from data.colony_wars_cards import CARDS
from data.legal_actions import get_legal_actions
from model.random_bot import choose_random_action
from data.rules import apply_action, get_card_def
from data.setup import create_game


def card_name(state, card_id: int) -> str:
    return state.cards[card_id].card_def_id


def pretty_card(state, card_registry, card_id: int) -> str:
    cdef = get_card_def(state, card_registry, card_id)
    return f"{card_id}:{cdef.name}"


def print_state(state, card_registry) -> None:
    me = state.players[state.active_player]
    opp = state.players[1 - state.active_player]

    print()
    print("=" * 80)
    print(f"Turn {state.turn_number} | Active player: {state.active_player} | Phase: {state.turn.phase}")
    print(f"Trade: {state.turn.trade} | Combat: {state.turn.combat}")
    print(f"Your authority: {me.authority} | Opp authority: {opp.authority}")
    print()

    print("Your hand:")
    for cid in me.hand:
        print(f"  {pretty_card(state, card_registry, cid)}")

    print("\nYour ships in play:")
    for cid in me.ships_in_play:
        print(f"  {pretty_card(state, card_registry, cid)}")

    print("\nYour bases in play:")
    for cid in me.bases_in_play:
        print(f"  {pretty_card(state, card_registry, cid)}")

    print("\nOpponent bases in play:")
    for cid in opp.bases_in_play:
        print(f"  {pretty_card(state, card_registry, cid)}")

    print("\nTrade row:")
    for cid in state.trade_row:
        cdef = get_card_def(state, card_registry, cid)
        print(f"  {cid}:{cdef.name} (cost={cdef.cost}, type={cdef.card_type})")

    print(f"\nExplorer pile: {state.explorer_pile_count}")
    print(f"Pending decisions: {len(state.pending)}")


def print_actions(actions, state, card_registry) -> None:
    print("\nLegal actions:")
    for i, action in enumerate(actions):
        print(f"  [{i}] {format_action(action, state, card_registry)}")


def format_action(action: dict, state, card_registry) -> str:
    t = action["type"]

    if t in {"play_card", "use_scrap_ability", "buy_trade_row_card", "attack_base", "choose_card"}:
        cid = action["card_id"]
        return f"{t} -> {pretty_card(state, card_registry, cid)}"

    if t == "choose_option":
        return f"{t} -> option {action['option_index']}"

    return t


def parse_human_action(actions, raw: str) -> dict:
    idx = int(raw.strip())
    if idx < 0 or idx >= len(actions):
        raise ValueError("Action index out of range.")
    return actions[idx]


def run_human_vs_random(seed: int = 1, human_player: int = 0) -> None:
    state = create_game(CARDS, seed=seed)
    rng = random.Random(seed + 999)

    while state.winner is None:
        # If cleanup is the only action, auto-run it
        actions = get_legal_actions(state, CARDS)
        if len(actions) == 1 and actions[0]["type"] == "cleanup_and_pass_turn":
            apply_action(state, CARDS, actions[0]["type"])
            continue

        if state.active_player == human_player:
            print_state(state, CARDS)
            actions = get_legal_actions(state, CARDS)
            print_actions(actions, state, CARDS)

            while True:
                raw = input("\nChoose action index: ")
                try:
                    action = parse_human_action(actions, raw)
                    apply_action(state, CARDS, action["type"], **{k: v for k, v in action.items() if k != "type"})
                    break
                except Exception as e:
                    print(f"Invalid input/action: {e}")
        else:
            action = choose_random_action(state, CARDS, get_legal_actions, rng=rng)
            print(f"\nBot chooses: {format_action(action, state, CARDS)}")
            apply_action(state, CARDS, action["type"], **{k: v for k, v in action.items() if k != "type"})

    print()
    print("=" * 80)
    print(f"Winner: player {state.winner}")


if __name__ == "__main__":
    run_human_vs_random(seed=1, human_player=0)