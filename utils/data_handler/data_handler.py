from datetime import datetime

from utils.data_handler.metatrader import MetaTraderManager
from utils.timeframes import mt5


class RealTimeDataHandler:
    def __init__(self, symbol, timeframe=None):
        self.symbol = symbol
        self.timeframe = timeframe if timeframe else 5 # number for 5 minute data
        self.data_manager = MetaTraderManager(self.symbol, self.timeframe)
        self.current_data = None
        self.last_update_time = None

    def update_data(self):
        current_time = datetime.now()

        if self.last_update_time is None or self._should_update(current_time):
            self.current_data = self.data_manager.get_historical_data()
            self.last_update_time = current_time

    def _should_update(self, current_time):
        if self.last_update_time is None:
            return True

        if self.timeframe == mt5.TIMEFRAME_M1:
            return (current_time - self.last_update_time).seconds >= 60
        elif self.timeframe == mt5.TIMEFRAME_M5:
            return (current_time - self.last_update_time).seconds >= 300
        elif self.timeframe == mt5.TIMEFRAME_H1:
            return (current_time - self.last_update_time).seconds >= 3600

        return True

    def get_data(self):
        self.update_data()
        return self.current_data