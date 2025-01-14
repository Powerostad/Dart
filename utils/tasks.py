from asgiref.sync import async_to_sync
from celery import shared_task
import asyncio
from typing import List, Dict
from celery.utils.log import get_task_logger
from utils.controllers.metatrader import AsyncMT5Controller
from utils.controllers.signal import SignalController, SignalGenerationConfig
from apps.forex.models import Signal
from utils.algorithms.algorithms import MHarrisSystematic, AligatorAlgorithm, NadayaraWatsonFullStrategy15Min
from utils.algorithms.base import TradingSignal
from django.conf import settings

try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

logger = get_task_logger("tasks")

mt5_controller = async_to_sync(AsyncMT5Controller.get_instance)()
controller = loop.run_until_complete(SignalController.create(settings.SIGNAL_CONFIG))


@shared_task(bind=True, max_retries=3)
def generate_trading_signals(self) -> Dict[str, List[TradingSignal]]:
    """Celery task to generate trading signals"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    try:
        all_symbols = async_to_sync(mt5_controller.get_mt5_symbols)()
        active_symbols = []
        for symbol in all_symbols:
            try:
                # Get recent volume data
                data = async_to_sync(mt5_controller.get_historical_data_candles)(
                    symbol,
                    timeframe='15m',
                    lookback=10
                )
                if data is not None and not data.empty:
                    avg_volume = data['volume'].mean()
                    active_symbols.append((symbol, avg_volume))
            except Exception as e:
                continue

        active_symbols.sort(key=lambda x: x[1], reverse=True)
        active_symbols = [symbol for symbol, _ in active_symbols]

        # Create configuration
        config = SignalGenerationConfig(
            symbols=active_symbols[:100],
            timeframes=settings.TRADING_TIMEFRAMES,
            algorithm_classes=[MHarrisSystematic, AligatorAlgorithm, NadayaraWatsonFullStrategy15Min],
            confidence_threshold=settings.SIGNAL_CONFIDENCE_THRESHOLD,
        )

        # Create controller and generate signals
        signals = loop.run_until_complete(controller.generate_multi_timeframe_signals())

        # Process and store signals
        for symbol, symbol_signals in signals.items():
            for signal in symbol_signals:
                store_trading_signal.delay(
                    symbol=signal.symbol,
                    timeframe=signal.timeframe,
                    signal_type=signal.signal_type.value,
                    confidence=signal.confidence,
                    algorithms=signal.algorithms_triggered
                )

        return signals

    except Exception as exc:
        self.retry(exc=exc, countdown=60)


@shared_task
def store_trading_signal(symbol: str, timeframe: str, signal_type: str,
                         confidence: float, algorithms: List[str]) -> None:
    """Store trading signal in database"""
    logger.info("Storing trading signal in database")
    Signal.objects.create(
        symbol=symbol,
        timeframe=timeframe,
        signal_type=signal_type,
        confidence=confidence,
        algorithms_triggered=algorithms
    )
    logger.info(f"Signal with symbol: {symbol} and timeframe: {timeframe} and signal type: {signal_type} has been stored")

# async def active_symbols(number_of_top_symbols=10):
#     cache_key = f"top_{number_of_top_symbols}_symbols"
#     cached_data = await self.cache.get(cache_key)
#     if cached_data is not None:
#         return cached_data
#     logger.info("before mt5 connection")
#     async with self.connection():
#         try:
#             logger.info("inside mt5 connection")
#             symbols = await sync_to_async(self.mt5.symbols_get)()
#             logger.info(f"got symbols: {symbols}")
#             symbol_names = [symbol.name for symbol in symbols]
#             active_symbols = []
#             for symbol in symbol_names:
#                 try:
#                     data = await self.get_historical_data_candles(symbol, timeframe="daily", lookback=10)
#                     logger.info(f"got historical data of {symbol}")
#                     if data is not None and not data.empty:
#                         avg_volume = data['volume'].mean()
#                         logger.info(f"avg_volume of {symbol}: {avg_volume}")
#                         active_symbols.append((symbol, avg_volume))
#                 except Exception as e:
#                     logger.error(f"error on getting data: {str(e)}")
#                     continue
#
#             active_symbols.sort(key=lambda x: x[1], reverse=True)
#             self.active_symbols = list({symbol for symbol, _ in active_symbols})[:number_of_top_symbols]
#
#             await self.cache.set(cache_key, symbol_names, ttl=86400)  # 24 Hour
#             logger.info(f"{self.active_symbols}")
#             return self.active_symbols

@shared_task(max_retries=3)
def five_minute_signal():
    async def task_logic():
        symbols = await mt5_controller.get_mt5_symbols(number_of_top_symbols=10)
        logger.info(f"all the symbols: {symbols}, len symbols: {len(symbols)}")
        for symbol in symbols:
            signal = await controller.generate_signals_for_symbol(symbol=symbol, timeframe="5m")
            logger.info(f"Symbol: {symbol}, Signal: {signal}")
            if signal is not None:
                store_trading_signal.delay(
                    symbol=signal.symbol,
                    timeframe=signal.timeframe,
                    signal_type=signal.signal_type.value,
                    confidence=signal.confidence,
                    algorithms=signal.algorithms_triggered
                )

    # Run the async function
    async_to_sync(task_logic)()
