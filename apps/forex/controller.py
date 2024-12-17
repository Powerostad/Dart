import pandas as pd
from mt5linux import MetaTrader5
from django.conf import settings

class MT5Controller:
    def __init__(self):
        host = settings.METATRADER_URL
        port = settings.METATRADER_PORT
        self.mt5 = MetaTrader5(host, port)

        self._initialize()

    def _initialize(self):
        try:
            if not self.mt5.initialize():
                raise ConnectionError("Failed To Initialize MetaTrader5!")
        except Exception as e:
            print("Unexpected Error on initializing MetaTrader5: ", str(e))
            raise

    def get_account_info(self):
        try:
            account_info = self.mt5.account_info()
            if not account_info:
                raise ConnectionError("Failed To Get Account Info!")
            return account_info._asdict()
        except Exception as e:
            print("Unexpected Error on getting MetaTrader5 account info: ", str(e))
            raise

    def get_historical_data_candles(self, symbol, timeframe, start_date, end_date):
        try:
            rates = self.mt5.copy_rates_from_pos(
                symbol,
                timeframe,
                0,
                100
            )

            if rates is None:
                raise Exception("Failed to retrieve historical data for {}".format(symbol))

            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            return df
        except Exception as e:
            print("Unexpected Error on getting historical data candles: ", str(e))
            raise