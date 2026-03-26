from __future__ import annotations

from collections import Counter

from data.colony_wars_cards import CARDS
from data.legal_actions import get_legal_actions
from data.rules import apply_action
from data.setup import create_game
from model.bot_registry import available_bots, build_bot


def ask_bot_name(prompt: str) -> str:
    bots = available_bots()
    print(prompt)
    for i, name in enumerate(bots):
        print(f"  [{i}] {name}")

    raw = input("Choose bot: ").strip()
    if raw.isdigit():
        idx = int(raw)
        if idx < 0 or idx >= len(bots):
            raise ValueError("Bot index out of range.")
        return bots[idx]

    raw = raw.lower()
    if raw in bots:
        return raw

    raise ValueError(f"Unknown bot choice: {raw}")


def ask_int(prompt: str, default: int) -> int:
    raw = input(f"{prompt} [{default}]: ").strip()
    if raw == "":
        return default
    return int(raw)


def run_single_game(bot0_name: str, bot1_name: str, seed: int) -> int:
    state = create_game(CARDS, seed=seed)

    bot0 = build_bot(bot0_name, seed=seed + 1000)
    bot1 = build_bot(bot1_name, seed=seed + 2000)
    bots = {0: bot0, 1: bot1}

    max_turns = 5000

    while state.winner is None and state.turn_number <= max_turns:
        actions = get_legal_actions(state, CARDS)
        if not actions:
            raise ValueError("No legal actions available during game.")

        # Auto-run forced cleanup if it is the only choice
        if len(actions) == 1 and actions[0]["type"] == "cleanup_and_pass_turn":
            apply_action(state, CARDS, "cleanup_and_pass_turn")
            continue

        bot = bots[state.active_player]
        action = bot.choose_action(state, CARDS)

        legal_actions = get_legal_actions(state, CARDS)
        if action not in legal_actions:
            raise ValueError(
                f"Bot {bot.name} produced illegal action {action}. Legal actions: {legal_actions}"
            )

        apply_action(
            state,
            CARDS,
            action["type"],
            **{k: v for k, v in action.items() if k != "type"},
        )

    if state.winner is None:
        # Fallback if a game somehow stalls
        p0 = state.players[0].authority
        p1 = state.players[1].authority
        if p0 > p1:
            return 0
        if p1 > p0:
            return 1
        return 0

    return state.winner


def run_match(bot_a_name: str, bot_b_name: str, games: int, base_seed: int = 1) -> None:
    wins = Counter()
    seat_wins = Counter()

    for i in range(games):
        seed = base_seed + i

        # Alternate seats for fairness
        if i % 2 == 0:
            p0_name, p1_name = bot_a_name, bot_b_name
            winner = run_single_game(p0_name, p1_name, seed)
            winner_name = p0_name if winner == 0 else p1_name
            wins[winner_name] += 1
            seat_wins[winner] += 1
        else:
            p0_name, p1_name = bot_b_name, bot_a_name
            winner = run_single_game(p0_name, p1_name, seed)
            winner_name = p0_name if winner == 0 else p1_name
            wins[winner_name] += 1
            seat_wins[winner] += 1

        if (i + 1) % 10 == 0 or i == games - 1:
            print(f"Completed {i + 1}/{games} games")

    print("\n" + "=" * 80)
    print("Match results")
    print("=" * 80)
    print(f"{bot_a_name}: {wins[bot_a_name]} wins ({wins[bot_a_name] / games:.1%})")
    print(f"{bot_b_name}: {wins[bot_b_name]} wins ({wins[bot_b_name] / games:.1%})")
    print()
    print(f"Seat 0 wins: {seat_wins[0]} ({seat_wins[0] / games:.1%})")
    print(f"Seat 1 wins: {seat_wins[1]} ({seat_wins[1] / games:.1%})")


def main() -> None:
    bot_a = ask_bot_name("Choose first bot")
    bot_b = ask_bot_name("Choose second bot")
    games = ask_int("Number of games", 100)
    seed = ask_int("Base seed", 1)

    print()
    print(f"Running {games} games: {bot_a} vs {bot_b}")
    run_match(bot_a, bot_b, games, base_seed=seed)


if __name__ == "__main__":
    main()