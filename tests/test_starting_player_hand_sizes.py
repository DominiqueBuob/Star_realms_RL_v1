from data.colony_wars_cards import CARDS
from data.setup import create_game
from data.legal_actions import get_legal_actions



def test_initial_legal_actions_contains_playable_hand_cards_and_end_phase():
    state = create_game(CARDS, seed=1)
    actions = get_legal_actions(state, CARDS)

    play_actions = [a for a in actions if a["type"] == "play_card"]
    assert len(play_actions) == 3
    assert {"type": "end_action_phase"} in actions