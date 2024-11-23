# import pandas as pd
# from openbb import obb
# from rich.jupyter import display
# from rich import print
#
#
# class HistoricalPrices:
#     def __init__(self, symbol, start_date, end_date, provider, **kwargs) -> None:
#         self.one: pd.DataFrame = (
#             obb.equity.price.historical(
#                 symbol=symbol,
#                 start_date=start_date,
#                 end_date=end_date,
#                 interval="1m",
#                 provider=provider,
#                 **kwargs
#             )
#             .to_df()
#             .convert_dtypes()
#         )
#         self.five: pd.DataFrame = (
#             obb.equity.price.historical(
#                 symbol=symbol,
#                 start_date=start_date,
#                 end_date=end_date,
#                 interval="5m",
#                 provider=provider,
#                 **kwargs
#             )
#             .to_df()
#             .convert_dtypes()
#         )
#         self.fifteen: pd.DataFrame = (
#             obb.equity.price.historical(
#                 symbol=symbol,
#                 start_date=start_date,
#                 end_date=end_date,
#                 interval="15m",
#                 provider=provider,
#                 **kwargs
#             )
#             .to_df()
#             .convert_dtypes()
#         )
#         self.thirty: pd.DataFrame = (
#             obb.equity.price.historical(
#                 symbol=symbol,
#                 start_date=start_date,
#                 end_date=end_date,
#                 interval="30m",
#                 provider=provider,
#                 **kwargs
#             )
#             .to_df()
#             .convert_dtypes()
#         )
#         self.sixty: pd.DataFrame = (
#             obb.equity.price.historical(
#                 symbol=symbol,
#                 start_date=start_date,
#                 end_date=end_date,
#                 interval="60m",
#                 provider=provider,
#                 **kwargs
#             )
#             .to_df()
#             .convert_dtypes()
#         )
#         self.daily: pd.DataFrame = (
#             obb.equity.price.historical(
#                 symbol=symbol,
#                 start_date=start_date,
#                 end_date=end_date,
#                 interval="1d",
#                 provider=provider,
#                 **kwargs
#             )
#             .to_df()
#             .convert_dtypes()
#         )
#         self.weekly: pd.DataFrame = (
#             obb.equity.price.historical(
#                 symbol=symbol,
#                 start_date=start_date,
#                 end_date=end_date,
#                 interval="1W",
#                 provider=provider,
#                 **kwargs
#             )
#             .to_df()
#             .convert_dtypes()
#         )
#         self.monthly: pd.DataFrame = (
#             obb.equity.price.historical(
#                 symbol=symbol,
#                 start_date=start_date,
#                 end_date=end_date,
#                 interval="1M",
#                 provider=provider,
#                 **kwargs
#             )
#             .to_df()
#             .convert_dtypes()
#         )
#
#     def get_all_intervals(self) -> pd.DataFrame:
#         """Combine all interval data into a single DataFrame."""
#         intervals = {
#             '1m': self.one,
#             '5m': self.five,
#             '15m': self.fifteen,
#             '30m': self.thirty,
#             '60m': self.sixty,
#             '1d': self.daily,
#             '1W': self.weekly,
#             '1M': self.monthly,
#         }
#
#         # Add an "Interval" column to each DataFrame and concatenate them
#         df_list = []
#         for interval, df in intervals.items():
#             df = df.copy()  # Make a copy to avoid modifying the original DataFrame
#             df["Interval"] = interval  # Add interval as a new column
#             df_list.append(df)
#
#         # Concatenate all DataFrames
#         all_data = pd.concat(df_list)
#
#         return all_data
#
#
# def load_historical(
#     symbol: str = "", start_date=None, end_date=None, provider=None, **kwargs
# ) -> HistoricalPrices:
#
#     if symbol == "":
#         print("[bold red]Please enter a ticker symbol[/bold red]")
#         return None
#
#     if provider is None:
#         provider = "yfinance"
#     prices = HistoricalPrices(symbol, start_date, end_date, provider, **kwargs)
#
#     return prices
#
#
# if __name__ == "__main__":
#     prices = load_historical("spy")
#
#     # Check if the prices object is valid before displaying
#     if prices:
#         # Get all interval data combined into one DataFrame
#         combined_df = prices.get_all_intervals()
#
#         # Display the combined DataFrame
#         print("\n[bold blue]Combined data for all intervals (first 5 rows):[/bold blue]")
#         print(combined_df.head(5).to_string())
#
#         # You can also display the entire DataFrame or parts of it based on your needs
#         print("\n[bold blue]Combined data (last 5 rows):[/bold blue]")
#         print(combined_df.tail(5).to_string())
