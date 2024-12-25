import logging

import numpy as np
from statsmodels.nonparametric.kernel_regression import KernelReg
import pandas_ta as ta
import pandas as pd
from utils.algorithms.base import TradingAlgorithm, SignalType


class AligatorAlgorithm(TradingAlgorithm):
    def __init__(self):
        super().__init__("Aligator_Strategy")
        self.mysize = 0.1
        self.TPSLRatio = 1.5
        self.perc = 0.02
        self.n_backcandles = 10

    def generate_signal(self, data: pd.DataFrame) -> SignalType:
        """
        Generate signal based on Aligator strategy.

        Args:
            data (pd.DataFrame): Market data

        Returns:
            SignalType: Buy, Sell, or Neutral signal
        """
        if len(data) < self.n_backcandles:
            return SignalType.NEUTRAL

        # Data preparation
        data = data.copy()
        data.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close"}, inplace=True)
        data = data[data.High != data.Low]

        # Calculate indicators
        data["SMA_1"] = ta.sma(data.Close, length=5).shift(3)
        data["SMA_2"] = ta.sma(data.Close, length=8).shift(5)
        data["SMA_3"] = ta.sma(data.Close, length=13).shift(8)
        data["EMA"] = ta.ema(data.Close, length=200)

        # Calculate SMA signals
        sma_buy = 0
        sma_sell = 0

        for i in range(self.n_backcandles):
            if (
                data.iloc[-i - 1]["SMA_1"] > data.iloc[-i - 1]["SMA_2"] > data.iloc[-i - 1]["SMA_3"]
                and data.iloc[-i - 1]["Low"] > data.iloc[-i - 1]["SMA_3"]
            ):
                sma_buy += 1

            if (
                data.iloc[-i - 1]["SMA_1"] < data.iloc[-i - 1]["SMA_2"] < data.iloc[-i - 1]["SMA_3"]
                and data.iloc[-i - 1]["High"] < data.iloc[-i - 1]["SMA_3"]
            ):
                sma_sell += 1

        # Determine Total Signal
        if sma_buy >= 5 and data.iloc[-1]["Close"] > data.iloc[-1]["EMA"]:
            return SignalType.BUY

        if sma_sell >= 5 and data.iloc[-1]["Close"] < data.iloc[-1]["EMA"]:
            return SignalType.SELL

        return SignalType.NEUTRAL


class MHarrisSystematic(TradingAlgorithm):
    def __init__(self):
        super().__init__("MHarris_Strategy")

    def generate_signal(self, data: pd.DataFrame) -> SignalType:
        """
        Generate signal based on M. Harris Systematic strategy.

        Args:
            data (pd.DataFrame): Market data

        Returns:
            SignalType: Buy, Sell, or Neutral signal
        """
        if len(data) < 5:
            return SignalType.NEUTRAL

        # Ensure data is in the correct format
        data = data.copy()
        data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close'}, inplace=True)
        data = data[data.High != data.Low]

        def calculate_signal(current_pos: int) -> int:
            c1 = data['Low'].iloc[current_pos - 4] > data['High'].iloc[current_pos]
            c2 = data['High'].iloc[current_pos] > data['Low'].iloc[current_pos - 3]
            c3 = data['Low'].iloc[current_pos - 3] > data['Low'].iloc[current_pos - 2]
            c4 = data['Low'].iloc[current_pos - 2] > data['Low'].iloc[current_pos - 1]
            c5 = data['Close'].iloc[current_pos] > data['High'].iloc[current_pos - 1]

            if c1 and c2 and c3 and c4 and c5:
                return 2

            c1 = data['High'].iloc[current_pos - 4] < data['Low'].iloc[current_pos]
            c2 = data['Low'].iloc[current_pos] < data['High'].iloc[current_pos - 3]
            c3 = data['High'].iloc[current_pos - 3] < data['High'].iloc[current_pos - 2]
            c4 = data['High'].iloc[current_pos - 2] < data['High'].iloc[current_pos - 1]
            c5 = data['Close'].iloc[current_pos] < data['Low'].iloc[current_pos - 1]

            if c1 and c2 and c3 and c4 and c5:
                return 1

            return 0

        current_candle = data.index[-1]
        current_pos = data.index.get_loc(current_candle)

        if current_pos < 4:
            return SignalType.NEUTRAL

        total_signal = calculate_signal(current_pos)

        if total_signal == 2:
            return SignalType.BUY
        elif total_signal == 1:
            return SignalType.SELL

        return SignalType.NEUTRAL


class NadayaraWatsonFullStrategy15Min(TradingAlgorithm):
    def __init__(self):
        # Initialization
        super().__init__("Nadayara_Watson_Strategy")
        self.backcandles = 10
        self.bw = 7

    def generate_signal(self, data: pd.DataFrame) -> SignalType:
        """
        Generate signal based on Nadayara Watson strategy.

        Args:
            data (pd.DataFrame): Market data

        Returns:
            SignalType: Buy, Sell, or Neutral signal
        """
        if len(data) < self.backcandles:
            return SignalType.NEUTRAL

        # Ensure data is in the correct format
        data = data.copy()
        data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close'}, inplace=True)
        data = data[data.High != data.Low]

        # Calculate necessary indicators
        data["EMA_slow"] = ta.ema(data.Close, length=50)
        data["EMA_fast"] = ta.ema(data.Close, length=40)
        data['ATR'] = ta.atr(data.High, data.Low, data.Close, length=7)

        # Envelope Calculation
        for current_candle_index in range(self.backcandles, len(data)):
            middle, upper, lower = self.__compute_envelopes(data, current_candle_index, self.backcandles, self.bw)
            data.at[current_candle_index, 'Middle_Envelope'] = middle
            data.at[current_candle_index, 'Upper_Envelope'] = upper
            data.at[current_candle_index, 'Lower_Envelope'] = lower

        # Bollinger Bands and Signal Calculations
        my_bbands = ta.bbands(data.Close, length=10, std=2)
        data = data.join(my_bbands)

        # EMA Signal
        above = data['EMA_fast'] > data['EMA_slow']
        below = data['EMA_fast'] < data['EMA_slow']
        above_all = above.rolling(window=self.backcandles).apply(lambda x: x.all(), raw=True).fillna(0).astype(bool)
        below_all = below.rolling(window=self.backcandles).apply(lambda x: x.all(), raw=True).fillna(0).astype(bool)

        data['EMASignal'] = 0
        data.loc[above_all, 'EMASignal'] = 2
        data.loc[below_all, 'EMASignal'] = 1

        # Total Signal Calculation
        condition_sell = (data['EMASignal'] == 2) & (data['Close'] <= data['BBL_10_2.0'])
        condition_buy = (data['EMASignal'] == 1) & (data['Close'] >= data['BBU_10_2.0'])
        data['Total_Signal'] = 0
        data.loc[condition_sell, 'Total_Signal'] = 1
        data.loc[condition_buy, 'Total_Signal'] = 2

        # Final Signal
        signal = data['Total_Signal'].iloc[-1]

        if signal == 2:
            return SignalType.BUY
        elif signal == 1:
            return SignalType.SELL

        return SignalType.NEUTRAL

    def __compute_envelopes(self, df, current_candle_index, backcandles, bw=3):
        # Slice the DataFrame to include only the past candles up to the current candle index
        start_index = max(current_candle_index - backcandles, 0)
        dfsample = df[start_index:current_candle_index + 1].copy()  # current candle included
        dfsample.reset_index(drop=True, inplace=True)

        # Create the Kernel Regression model
        X = dfsample.index
        model = KernelReg(endog=dfsample['Close'], exog=X, var_type='c', reg_type='lc', bw=[bw])
        fitted_values, _ = model.fit()

        # Calculate residuals and standard deviation of residuals
        residuals = dfsample['Close'] - fitted_values
        std_dev = 2. * np.std(residuals)

        # Calculate the envelopes
        middle = fitted_values[-1]
        upper = middle + std_dev
        lower = middle - std_dev

        return middle, upper, lower

    