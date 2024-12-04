import pandas as pd
import aiohttp
import asyncio
from django.conf import settings


class MetaTraderManager:
    def __init__(self, symbols, timeframe):
        self.symbols = symbols
        self.timeframe = timeframe

        self.base_url = settings.METATRADER_URL
        self.historical_data_urls = [self.base_url + f"{symbol}/" for symbol in self.symbols]
        self.symbol_info_urls = [self.base_url + f"info/{symbol}/" for symbol in self.symbols]

    async def _fetch_data(self, url, params=None):
        """Helper function to fetch data asynchronously using aiohttp."""
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                response.raise_for_status()  # Raise an exception for HTTP errors
                return await response.json()

    async def get_historical_data(self):
        try:
            # Asynchronously fetch historical data for all symbols
            tasks = [
                self._fetch_data(url, params={"timeframe": self.timeframe}) for url in self.historical_data_urls
            ]
            responses = await asyncio.gather(*tasks)  # Gather all the results

            # Create a dictionary where each symbol is the key
            symbol_data = {}
            for symbol, response in zip(self.symbols, responses):
                symbol_data[symbol] = pd.DataFrame.from_dict(response)  # Associate symbol with DataFrame

            return symbol_data
        except Exception as e:
            print(f"Error in getting historical data from MetaTrader: {e}")
            return None

    async def get_symbol_info(self):
        try:
            # Asynchronously fetch symbol info for all symbols
            tasks = [self._fetch_data(url) for url in self.symbol_info_urls]
            responses = await asyncio.gather(*tasks)

            # Create a dictionary where each symbol is the key
            symbol_info = {}
            for symbol, response in zip(self.symbols, responses):
                symbol_info[symbol] = response  # Associate symbol with symbol info

            return symbol_info
        except Exception as e:
            print(f"Error in getting symbol info from MetaTrader: {e}")
            return None
