import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Optional

import aiocache
import pandas as pd
from asgiref.sync import sync_to_async
from mt5linux import MetaTrader5
from django.conf import settings
from utils.utils import async_retry
from logging import getLogger

logger = getLogger(__name__)


class AsyncMT5Controller:
    _instance = None
    _lock = asyncio.Lock()
    _connection_pool: Dict[str, 'AsyncMT5Controller'] = {}

    def __init__(self, connection_id: str = 'default'):
        self.connection_id = connection_id
        self.host = settings.METATRADER_URL
        self.port = settings.METATRADER_PORT
        self.mt5: Optional[MetaTrader5] = None
        self._initialized = False

        self.timeframe_map = {
            '15m': MetaTrader5.TIMEFRAME_M15,
            '1h': MetaTrader5.TIMEFRAME_H1,
            '4h': MetaTrader5.TIMEFRAME_H4,
            'daily': MetaTrader5.TIMEFRAME_D1
        }

        self.cache = aiocache.Cache(aiocache.SimpleMemoryCache)

    @classmethod
    async def get_instance(cls, connection_id: str = 'default') -> 'AsyncMT5Controller':
        async with cls._lock:
            if connection_id not in cls._connection_pool:
                controller = cls(connection_id)
                await controller._initialize()
                cls._connection_pool[connection_id] = controller
            return cls._connection_pool[connection_id]

    @async_retry(retries=3, delay=1)
    async def _initialize(self) -> None:
        if self._initialized:
            return

        try:
            self.mt5 = MetaTrader5(self.host, self.port)
            success = await sync_to_async(self.mt5.initialize)()

            if not success:
                raise ConnectionError("Failed To Initialize MetaTrader5!")

            self._initialized = True
            logger.info('MetaTrader5 Initialized')
        except Exception as e:
            logger.error("Unexpected Error on initializing MetaTrader5: ", str(e))
            self._initialized = False
            raise


    @asynccontextmanager
    async def connection(self):
        if not self._initialized:
            await self._initialize()

        try:
            yield self
        except Exception as e:
            logger.error("MetaTrader5 Connection Error: ", str(e))
            self._initialized = False
            raise

    @async_retry(retries=3, delay=1)
    async def get_historical_data_candles(self, symbol, timeframe, lookback: int = 300) -> pd.DataFrame:
        cache_key = f"candles_{symbol}_{timeframe}_{lookback}_{self.connection_id}"
        cached_data = await self.cache.get(cache_key)
        if cached_data is not None:
            return pd.DataFrame(cached_data)

        async with self.connection():
            try:
                rates = await sync_to_async(self.mt5.copy_rates_from_pos)(
                    symbol,
                    self.timeframe_map.get(timeframe, self.mt5.TIMEFRAME_M15),
                    0,
                    lookback
                )

                if rates is None:
                    raise Exception("Failed to retrieve historical data for {}".format(symbol))

                df = pd.DataFrame(rates)
                df['time'] = pd.to_datetime(df['time'], unit='s')
                df.set_index('time', inplace=True)

                await self.cache.set(cache_key, df.to_dict("records"), ttl=60)

                return df
            except Exception as e:
                logger.error(f"Unexpected Error on getting historical data candles: {str(e)}")
                raise

    @async_retry(retries=3, delay=1)
    async def get_mt5_symbols(self):
        cache_key = f"symbols_{self.connection_id}"
        cached_data = await self.cache.get(cache_key)
        if cached_data is not None:
            return cached_data

        async with self.connection():
            try:
                symbols = await sync_to_async(self.mt5.symbols_get)()
                symbol_names = [symbol.name for symbol in symbols]

                await self.cache.set(cache_key, symbol_names, ttl=60)
                print("IN GET_MT5_SYMBOLS: ", symbol_names)
                return symbol_names
            except Exception as e:
                logger.error(f"Unexpected Error on getting symbols: {str(e)}")
                raise


    @classmethod
    async def cleanup_connections(cls) -> None:
        """
        Cleanup all MT5 connections in the pool
        """
        async with cls._lock:
            for connection_id, controller in cls._connection_pool.items():
                try:
                    if controller.mt5:
                        await sync_to_async(controller.mt5.shutdown)()
                    logger.info(f"Cleaned up MT5 connection: {connection_id}")
                except Exception as e:
                    logger.error(f"Error cleaning up connection {connection_id}: {str(e)}")
            cls._connection_pool.clear()