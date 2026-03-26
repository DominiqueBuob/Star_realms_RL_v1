from __future__ import annotations

from typing import Mapping

from data.card_defs import CardDef
from data.enums import CardType
from data.legal_actions import get_legal_actions
from data.rules import get_card_def
from data.state import GameState


class ExpensiveBuyerScrapperBot:
    name = "expensive_buyer_scrapper"

    def choose_action(self, state: GameState, card_registry: Mapping[str, CardDef]) -> dict:
        actions = get_legal_actions(state, card_registry)
        if not actions:
            raise ValueError("No legal actions available.")

        pending = state.pending[0] if state.pending else None
        if pending:
            return self._choose_pending_action(state, card_registry, actions, pending.payload.get("kind"))

        action = self._best_normal_action(state, card_registry, actions)
        if action is None:
            raise ValueError("Could not choose an action.")
        return action

    def _choose_pending_action(
        self,
        state: GameState,
        card_registry: Mapping[str, CardDef],
        actions: list[dict],
        kind: str | None,
    ) -> dict:
        if kind == "choose_one":
            return self._choose_best_option(state, card_registry, actions)

        if kind in {
            "scrap_hand",
            "scrap_discard",
            "scrap_hand_or_discard",
            "scrap_trade_row",
            "discard_then_draw_same_count",
            "may_discard_then_draw",
            "discard_up_to_then_gain_per_discard_choice",
            "scrap_up_to_then_draw_same_count",
            "forced_discard",
        }:
            return self._choose_cheapest_card_or_decline(state, card_registry, actions)

        if kind == "acquire_free":
            return self._choose_most_expensive_card(state, card_registry, actions)

        if kind == "destroy_base":
            return self._choose_best_base_target(state, card_registry, actions)

        return actions[0]

    def _best_normal_action(
        self,
        state: GameState,
        card_registry: Mapping[str, CardDef],
        actions: list[dict],
    ) -> dict | None:
        play_actions = [a for a in actions if a["type"] == "play_card"]
        if play_actions:
            return max(play_actions, key=lambda a: self._play_priority(state, card_registry, a["card_id"]))

        scrap_actions = [a for a in actions if a["type"] == "use_scrap_ability"]
        if scrap_actions:
            return max(scrap_actions, key=lambda a: self._scrap_ability_priority(state, card_registry, a["card_id"]))

        buy_actions = [a for a in actions if a["type"] == "buy_trade_row_card"]
        if buy_actions:
            return max(buy_actions, key=lambda a: self._card_cost(state, card_registry, a["card_id"]))

        explorer_actions = [a for a in actions if a["type"] == "buy_explorer"]
        if explorer_actions:
            return explorer_actions[0]

        attack_base_actions = [a for a in actions if a["type"] == "attack_base"]
        if attack_base_actions:
            return max(attack_base_actions, key=lambda a: self._base_priority(state, card_registry, a["card_id"]))

        attack_player_actions = [a for a in actions if a["type"] == "attack_player"]
        if attack_player_actions:
            return attack_player_actions[0]

        for t in ("end_action_phase", "end_buy_phase", "end_attack_phase", "cleanup_and_pass_turn"):
            for action in actions:
                if action["type"] == t:
                    return action

        return actions[0] if actions else None

    def _choose_most_expensive_card(
        self,
        state: GameState,
        card_registry: Mapping[str, CardDef],
        actions: list[dict],
    ) -> dict:
        choose_card_actions = [a for a in actions if a["type"] == "choose_card"]
        if not choose_card_actions:
            for a in actions:
                if a["type"] == "decline":
                    return a
            return actions[0]
        return max(choose_card_actions, key=lambda a: self._card_cost(state, card_registry, a["card_id"]))

    def _choose_cheapest_card_or_decline(
        self,
        state: GameState,
        card_registry: Mapping[str, CardDef],
        actions: list[dict],
    ) -> dict:
        choose_card_actions = [a for a in actions if a["type"] == "choose_card"]
        if not choose_card_actions:
            for a in actions:
                if a["type"] == "decline":
                    return a
            return actions[0]
        return min(
            choose_card_actions,
            key=lambda a: (
                self._card_cost(state, card_registry, a["card_id"]),
                self._tie_break_scrap(state, card_registry, a["card_id"]),
            ),
        )

    def _choose_best_base_target(
        self,
        state: GameState,
        card_registry: Mapping[str, CardDef],
        actions: list[dict],
    ) -> dict:
        choose_card_actions = [a for a in actions if a["type"] == "choose_card"]
        if not choose_card_actions:
            for a in actions:
                if a["type"] == "decline":
                    return a
            return actions[0]
        return max(choose_card_actions, key=lambda a: self._base_priority(state, card_registry, a["card_id"]))

    def _choose_best_option(
        self,
        state: GameState,
        card_registry: Mapping[str, CardDef],
        actions: list[dict],
    ) -> dict:
        # Simple heuristic:
        # prefer more trade in BUY-ish choices, else more combat, then draw, then authority
        # without deep simulation.
        option_actions = [a for a in actions if a["type"] == "choose_option"]
        if not option_actions:
            return actions[0]

        pending = state.pending[0]
        options = pending.payload["options"]

        def score_option(index: int) -> tuple[int, int, int, int]:
            trade = 0
            combat = 0
            draw = 0
            authority = 0
            for eff in options[index]:
                name = type(eff).__name__
                if name == "GainTrade":
                    trade += eff.amount
                elif name == "GainCombat":
                    combat += eff.amount
                elif name == "DrawCards":
                    draw += eff.amount
                elif name == "GainAuthority":
                    authority += eff.amount
            return (trade, combat, draw, authority)

        best = max(option_actions, key=lambda a: score_option(a["option_index"]))
        return best

    def _card_cost(self, state: GameState, card_registry: Mapping[str, CardDef], card_id: int) -> int:
        cdef = get_card_def(state, card_registry, card_id)
        return -1 if cdef.cost is None else cdef.cost

    def _play_priority(self, state: GameState, card_registry: Mapping[str, CardDef], card_id: int) -> tuple[int, int, int]:
        cdef = get_card_def(state, card_registry, card_id)
        score = self._card_cost(state, card_registry, card_id)

        text_bonus = 0
        for ability in cdef.abilities:
            trig = getattr(ability.trigger, "value", str(ability.trigger))
            if trig == "ON_PLAY":
                for eff in ability.effects:
                    name = type(eff).__name__
                    if name == "DrawCards":
                        text_bonus += 50
                    elif name in {"GainTrade", "GainCombat", "GainAuthority"}:
                        text_bonus += 10
                    elif name.startswith("Scrap"):
                        text_bonus += 20
                    elif name in {"ChooseOne", "AcquireFree", "SetNextAcquireDestination"}:
                        text_bonus += 30

        is_base = 1 if cdef.card_type == CardType.BASE else 0
        return (text_bonus, score, is_base)

    def _scrap_ability_priority(self, state: GameState, card_registry: Mapping[str, CardDef], card_id: int) -> tuple[int, int]:
        cdef = get_card_def(state, card_registry, card_id)
        score = self._card_cost(state, card_registry, card_id)
        base_bonus = 100 if cdef.card_type == CardType.SHIP else 0
        return (base_bonus, score)

    def _base_priority(self, state: GameState, card_registry: Mapping[str, CardDef], card_id: int) -> tuple[int, int]:
        cdef = get_card_def(state, card_registry, card_id)
        defense = -1 if cdef.defense is None else cdef.defense
        cost = self._card_cost(state, card_registry, card_id)
        is_outpost = 1 if getattr(cdef, "is_outpost", False) else 0
        return (is_outpost, defense, cost)

    def _tie_break_scrap(self, state: GameState, card_registry: Mapping[str, CardDef], card_id: int) -> tuple[int, int, str]:
        cdef = get_card_def(state, card_registry, card_id)
        faction_bias = 0 if "UNALIGNED" in {f.value for f in cdef.factions} else 1
        cost = self._card_cost(state, card_registry, card_id)
        return (faction_bias, cost, cdef.name)