import numpy as np
from statsmodels.nonparametric.kernel_regression import KernelReg
import pandas_ta as ta
import pandas as pd
from utils.algorithms.base import TradingAlgorithm


class AligatorAlgorithm(TradingAlgorithm):
    def __init__(self):
        self.mysize = 0.1
        self.TPSLRatio = 1.5
        self.perc = 0.02

        self.n_backcandles = 10


    def _handle_df_needs(self, df):
        key = list(df.keys())[0]

        df = pd.DataFrame(df[key])
        df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close'},
                            inplace=True)
        df["time"] = pd.to_datetime(df["time"], unit='s')
        df = df[df.High != df.Low]
        df.set_index("time", inplace=True, drop=True)

        df["SMA_1"] = ta.sma(df.Close, length=5).shift(3)  # 3
        df["SMA_2"] = ta.sma(df.Close, length=8).shift(5)  # 5
        df["SMA_3"] = ta.sma(df.Close, length=13).shift(8)  # 8
        df["SMA_Diff"] = df["SMA_1"] - df["SMA_3"]

        df["EMA"] = ta.ema(df.Close, length=200)
        return df

    def get_signal(self, df):
        df_copy = df.copy()
        df_copy = self._handle_df_needs(df_copy)
        df_copy = self.assign_sma_signals(df_copy)
        df_copy['TotalSignal'] = df_copy.apply(lambda row: self.__total_signal(row) if row.name >= 7 else 0,
                                                         axis=1)
        df_copy['pointpos'] = df_copy.apply(lambda row: self.__pointpos(row), axis=1)
        df_copy.set_index("time", inplace=True, drop=True)

        final_signal = df_copy['TotalSignal']

        try:
            signal = final_signal.iloc[0]
            return signal
        except Exception as e:
            # raise e
            print(f"Error generating signal: {str(e)}")
            return 0

    def _check_sma_conditions(self, row, df):

        # Extract relevant slices of SMA columns for comparison
        sma_1_slice = df['SMA_1'].iloc[row.name - self.n_backcandles:row.name]
        sma_2_slice = df['SMA_2'].iloc[row.name - self.n_backcandles:row.name]
        sma_3_slice = df['SMA_3'].iloc[row.name - self.n_backcandles:row.name]
        sma_diff_slice = df['SMA_Diff'].iloc[row.name - self.n_backcandles:row.name]

        # Extract relevant slices of High, Low, and EMA columns for comparison
        high_slice = df['High'].iloc[row.name - self.n_backcandles:row.name]
        low_slice = df['Low'].iloc[row.name - self.n_backcandles:row.name]
        ema_slice = df['EMA'].iloc[row.name - self.n_backcandles:row.name]

        condition_1 = all(sma_1 < sma_2 < sma_3 for sma_1, sma_2, sma_3 in zip(sma_1_slice, sma_2_slice, sma_3_slice))
        condition_2 = all(sma_1 > sma_2 > sma_3 for sma_1, sma_2, sma_3 in zip(sma_1_slice, sma_2_slice, sma_3_slice))

        condition_1_confirmed = all(high < ema for high, ema in zip(high_slice, ema_slice))
        condition_2_confirmed = all(low > ema for low, ema in zip(low_slice, ema_slice))

        condition_3_average_sma_diff = abs(sma_diff_slice).mean() > 1e-6

        # Return the signal based on the conditions
        if condition_1 and condition_3_average_sma_diff and condition_2_confirmed:  # inverted conditions because alligator signal should happen ABOVE the EMA
            return 1
        if condition_2 and condition_3_average_sma_diff and condition_1_confirmed:  # inverted conditions because alligator signal should happen BELOW the EMA
            return 2

        return 0

    # ----------------------------------------------------------------------------------------------------------------------------------
    def assign_sma_signals(self, df):
        # Ensure index is properly ordered and numeric for slicing
        df = df.reset_index(drop=False)

        # Initialize the SMA_Signal column with an apply function
        # Apply starts from the n_backcandles-th row to have enough data for comparison
        df['SMA_Signal'] = 0
        df.loc[self.n_backcandles:, 'SMA_Signal'] = df.iloc[self.n_backcandles:].apply(lambda row: self._check_sma_conditions(row, df), axis=1)
        return df

    def __total_signal(self, row):
        # Directly use the SMA_Signal value for the current row
        sma_signal_result = row['SMA_Signal']

        # Calculate the candle's body and wick sizes
        # body_size = abs(row['Close'] - row['Open'])
        # upper_wick = max(row['High'] - row['Close'], row['High'] - row['Open'])

        # Check the conditions for generating the total signal
        if sma_signal_result == 2:
            if (row['Close'] < row['SMA_2']):  # and upper_wick < (body_size / 10)):
                return 1
        elif sma_signal_result == 1:
            if (row['Close'] > row['SMA_2']):  # and upper_wick < (body_size / 10)):
                return 2

        return 0

    def __pointpos(self, x):
        if x['TotalSignal'] == 2:
            return x['Low'] - 1e-3
        elif x['TotalSignal'] == 1:
            return x['High'] + 1e-3
        else:
            return np.nan


class MHarrisSystematic(TradingAlgorithm):
    def __init__(self):
        pass

    def _handle_df_needs(self, df_copy):
        key = list(df_copy.keys())[0]

        df = pd.DataFrame(df_copy[key])
        df_copy.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close'},
                            inplace=True)
        df_copy["time"] = pd.to_datetime(df_copy["time"], unit='s')
        df_copy = df_copy[df_copy.High != df_copy.Low]
        df_copy.set_index("time", inplace=True, drop=True)

        return df_copy
    def get_signal(self, df):
        df_copy = df.copy()
        df_copy = self._handle_df_needs(df_copy)
        df_copy = self._add_total_signal(df_copy)
        df_copy = self._add_pointpos_column(df_copy, "TotalSignal")
        signal = df_copy['TotalSignal'].iloc[0]
        return signal


    def _total_signal(self, df, current_candle):
        current_pos = df.index.get_loc(current_candle)

        c1 = df['Low'].iloc[current_pos - 4] > df['High'].iloc[current_pos]
        c2 = df['High'].iloc[current_pos] > df['Low'].iloc[current_pos - 3]
        c3 = df['Low'].iloc[current_pos - 3] > df['Low'].iloc[current_pos - 2]
        c4 = df['Low'].iloc[current_pos - 2] > df['Low'].iloc[current_pos - 1]
        c5 = df['Close'].iloc[current_pos] > df['High'].iloc[current_pos - 1]

        if c1 and c2 and c3 and c4 and c5:
            return 2

        c1 = df['High'].iloc[current_pos - 4] < df['Low'].iloc[current_pos]
        c2 = df['Low'].iloc[current_pos] < df['High'].iloc[current_pos - 3]
        c3 = df['High'].iloc[current_pos - 3] < df['High'].iloc[current_pos - 2]
        c4 = df['High'].iloc[current_pos - 2] < df['High'].iloc[current_pos - 1]
        c5 = df['Close'].iloc[current_pos] < df['Low'].iloc[current_pos - 1]

        if c1 and c2 and c3 and c4 and c5:
            return 1

        return 0

    def _add_total_signal(self, df):
        df['TotalSignal'] = df.apply(lambda row: self._total_signal(df, row.name), axis=1)
        return df

    def _add_pointpos_column(self, df, signal_column):
        """
        Adds a 'pointpos' column to the DataFrame to indicate the position of support and resistance points.

        Parameters:
        df (DataFrame): DataFrame containing the stock data with the specified SR column, 'Low', and 'High' columns.
        sr_column (str): The name of the column to consider for the SR (support/resistance) points.

        Returns:
        DataFrame: The original DataFrame with an additional 'pointpos' column.
        """

        df['pointpos'] = df.apply(lambda row: self.__pointpos(row, signal_column), axis=1)
        return df

    def __pointpos(self, row, signal_column):
        if row[signal_column] == 2:
            return row['Low'] - 1e-4
        elif row[signal_column] == 1:
            return row['High'] + 1e-4
        else:
            return np.nan

class NadayaraWatsonFullStrategy15Min(TradingAlgorithm):
    def __init__(self):
        # Initialization
        self.backcandles = 10
        self.bw = 7

    def _handle_df_needs(self, df_copy):
        key = list(df_copy.keys())[0]

        df = pd.DataFrame(df_copy[key])
        df_copy.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close'},
                            inplace=True)
        df_copy["time"] = pd.to_datetime(df_copy["time"], unit='s')
        df_copy = df_copy[df_copy.High != df_copy.Low]
        df_copy.set_index("time", inplace=True, drop=True)

        df_copy["EMA_slow"] = ta.ema(df_copy.Close, length=50)
        df_copy["EMA_fast"] = ta.ema(df_copy.Close, length=40)
        df_copy['ATR'] = ta.atr(df_copy.High, df_copy.Low, df_copy.Close, length=7)
        df_copy.reset_index(inplace=True, drop=True)
        df_copy['Middle_Envelope'] = np.nan
        df_copy['Upper_Envelope'] = np.nan
        df_copy['Lower_Envelope'] = np.nan

        return df_copy

    def get_signal(self, df):
        df_copy = df.copy()
        df_copy = self._handle_df_needs(df_copy)
        df_copy = self._set_envelopes(df_copy)
        my_bbands = ta.bbands(df_copy.Close, length=10, std=2)
        df_copy = df_copy.join(my_bbands)
        df_copy = self._ema_signal(df_copy, 7)
        df_copy = self._total_signal_BB(df_copy)
        df_copy["TotalSignal"] = df_copy.Total_Signal
        df_copy['pointpos'] = df_copy.apply(lambda row: self.__pointpos(row, "TotalSignal"), axis=1)

        signal = df_copy['TotalSignal'].iloc[0]
        return signal

    def _set_envelopes(self, df_copy):
        for current_candle_index in range(self.backcandles, len(df_copy)):
            middle, upper, lower = self.__compute_envelopes(df_copy, current_candle_index, self.backcandles, self.bw)
            df_copy.at[current_candle_index, 'Middle_Envelope'] = middle
            df_copy.at[current_candle_index, 'Upper_Envelope'] = upper
            df_copy.at[current_candle_index, 'Lower_Envelope'] = lower
        return df_copy

    def __compute_envelopes(self, df, current_candle_index, backcandles, bw=3):
        # Slice the DataFrame to include only the past candles up to the current candle index
        start_index = max(current_candle_index - backcandles, 0)
        dfsample = df[start_index:current_candle_index + 1].copy()  # current candle included

        # Ensure the index is continuous for the kernel regression
        dfsample.reset_index(drop=True, inplace=True)

        # Create the Kernel Regression model
        X = dfsample.index
        model = KernelReg(endog=dfsample['Close'], exog=X, var_type='c', reg_type='lc', bw=[bw])
        fitted_values, _ = model.fit()

        # Calculate residuals and standard deviation of residuals
        residuals = dfsample['Close'] - fitted_values
        std_dev = 2. * np.std(residuals)
        # std_dev = dfsample['Close'].rolling(window=backcandles-1).std().iloc[-1]

        # Calculate the envelopes
        middle = fitted_values[-1]
        upper = middle + std_dev
        lower = middle - std_dev

        return middle, upper, lower

    def _ema_signal(self, df, backcandles):
        # Create boolean Series for conditions
        above = df['EMA_fast'] > df['EMA_slow']
        below = df['EMA_fast'] < df['EMA_slow']

        # Rolling window to check if condition is met consistently over the window
        above_all = above.rolling(window=backcandles).apply(lambda x: x.all(), raw=True).fillna(0).astype(bool)
        below_all = below.rolling(window=backcandles).apply(lambda x: x.all(), raw=True).fillna(0).astype(bool)

        # Assign signals based on conditions
        df['EMASignal'] = 0  # Default no signal
        df.loc[above_all, 'EMASignal'] = 2  # Signal 2 where EMA_fast consistently above EMA_slow
        df.loc[below_all, 'EMASignal'] = 1  # Signal 1 where EMA_fast consistently below EMA_slow
        return df

    def _total_signal_BB(self, df):
        # Vectorized conditions for total_signal
        condition_sell = (df['EMASignal'] == 2) & (df['Close'] <= df['BBL_10_2.0'])
        condition_buy = (df['EMASignal'] == 1) & (df['Close'] >= df['BBU_10_2.0'])

        # Assigning signals based on conditions
        df['Total_Signal'] = 0  # Default no signal
        df.loc[condition_sell, 'Total_Signal'] = 1
        df.loc[condition_buy, 'Total_Signal'] = 2
        return df

    def __pointpos(self, row, signal_column):
        if row[signal_column] == 2:
            return row['Low'] - 1e-4
        elif row[signal_column] == 1:
            return row['High'] + 1e-4
        else:
            return np.nan
    