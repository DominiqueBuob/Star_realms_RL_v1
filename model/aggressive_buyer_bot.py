from __future__ import annotations

from typing import Mapping

from data.card_defs import CardDef
from data.legal_actions import get_legal_actions
from data.rules import get_card_def
from data.state import GameState


class AggressiveBuyerBot:
    name = "aggressive_buyer"

    def choose_action(self, state: GameState, card_registry: Mapping[str, CardDef]) -> dict:
        actions = get_legal_actions(state, card_registry)
        if not actions:
            raise ValueError("No legal actions available.")

        # 1. Handle pending choices (scrap, discard, etc.)
        if state.pending:
            return actions[0]

        # 2. Action Phase: Play cards and use abilities
        play_actions = [a for a in actions if a["type"] == "play_card"]
        if play_actions:
            return play_actions[0]

        scrap_actions = [a for a in actions if a["type"] == "use_scrap_ability"]
        if scrap_actions:
            return scrap_actions[0]

        # 3. Buy Phase Logic: Buy highest combat, then highest cost
        buy_actions = [a for a in actions if a["type"] in ("buy_trade_row_card", "buy_explorer")]
        if buy_actions:
            return max(buy_actions, key=lambda a: self._buy_priority(state, card_registry, a))

        # 4. Attack Phase Logic: Always attack if possible
        attack_base_actions = [a for a in actions if a["type"] == "attack_base"]
        if attack_base_actions:
            return attack_base_actions[0]

        attack_player_actions = [a for a in actions if a["type"] == "attack_player"]
        if attack_player_actions:
            return attack_player_actions[0]

        # 5. End phases
        for phase_end in ("end_action_phase", "end_buy_phase", "end_attack_phase", "cleanup_and_pass_turn"):
            for action in actions:
                if action["type"] == phase_end:
                    return action

        # Fallback
        return actions[0]

    def _buy_priority(self, state: GameState, card_registry: Mapping[str, CardDef], action: dict) -> tuple[int, int]:
        """
        Returns a tuple of (combat_value, cost_value).
        max() will prioritize the highest combat first, and use cost as a tiebreaker.
        """
        if action["type"] == "buy_explorer":
            # Explorers provide 0 combat and cost 2 trade
            return (0, 2)

        card_id = action["card_id"]
        cdef = get_card_def(state, card_registry, card_id)

        combat = 0
        # Tally up all combat provided by the card's effects
        for ability in cdef.abilities:
            for eff in ability.effects:
                if type(eff).__name__ == "GainCombat":
                    combat += getattr(eff, "amount", 0)

        cost = cdef.cost if cdef.cost is not None else -1
        
        return (combat, cost)