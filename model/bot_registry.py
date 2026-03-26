from __future__ import annotations

from model.expensive_buyer_scrapper_bot import ExpensiveBuyerScrapperBot
from model.random_bot import RandomBot
from model.aggressive_buyer_bot import AggressiveBuyerBot


def build_bot(name: str, seed: int | None = None):
    name = name.lower().strip()

    if name == "random":
        return RandomBot(seed=seed)
    if name == "expensive_buyer_scrapper":
        return ExpensiveBuyerScrapperBot()
    if name == "aggressive_buyer_bot":
        return AggressiveBuyerBot()

    raise ValueError(f"Unknown bot: {name}")


def available_bots() -> list[str]:
    return [
        "random",
        "expensive_buyer_scrapper",
        "aggressive_buyer_bot",
    ]