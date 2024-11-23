from datetime import datetime, timedelta

from utils.data_handler.data_handler import RealTimeDataHandler
from utils.data_handler.metatrader import MetaTraderManager
from utils.position_manager.position_manager import PositionManager
from utils.timeframes import mt5


class SignalManager:
    def __init__(self, symbol, timeframe=mt5.TIMEFRAME_M1, max_positions=10):
        self.symbol = symbol
        self.timeframe = timeframe
        self.max_positions = max_positions
        self.algorithms = []
        self.last_trade_time = None
        self.data_handler = RealTimeDataHandler(symbol, timeframe)
        self.position_manager = PositionManager(max_positions=max_positions)
        self.minimum_trade_interval = timedelta(minutes=5)

        self.risk_percent = 0.02  # 2% risk per trade
        self.reward_ratio = 2.0  # Risk:Reward ratio (1:2)

        # Get symbol info for pip value calculations
        self.symbol_info = MetaTraderManager(symbol, timeframe).get_symbol_info()


    def add_algorithm(self, algorithm):
        self.algorithms.append(algorithm)

    def get_signal(self):
        self.data_handler.update_data()
        if not self._can_trade():
            return "hold"
        signals = []
        for algorithm in self.algorithms:
            signal = algorithm.get_signal(self.data_handler.get_data())
            signals.append(signal)

        return self._process_signals(signals)


    def _can_trade(self):
        """Check if enough time has passed since last trade"""
        current_time = datetime.now()
        if (self.last_trade_time is None or
            current_time - self.last_trade_time >= self.minimum_trade_interval):
            return True
        return False

    def _process_signals(self, signals):
        # Count signals
        buy_count = 0
        sell_count = 0
        hold_count = 0

        for signal in signals:
            if signal == 0:
                hold_count += 1
            elif signal == 1:
                sell_count += 1
            elif signal == 2:
                buy_count += 1

        total_signals = len(signals)
        if buy_count / total_signals >= 0.7:
            return 'buy'
        elif sell_count / total_signals >= 0.7:
            return 'sell'
        return 'hold'

    def buy(self, entry, sl, tp):
        pass

    def sell(self, entry, sl, tp):
        pass