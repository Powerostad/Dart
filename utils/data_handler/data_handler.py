import asyncio
from datetime import datetime
from utils.data_handler.metatrader import MetaTraderManager
from utils.timeframes import mt5


class RealTimeDataHandler:
    def __init__(self, symbols, timeframe=None):
        self.symbols = symbols
        self.timeframe = timeframe if timeframe else 5  # Default to 5-minute data
        self.data_manager = MetaTraderManager(self.symbols, self.timeframe)
        self.current_data = None
        self.last_update_time = None

    async def update_data(self):
        """Asynchronously update data if necessary."""
        current_time = datetime.now()

        if self.last_update_time is None or self._should_update(current_time):
            self.current_data = await self.data_manager.get_historical_data()  # Await the async call to get data
            self.last_update_time = current_time

    def _should_update(self, current_time):
        """Check if the data should be updated based on timeframe and time passed."""
        if self.last_update_time is None:
            return True

        time_diff = (current_time - self.last_update_time).seconds

        if self.timeframe == mt5.TIMEFRAME_M1:  # 1-minute timeframe
            return time_diff >= 60
        elif self.timeframe == mt5.TIMEFRAME_M5:  # 5-minute timeframe
            return time_diff >= 300
        elif self.timeframe == mt5.TIMEFRAME_H1:  # 1-hour timeframe
            return time_diff >= 3600

        return True

    async def get_data(self):
        """Get the most recent data, updating if necessary."""
        await self.update_data()  # Asynchronously update data
        return self.current_data
