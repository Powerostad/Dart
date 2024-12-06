from dataclasses import dataclass


@dataclass(frozen=True)
class Timeframes:
    TIMEFRAME_M1: int = 1
    TIMEFRAME_M2: int = 2
    TIMEFRAME_M3: int = 3
    TIMEFRAME_M4: int = 4
    TIMEFRAME_M5: int = 5
    TIMEFRAME_M6: int = 6
    TIMEFRAME_M10: int = 10
    TIMEFRAME_M12: int = 12
    TIMEFRAME_M15: int = 15
    TIMEFRAME_M20: int = 20
    TIMEFRAME_M30: int = 30
    TIMEFRAME_H1: int = 16385
    TIMEFRAME_H2: int = 16386
    TIMEFRAME_H3: int = 16387
    TIMEFRAME_H4: int = 16388
    TIMEFRAME_H6: int = 16390
    TIMEFRAME_H8: int = 16392
    TIMEFRAME_H12: int = 16396
    TIMEFRAME_D1: int = 16408
    TIMEFRAME_D2: int = 16409
    TIMEFRAME_D3: int = 16410
    TIMEFRAME_D4: int = 16411
    TIMEFRAME_D5: int = 16412
    TIMEFRAME_D6: int = 16413
    TIMEFRAME_W1: int = 32769
    TIMEFRAME_MN1: int = 49153

mt5 = Timeframes()
