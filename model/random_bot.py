import random


def choose_random_action(state, card_registry, get_legal_actions_fn, rng: random.Random | None = None) -> dict:
    rng = rng or random.Random()
    actions = get_legal_actions_fn(state, card_registry)
    if not actions:
        raise ValueError("No legal actions available.")
    return rng.choice(actions)