import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Optional

import aiocache
import pandas as pd
from asgiref.sync import sync_to_async
from mt5linux import MetaTrader5
from django.conf import settings
from utils.utils import async_retry
from celery.utils.log import get_task_logger

logger = get_task_logger("tasks")


class AsyncMT5Controller:
    _instance = None
    _lock = asyncio.Lock()
    _connection_pool: Dict[str, 'AsyncMT5Controller'] = {}

    def __init__(self, connection_id: str = 'default'):
        self.active_symbols = None
        self.connection_id = connection_id
        self.host = settings.METATRADER_URL
        self.port = settings.METATRADER_PORT
        self.mt5: Optional[MetaTrader5] = None
        self._initialized = False

        self.timeframe_map = {
            "1m": MetaTrader5.TIMEFRAME_M1,
            "5m": MetaTrader5.TIMEFRAME_M5,
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
            self.mt5 = MetaTrader5(self.host, int(self.port))
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
                rates = self.mt5.copy_rates_from_pos(
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
                pass

    @async_retry(retries=3, delay=1)
    async def get_mt5_symbols(self, number_of_top_symbols:int=100):
        # cache_key = f"top_{number_of_top_symbols}_symbols"
        # cached_data = await self.cache.get(cache_key)
        # if cached_data is not None:
        #     return cached_data
        async with self.connection():
            try:
                symbols_wanted = [
                    "EURUSD", "USDJPY", "GBPUSD", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD",
                    "BTCUSD", "ETHUSD", "SOLUSD", "XRPUSD", "DOGEUSD", "BNBUSD", "AVAXUSD",
                    "TSLA", "AAPL", "COIN", "GOOGL", "FB", "AMZN", "NFLX", "PFE",
                    "US30", "US500", "DE40", "UK100", "JP225", "NAS100",
                    "XAUUSD", "XAGUSD", "USOIL", "UKOIL", "XPTUSD", "XPDUSD"
                ]

                # Convert that list to a single comma-separated string
                symbols_str = ",".join(symbols_wanted)

                symbols = self.mt5.symbols_get(group=symbols_str)
                logger.info(f"Founded Symbols:\n {symbols}")
                symbol_names = [symbol.name for symbol in symbols]
                # active_symbols = []
                # for symbol in symbol_names:
                #     try:
                #         data = await self.get_historical_data_candles(symbol, timeframe="daily", lookback=10)
                #         if data is not None and not data.empty:
                #             avg_volume = data['tick_volume'].mean()
                #             active_symbols.append((symbol, avg_volume))
                #     except Exception as e:
                #         raise e
                #         logger.error(f"error on getting data: {str(e)}")
                #         continue
                #
                # active_symbols.sort(key=lambda x: x[1], reverse=True)
                # self.active_symbols = list({symbol for symbol, _ in active_symbols})[:number_of_top_symbols]
                self.active_symbols = symbol_names
                # await self.cache.set(cache_key, symbol_names, ttl=86400) # 24 Hour
                return self.active_symbols
            except Exception as e:
                logger.error(f"Unexpected Error on getting symbols: {str(e)}")
                raise

    @async_retry(retries=3, delay=1)
    async def get_current_price(self, symbol: str, price_type: str = "ask") -> float:
        """
            Retrieve the current market price for a given symbol.

            Args:
                symbol (str): The trading symbol to fetch the current price for.
                price_type (str, optional): The type of price to retrieve.
                    Defaults to 'ask'. Options include:
                    - 'ask': Current ask (lowest seller's price)
                    - 'bid': Current bid (highest buyer's price)
                    - 'last': Last traded price

            Returns:
                float: Current market price for the specified symbol.

            Raises:
                ValueError: If an invalid price type is specified.
                Exception: If there are issues retrieving the price from MT5.
            """
        valid_price_types = ["ask", "bid", "last"]
        if price_type not in valid_price_types:
            raise ValueError(f"Invalid price type: {price_type}")

        cache_key = f"current_price_{symbol}_{price_type}"
        cache = await self.cache.get(cache_key)
        if cache is not None:
            return cache

        async with self.connection():
            try:
                symbol_info = self.mt5.symbol_info(symbol)
                if not symbol_info:
                    raise ValueError(f"Symbol {symbol} not found on MT5")
                if price_type == "ask":
                    current_price = symbol_info.ask
                elif price_type == "bid":
                    current_price = symbol_info.bid
                else:
                    current_price = symbol_info.last

                if current_price is None or current_price <= 0:
                    raise ValueError(f"Invalid price for {symbol}")

                await self.cache.set(cache_key, current_price, ttl=60)
                return current_price
            except Exception as e:
                logger.error(f"Unexpected Error on getting current price for symbol {symbol}: {str(e)}")
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