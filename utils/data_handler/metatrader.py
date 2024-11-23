import pandas as pd
from django.conf import settings
import requests


class MetaTraderManager:
    def __init__(self, symbol, timeframe):
        self.symbol = symbol
        self.timeframe = timeframe

        self.base_url = settings.METATRADER_URL
        self.historical_data_url = self.base_url + f"{self.symbol}/"
        self.symbol_info_url = self.base_url + f"info/{self.symbol}/"


    def get_historical_data(self):
        try:
            response = requests.get(self.historical_data_url, params={"timeframe": self.timeframe})
            df = pd.DataFrame.from_dict(response.json())
            return df
        except Exception as e:
            raise e
            print("Error in getting historical data from metatrader")
            return None

    def get_symbol_info(self):
        try:
            response = requests.get(self.symbol_info_url)
            return response.json()
        except Exception as e:
            raise e
