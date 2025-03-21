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
        if len(data) < 5:
            return SignalType.NEUTRAL

        data = data.copy()
        data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close'}, inplace=True)
        data = data[data.High != data.Low]

        if len(data) < 5:
            return SignalType.NEUTRAL

        def calculate_signal(current_pos: int) -> int:
            # Buy conditions (higher lows)
            c1 = data['Low'].iloc[current_pos - 4] > data['High'].iloc[current_pos]
            c2 = data['High'].iloc[current_pos] > data['Low'].iloc[current_pos - 3]
            c3 = data['Low'].iloc[current_pos - 3] < data['Low'].iloc[current_pos - 2]  # Higher low
            c4 = data['Low'].iloc[current_pos - 2] < data['Low'].iloc[current_pos - 1]  # Higher low
            c5 = data['Close'].iloc[current_pos] > data['High'].iloc[current_pos - 1]

            if c1 and c2 and c3 and c4 and c5:
                return 2  # Buy

            # Sell conditions (lower highs)
            c1 = data['High'].iloc[current_pos - 4] < data['Low'].iloc[current_pos]
            c2 = data['Low'].iloc[current_pos] < data['High'].iloc[current_pos - 3]
            c3 = data['High'].iloc[current_pos - 3] > data['High'].iloc[current_pos - 2]  # Lower high
            c4 = data['High'].iloc[current_pos - 2] > data['High'].iloc[current_pos - 1]  # Lower high
            c5 = data['Close'].iloc[current_pos] < data['Low'].iloc[current_pos - 1]

            if c1 and c2 and c3 and c4 and c5:
                return 1  # Sell

            return 0

        current_candle = data.index[-1]
        current_pos = data.index.get_loc(current_candle)
        print(f"current POS: {current_candle}")

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
        super().__init__("Nadayara_Watson_Strategy")
        self.backcandles = 10
        self.bw = 7

    def generate_signal(self, data: pd.DataFrame) -> SignalType:
        if len(data) < 50:
            return SignalType.NEUTRAL

        data = data.copy()
        data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close'}, inplace=True)
        data = data[data.High != data.Low]

        if len(data) < 50:
            return SignalType.NEUTRAL

        data["EMA_slow"] = ta.ema(data.Close, length=50)
        data["EMA_fast"] = ta.ema(data.Close, length=40)
        data['ATR'] = ta.atr(data.High, data.Low, data.Close, length=7)

        for current_candle_index in range(self.backcandles, len(data)):
            middle, upper, lower = self.__compute_envelopes(data, current_candle_index, self.backcandles, self.bw)
            data.at[current_candle_index, 'Middle_Envelope'] = middle
            data.at[current_candle_index, 'Upper_Envelope'] = upper
            data.at[current_candle_index, 'Lower_Envelope'] = lower

        my_bbands = ta.bbands(data.Close, length=10, std=2)
        data = data.join(my_bbands)

        # Adjusted to use majority (5/10 periods)
        above = data['EMA_fast'] > data['EMA_slow']
        below = data['EMA_fast'] < data['EMA_slow']
        above_majority = above.rolling(window=self.backcandles).apply(lambda x: x.sum() >= 5, raw=True).fillna(0).astype(bool)
        below_majority = below.rolling(window=self.backcandles).apply(lambda x: x.sum() >= 5, raw=True).fillna(0).astype(bool)

        data['EMASignal'] = 0
        data.loc[above_majority, 'EMASignal'] = 2  # Uptrend
        data.loc[below_majority, 'EMASignal'] = 1  # Downtrend

        # Corrected signal conditions
        condition_buy = (data['EMASignal'] == 2) & (data['Close'] <= data['BBL_10_2.0'])  # Buy dip in uptrend
        condition_sell = (data['EMASignal'] == 1) & (data['Close'] >= data['BBU_10_2.0'])  # Sell peak in downtrend

        data['Total_Signal'] = 0
        data.loc[condition_buy, 'Total_Signal'] = 2
        data.loc[condition_sell, 'Total_Signal'] = 1

        signal = data['Total_Signal'].iloc[-1]

        if signal == 2:
            return SignalType.BUY
        elif signal == 1:
            return SignalType.SELL

        return SignalType.NEUTRAL

    def __compute_envelopes(self, df, current_candle_index, backcandles, bw=3):
        start_index = max(current_candle_index - backcandles, 0)
        dfsample = df[start_index:current_candle_index + 1].copy()
        dfsample.reset_index(drop=True, inplace=True)

        X = dfsample.index
        model = KernelReg(endog=dfsample['Close'], exog=X, var_type='c', reg_type='lc', bw=[bw])
        fitted_values, _ = model.fit()

        residuals = dfsample['Close'] - fitted_values
        std_dev = 2. * np.std(residuals)

        middle = fitted_values[-1]
        upper = middle + std_dev
        lower = middle - std_dev

        return middle, upper, lower


class SMCTrading(TradingAlgorithm):
    def __init__(self):
        super().__init__("SMC_Strategy")
        self.atr_period = 14

    def generate_signal(self, data: pd.DataFrame) -> SignalType:
        # Check initial data requirements
        if len(data) < 20:  # Minimum data for SMC calculations
            return SignalType.NEUTRAL

        # Prepare dataframe copy with expected column names
        df = data.copy().rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close'
        }, errors='ignore')

        # Filter invalid candles
        df = df[df['High'] != df['Low']]
        if len(df) < 20:
            return SignalType.NEUTRAL

        # Calculate features
        df = self._calculate_basic_features(df)
        df = self._identify_order_blocks(df)
        df = self._identify_fair_value_gaps(df)
        df = self._identify_liquidity_levels(df)
        df = self._identify_mitigation_points(df)
        df = self._identify_trade_setups(df)

        # Check last 3 candles for setups
        recent_data = df.iloc[-3:]
        for i in reversed(range(len(recent_data))):
            if recent_data.iloc[i]['buy_setup']:
                return SignalType.BUY
            if recent_data.iloc[i]['sell_setup']:
                return SignalType.SELL

        return SignalType.NEUTRAL

    def _calculate_basic_features(self, df):
        """Calculate technical features used in SMC analysis"""
        df = df.copy()
        df['body_size'] = abs(df['Close'] - df['Open'])
        df['upper_wick'] = df['High'] - df[['Open', 'Close']].max(axis=1)
        df['lower_wick'] = df[['Open', 'Close']].min(axis=1) - df['Low']
        df['bullish'] = df['Close'] > df['Open']
        df['candle_range'] = df['High'] - df['Low']

        # Calculate True Range and ATR
        df['tr'] = np.maximum(
            df['High'] - df['Low'],
            np.maximum(
                abs(df['High'] - df['Close'].shift(1)),
                abs(df['Low'] - df['Close'].shift(1))
            )
        )
        df['atr'] = df['tr'].rolling(self.atr_period).mean()
        return df

    def _identify_order_blocks(self, df):
        """Identify bullish/bearish order blocks"""
        df = df.copy()
        window_size = 5

        # Initialize columns
        df['bullish_ob'] = False
        df['bearish_ob'] = False
        df['bullish_ob_strength'] = 0.0
        df['bearish_ob_strength'] = 0.0

        # Identify swing points
        df['swing_high'] = df['High'].rolling(window_size, center=True).apply(
            lambda x: x[window_size // 2] == np.max(x), raw=True)
        df['swing_low'] = df['Low'].rolling(window_size, center=True).apply(
            lambda x: x[window_size // 2] == np.min(x), raw=True)

        # Find bullish order blocks
        for i in range(3, len(df) - 3):
            if (not df.iloc[i]['bullish'] and
                    df.iloc[i + 1:i + 4]['Close'].max() > df.iloc[i - 2:i + 1]['High'].max()):
                df.loc[df.index[i], 'bullish_ob'] = True
                move = df.iloc[i + 1:i + 4]['Close'].max() - df.iloc[i]['Low']
                df.loc[df.index[i], 'bullish_ob_strength'] = move / df.iloc[i]['atr']

        # Find bearish order blocks
        for i in range(3, len(df) - 3):
            if (df.iloc[i]['bullish'] and
                    df.iloc[i + 1:i + 4]['Close'].min() < df.iloc[i - 2:i + 1]['Low'].min()):
                df.loc[df.index[i], 'bearish_ob'] = True
                move = df.iloc[i]['High'] - df.iloc[i + 1:i + 4]['Close'].min()
                df.loc[df.index[i], 'bearish_ob_strength'] = move / df.iloc[i]['atr']

        return df

    def _identify_fair_value_gaps(self, df):
        """Identify Fair Value Gaps in price action"""
        df = df.copy()
        df['bullish_fvg'] = False
        df['bearish_fvg'] = False

        for i in range(2, len(df)):
            # Bullish FVG (current low > previous high)
            if df.iloc[i]['Low'] > df.iloc[i - 2]['High']:
                df.loc[df.index[i], 'bullish_fvg'] = True

            # Bearish FVG (current high < previous low)
            if df.iloc[i]['High'] < df.iloc[i - 2]['Low']:
                df.loc[df.index[i], 'bearish_fvg'] = True

        return df

    def _identify_liquidity_levels(self, df):
        """Identify key liquidity zones"""
        df = df.copy()
        window = 5
        df['buy_liquidity'] = False
        df['sell_liquidity'] = False

        # Swing lows (buy liquidity)
        for i in range(window, len(df) - window):
            if all(df.iloc[i]['Low'] < df.iloc[i - window:i]['Low']) and \
                    all(df.iloc[i]['Low'] < df.iloc[i + 1:i + window + 1]['Low']):
                df.loc[df.index[i], 'buy_liquidity'] = True

        # Swing highs (sell liquidity)
        for i in range(window, len(df) - window):
            if all(df.iloc[i]['High'] > df.iloc[i - window:i]['High']) and \
                    all(df.iloc[i]['High'] > df.iloc[i + 1:i + window + 1]['High']):
                df.loc[df.index[i], 'sell_liquidity'] = True

        return df

    def _identify_mitigation_points(self, df):
        """Identify price mitigation points"""
        df = df.copy()
        df['high_mitigation'] = False
        df['low_mitigation'] = False

        for i in range(5, len(df)):
            # High mitigation
            recent_high = df.iloc[i - 5:i]['High'].max()
            if df.iloc[i]['High'] >= recent_high and df.iloc[i - 1]['High'] < recent_high:
                df.loc[df.index[i], 'high_mitigation'] = True

            # Low mitigation
            recent_low = df.iloc[i - 5:i]['Low'].min()
            if df.iloc[i]['Low'] <= recent_low and df.iloc[i - 1]['Low'] > recent_low:
                df.loc[df.index[i], 'low_mitigation'] = True

        return df

    def _identify_trade_setups(self, df):
        """Identify complete SMC trade setups"""
        df = df.copy()
        df['buy_setup'] = False
        df['sell_setup'] = False

        for i in range(5, len(df)):
            # Bullish setup criteria
            bull_cond = (
                    (df.iloc[i - 5:i]['bullish_ob'].any() |
                     df.iloc[i - 5:i]['bullish_fvg'].any()) and
                    df.iloc[i - 3:i]['buy_liquidity'].any() and
                    (df.iloc[i]['lower_wick'] > 1.5 * df.iloc[i]['body_size']) and
                    df.iloc[i]['bullish']
            )

            if bull_cond:
                df.loc[df.index[i], 'buy_setup'] = True

            # Bearish setup criteria
            bear_cond = (
                    (df.iloc[i - 5:i]['bearish_ob'].any() |
                     df.iloc[i - 5:i]['bearish_fvg'].any()) and
                    df.iloc[i - 3:i]['sell_liquidity'].any() and
                    (df.iloc[i]['upper_wick'] > 1.5 * df.iloc[i]['body_size']) and
                    not df.iloc[i]['bullish']
            )

            if bear_cond:
                df.loc[df.index[i], 'sell_setup'] = True

        return df