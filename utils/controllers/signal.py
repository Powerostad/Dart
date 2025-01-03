from dataclasses import dataclass
from typing import List, Dict, Type, Optional

from celery.utils.log import get_task_logger

from utils.algorithms.base import TradingAlgorithm, TradingSignal, SignalType
from utils.controllers.metatrader import AsyncMT5Controller

logger = get_task_logger(__name__)

@dataclass
class SignalGenerationConfig:
    """Configuration for signal generation"""
    timeframes: List[str]
    algorithm_classes: List[Type[TradingAlgorithm]]
    confidence_threshold: float = 0.7


class SignalController:
    def __init__(self,
                 market_data_manager: AsyncMT5Controller,
                 config: SignalGenerationConfig):
        self.market_data_manager = market_data_manager
        self.config = config
        self.algorithms = [algo() for algo in config.algorithm_classes]

    @classmethod
    async def create(cls, config: SignalGenerationConfig) -> 'SignalController':
        """Factory method for creating SignalController instance"""
        controller = await AsyncMT5Controller.get_instance()
        return cls(controller, config)

    async def generate_signals_for_symbol(self, symbol: str, timeframe: str) -> Optional[TradingSignal]:
        """Generate signals for a single symbol and timeframe"""
        try:
            # Retrieve historical market data
            data = await self.market_data_manager.get_historical_data_candles(
                symbol=symbol,
                timeframe=timeframe
            )

            algorithm_signals = []
            for algo in self.algorithms:
                try:
                    signal = algo.generate_signal(data)
                    print("SIGNAL IS: ", signal)
                    if signal != SignalType.NEUTRAL:
                        algorithm_signals.append({
                            'name': algo.name,
                            'signal': signal
                        })
                except Exception as e:
                    logger.error(f"Algorithm {algo.name} failed: {str(e)}")
                    continue

            if not algorithm_signals:
                return None

            # Calculate confidence based on algorithm agreement
            buy_count = sum(1 for s in algorithm_signals if s['signal'] == SignalType.BUY)
            sell_count = sum(1 for s in algorithm_signals if s['signal'] == SignalType.SELL)

            # Determine dominant signal
            if buy_count > sell_count:
                confidence = buy_count / len(self.algorithms)
                signal_type = SignalType.BUY
            else:
                confidence = sell_count / len(self.algorithms)
                signal_type = SignalType.SELL

            # Only generate signal if confidence threshold is met
            if confidence < self.config.confidence_threshold:
                return None

            return TradingSignal(
                symbol=symbol,
                timeframe=timeframe,
                signal_type=signal_type,
                confidence=confidence,
                algorithms_triggered=[s['name'] for s in algorithm_signals]
            )

        except Exception as e:
            logger.error(f"Error generating signals for {symbol} {timeframe}: {str(e)}")
            return None

    async def generate_multi_timeframe_signals(self) -> Dict[str, List[TradingSignal]]:
        """Generate signals across multiple symbols and timeframes"""
        all_signals = {}

        try:
            for symbol in self.config.symbols:
                symbol_signals = []

                for timeframe in self.config.timeframes:
                    try:
                        signals = await self.generate_signals_for_symbol(symbol, timeframe)
                        symbol_signals.extend(signals)
                    except Exception as e:
                        logger.error(f"Error processing {symbol} {timeframe}: {str(e)}")
                        continue

                if symbol_signals:
                    all_signals[symbol] = symbol_signals

        except Exception as e:
            logger.error(f"Error in generate_multi_timeframe_signals: {str(e)}")

        return all_signals

    async def available_symbols(self) -> List[str]:
        """Get available trading symbols"""
        try:
            return await self.market_data_manager.get_mt5_symbols()
        except Exception as e:
            logger.error(f"Error getting available symbols: {str(e)}")
            return []