from dataclasses import dataclass, asdict
from enum import Enum, auto
from typing import List

import pandas as pd


class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    NEUTRAL = "NEUTRAL"


@dataclass
class TradingSignal:
    symbol: str
    timeframe: str
    signal_type: SignalType
    confidence: float
    algorithms_triggered: List[str]

    def to_dict(self):
        data = asdict(self)
        data["signal_type"] = self.signal_type.name
        return data

class TradingAlgorithm:
    def __init__(self, name: str):
        self.name = name

    def generate_signal(self, data: pd.DataFrame) -> SignalType:
        raise NotImplementedError("Subclasses must implement this method.")
