from __future__ import annotations

from model.expensive_buyer_scrapper_bot import ExpensiveBuyerScrapperBot
from model.random_bot import RandomBot


def build_bot(name: str, seed: int | None = None):
    name = name.lower().strip()

    if name == "random":
        return RandomBot(seed=seed)
    if name == "expensive_buyer_scrapper":
        return ExpensiveBuyerScrapperBot()

    raise ValueError(f"Unknown bot: {name}")


def available_bots() -> list[str]:
    return [
        "random",
        "expensive_buyer_scrapper",
    ]