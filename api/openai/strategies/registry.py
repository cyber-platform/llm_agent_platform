from __future__ import annotations

from api.openai.strategies.direct import DirectStrategy
from api.openai.strategies.rotate_on_429_rounding import RotateOn429RoundingStrategy


def get_strategy(strategy_id: str):
    if strategy_id == RotateOn429RoundingStrategy.id:
        return RotateOn429RoundingStrategy()
    return DirectStrategy()
