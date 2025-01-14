import pandas as pd
from celery.utils.log import get_task_logger
from utils.data_handler.data_handler import RealTimeDataHandler
from utils.position_manager.position_manager import PositionManager
from utils.timeframes import mt5
import asyncio
import logging
from typing import Dict, List, Union
from datetime import datetime, timedelta


class SignalManager:
    def __init__(self,
                 symbols: List[str],
                 timeframe=mt5.TIMEFRAME_M1,
                 max_positions=10,
                 trade_interval: timedelta = timedelta(minutes=5)):
        """
        Enhanced SignalManager with robust async signal generation.

        Args:
            symbols (List[str]): List of trading symbols
            timeframe (int): Trading timeframe
            max_positions (int): Maximum concurrent positions
            trade_interval (timedelta): Minimum time between trades
        """
        self.logger = get_task_logger("tasks")

        # Core configuration
        self.symbols = symbols
        self.timeframe = timeframe
        self.max_positions = max_positions
        self.trade_interval = trade_interval

        # Signal generation components
        self.data_handlers = {
            symbol: RealTimeDataHandler([symbol], timeframe)
            for symbol in symbols
        }
        self.position_manager = PositionManager(
            max_positions=max_positions,
            risk_per_trade=0.02
        )

        # Signal algorithms registry
        self.algorithms = []

        # Trade tracking
        self.last_trade_time = None

    def add_algorithm(self, algorithm):
        """
        Register a signal generation algorithm.

        Args:
            algorithm: Signal generation algorithm with get_signal method
        """
        self.algorithms.append(algorithm)

    async def get_signals(self) -> Dict[str, str]:
        """
        Asynchronously generate signals for all symbols.

        Returns:
            Dict mapping symbols to their generated signals
        """
        try:
            # Concurrently update data for all symbols
            await asyncio.gather(
                *[handler.update_data() for handler in self.data_handlers.values()]
            )

            # Generate signals for each symbol
            signals = {}
            for symbol in self.symbols:
                # Get historical data for the symbol
                symbol_data = await self.data_handlers[symbol].get_data()

                # Process signals using registered algorithms
                signals[symbol] = await self._generate_symbol_signal(symbol, symbol_data)

            return signals

        except Exception as e:
            self.logger.error(f"Error generating signals: {e}")
            return {symbol: 'error' for symbol in self.symbols}

    async def _generate_symbol_signal(self, symbol: str, symbol_data: pd.DataFrame) -> str:
        """
        Generate signals for a specific symbol using registered algorithms.

        Args:
            symbol (str): Trading symbol
            symbol_data (pd.DataFrame): Historical price data

        Returns:
            Aggregated signal ('buy', 'sell', 'hold')
        """
        if not self.algorithms:
            self.logger.warning("No signal algorithms registered")
            return 'hold'

        # Collect individual algorithm signals
        algorithm_signals = []
        for algorithm in self.algorithms:
            try:
                signal = algorithm.get_signal(symbol_data)
                algorithm_signals.append(signal)
            except Exception as e:
                self.logger.error(f"Algorithm signal error for {symbol}: {e}")

        return self._aggregate_signals(algorithm_signals)

    def _aggregate_signals(self, signals: List[int]) -> str:
        """
        Aggregate signals using weighted consensus.

        Args:
            signals (List[int]): Raw algorithm signals

        Returns:
            Consensus signal
        """
        if not signals:
            return 'hold'

        buy_weight = sum(1 for sig in signals if sig == 2)
        sell_weight = sum(1 for sig in signals if sig == 1)

        total_weight = len(signals)
        buy_ratio = buy_weight / total_weight
        sell_ratio = sell_weight / total_weight

        if buy_ratio >= 0.7:
            return 'buy'
        elif sell_ratio >= 0.7:
            return 'sell'

        return 'hold'