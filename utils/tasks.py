from asgiref.sync import async_to_sync
from celery import shared_task
import asyncio
from typing import List
from celery.utils.log import get_task_logger
from channels.layers import get_channel_layer
from gevent.hub import signal

from utils.controllers.metatrader import AsyncMT5Controller
from utils.controllers.signal import SignalController, SignalGenerationConfig
from apps.forex.models import Signal, SignalStatus
from utils.algorithms.base import SignalType
from django.conf import settings

channel_layer = get_channel_layer()


try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

logger = get_task_logger(__name__)

SIGNAL_CONFIG = SignalGenerationConfig(
    timeframes=settings.TRADING_TIMEFRAMES,
    algorithm_classes=settings.TRADING_ALGORITHMS,
    confidence_threshold=settings.SIGNAL_CONFIDENCE_THRESHOLD,
)

mt5_controller: AsyncMT5Controller = async_to_sync(AsyncMT5Controller.get_instance)()
controller: SignalController = loop.run_until_complete(SignalController.create(SIGNAL_CONFIG))


@shared_task
def store_trading_signal(
        symbol: str,
        timeframe: str,
        signal_type: str,
        confidence: float,
        algorithms: List[str],
        current_price: float
) -> None:
    """
    Store trading signal in database with enhanced parameters
    """
    logger.info("Storing advanced trading signal in database")

    signal_direction = SignalType(signal_type)

    signal = Signal.create_signal(
        symbol=symbol,
        timeframe=timeframe,
        signal_type=signal_direction,
        confidence=confidence,
        algorithms=algorithms,
        current_price=current_price
    )

    logger.info(f"Advanced Signal created for {symbol} with status: {signal.status}")


@shared_task(max_retries=3)
def one_minute_signal():
    """
    Generate and store 1-minute trading signals
    """

    async def task_logic():
        # Fetch symbols and generate signals
        symbols = await mt5_controller.get_mt5_symbols()

        for symbol in symbols:
            try:
                current_ask_price = await mt5_controller.get_current_price(symbol, price_type="ask")
                current_bid_price = await mt5_controller.get_current_price(symbol, price_type="bid")
                signal = await controller.generate_signals_for_symbol(
                    symbol=symbol,
                    timeframe="1m"
                )
                if signal is not None:
                    signal_data = {
                        "symbol": signal.symbol,
                        "timeframe": signal.timeframe,
                        "signal_type": signal.signal_type,
                        "confidence": signal.confidence,
                        "current_price": current_ask_price if signal.signal_type == SignalType.BUY else current_bid_price,
                        "algorithms": signal.algorithms_triggered
                    }
                    store_trading_signal.delay(
                        **signal_data
                    )
                    # channel_layer.group_send(
                    # "signal_notifications",
                    # {
                    #     'type': 'signal_notification',
                    #     'signal': signal_data
                    # })
            except Exception as e:
                logger.error(f"Error processing {symbol}: {str(e)}")

    # Run the async function
    async_to_sync(task_logic)()


@shared_task(max_retries=3)
def five_minute_signal():
    """
    Generate and store 5-minute trading signals
    """

    async def task_logic():
        # Fetch symbols and generate signals
        symbols = await mt5_controller.get_mt5_symbols()

        for symbol in symbols:
            try:
                current_ask_price = await mt5_controller.get_current_price(symbol, price_type="ask")
                current_bid_price = await mt5_controller.get_current_price(symbol, price_type="bid")
                signal = await controller.generate_signals_for_symbol(
                    symbol=symbol,
                    timeframe="5m"
                )
                if signal is not None:
                    store_trading_signal.delay(
                        symbol=signal.symbol,
                        timeframe=signal.timeframe,
                        signal_type=signal.signal_type.value,
                        confidence=signal.confidence,
                        algorithms=signal.algorithms_triggered,
                        current_price=current_ask_price if signal.signal_type == SignalType.BUY else current_bid_price,
                    )
            except Exception as e:
                logger.error(f"Error processing {symbol}: {str(e)}")

    # Run the async function
    async_to_sync(task_logic)()

@shared_task(max_retries=3)
def fifteen_minute_signal():
    """
    Generate and store 15-minute trading signals
    """

    async def task_logic():
        # Fetch symbols and generate signals
        symbols = await mt5_controller.get_mt5_symbols()

        for symbol in symbols:
            try:
                current_ask_price = await mt5_controller.get_current_price(symbol, price_type="ask")
                current_bid_price = await mt5_controller.get_current_price(symbol, price_type="bid")
                signal = await controller.generate_signals_for_symbol(
                    symbol=symbol,
                    timeframe="15m"
                )
                if signal is not None:
                    store_trading_signal.delay(
                        symbol=signal.symbol,
                        timeframe=signal.timeframe,
                        signal_type=signal.signal_type.value,
                        confidence=signal.confidence,
                        algorithms=signal.algorithms_triggered,
                        current_price=current_ask_price if signal.signal_type == SignalType.BUY else current_bid_price,
                    )
            except Exception as e:
                logger.error(f"Error processing {symbol}: {str(e)}")

    # Run the async function
    async_to_sync(task_logic)()

@shared_task
def update_signal_statuses():
    """
    Periodic task to update signal statuses
    """
    active_signals = Signal.objects.filter(
        status__in=[
            SignalStatus.PENDING.name,
            SignalStatus.ACTIVE.name
        ]
    )

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    for signal in active_signals:
        try:
            current_price = loop.run_until_complete(mt5_controller.get_current_price(signal.symbol))
            signal.update_signal_status(current_price)
        except Exception as e:
            logger.error(f"Error updating signal {signal.id}: {str(e)}")
            continue

    Signal.cleanup_expired_signals()
    loop.close()