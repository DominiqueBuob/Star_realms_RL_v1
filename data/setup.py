from __future__ import annotations

from state import GameState, PlayerState
from turn_state import TurnState
from enums import Phase


STARTING_AUTHORITY = 50
STARTING_SCOUTS = 8
STARTING_VIPERS = 2
STARTING_HAND_SIZE = 5
TRADE_ROW_SIZE = 5


def _make_starting_deck(state: GameState, player_idx: int) -> list[int]:
    deck = []
    for _ in range(STARTING_SCOUTS):
        deck.append(state.new_instance("scout", owner=player_idx))
    for _ in range(STARTING_VIPERS):
        deck.append(state.new_instance("viper", owner=player_idx))
    state.rng.shuffle(deck)
    return deck


def _draw_to_hand(state: GameState, player_idx: int, n: int) -> None:
    player = state.players[player_idx]
    for _ in range(n):
        if not player.draw_pile:
            if not player.discard_pile:
                return
            player.draw_pile = list(player.discard_pile)
            player.discard_pile.clear()
            state.rng.shuffle(player.draw_pile)
        card_id = player.draw_pile.pop()
        player.hand.append(card_id)


def _build_trade_deck(state: GameState, card_registry: dict[str, object]) -> list[int]:
    deck: list[int] = []
    for card_def_id, card_def in card_registry.items():
        if card_def_id in {"scout", "viper", "explorer"}:
            continue
        cost = getattr(card_def, "cost", None)
        if cost is None:
            continue
        deck.append(state.new_instance(card_def_id, owner=None))
    state.rng.shuffle(deck)
    return deck


def _fill_trade_row(state: GameState) -> None:
    while len(state.trade_row) < TRADE_ROW_SIZE and state.trade_deck:
        state.trade_row.append(state.trade_deck.pop())


def create_game(card_registry: dict[str, object], seed: int | None = None) -> GameState:
    state = GameState()
    if seed is not None:
        state.rng.seed(seed)

    state.players = [
        PlayerState(authority=STARTING_AUTHORITY),
        PlayerState(authority=STARTING_AUTHORITY),
    ]

    for player_idx in (0, 1):
        state.players[player_idx].draw_pile = _make_starting_deck(state, player_idx)
        _draw_to_hand(state, player_idx, STARTING_HAND_SIZE)

    state.trade_deck = _build_trade_deck(state, card_registry)
    _fill_trade_row(state)

    state.explorer_pile_count = 10
    state.active_player = 0
    state.turn_number = 1
    state.turn = TurnState(phase=Phase.ACTION)
    state.pending.clear()
    state.winner = None
    return state