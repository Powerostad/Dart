from typing import List, Dict
from utils.algorithms.base import TradingAlgorithm, TradingSignal, SignalType
from utils.controllers.metatrader import AsyncMT5Controller


class SignalController:
    def __init__(self,
                 market_data_manager,
                 symbols: List[str],
                 timeframes: List[str],
                 algorithms: List[TradingAlgorithm]
                 ):
        self.market_data_manager = market_data_manager
        self.symbols = symbols
        self.timeframes = timeframes
        self.algorithms = algorithms

    @classmethod
    async def create(cls, symbols: List[str], timeframes: List[str], algorithms: List[TradingAlgorithm]):
        controller = AsyncMT5Controller()
        return cls(controller, symbols, timeframes, algorithms)


    async def generate_multi_timeframe_signals(self) -> Dict[str, List[TradingSignal]]:
        """
        Generate signals across multiple symbols and timeframes
        
        Returns:
            Dict[str, List[TradingSignal]]: Signals for each symbol
        """

        print("INSIDE GENERATE_MULTI_TIMEFRAME_SIGNALS")
        all_signals = {}

        for symbol in self.symbols:
            symbol_signals = []

            for timeframe in self.timeframes:
                # Retrieve historical market data
                data = await self.market_data_manager.get_historical_data_candles(symbol, timeframe)

                # Run all algorithms
                algorithm_signals = []
                for algo in self.algorithms:
                    signal = algo.generate_signal(data)
                    if signal != SignalType.NEUTRAL:
                        algorithm_signals.append(algo.name)

                # Calculate confidence and create signal
                confidence = len(algorithm_signals) / len(self.algorithms)

                if algorithm_signals:
                    dominant_signal = SignalType.BUY if confidence > 0.5 else SignalType.SELL
                    trading_signal = TradingSignal(
                        symbol=symbol,
                        timeframe=timeframe,
                        signal_type=dominant_signal,
                        confidence=confidence,
                        algorithms_triggered=algorithm_signals
                    )
                    symbol_signals.append(trading_signal)

            all_signals[symbol] = symbol_signals
        print("ALL SIGNALS: ", all_signals)
        return all_signals

    async def available_symbols(self):
        print("IN AVAILABLE SYMBOLS: ", await self.market_data_manager.get_mt5_symbols())
        return await self.market_data_manager.get_mt5_symbols()