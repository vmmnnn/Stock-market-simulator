from datetime import date, datetime, timedelta
import pandas as pd
import yfinance as yf
from functools import lru_cache

# download all data available
# valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
@lru_cache(maxsize=500)
def get_data(ticker, interval):
    if interval in ["1d", "5d", "1wk", "1mo", "3mo"]:
        return yf.download(ticker, interval=interval, period="max")

    if interval == "1m":
        delta = timedelta(days=7)
    elif interval in ["2m", "5m", "15m", "30m", "90m"]:
        delta = timedelta(days=59)
    else:          # interval in ["60m", "1h"]
        delta = timedelta(days=729)

    start_period = datetime.now() - delta
    return yf.download(ticker, interval=interval, start=start_period)



# market for a particular date
class Market:
    def __init__(self, date):
        self.__date = date


    # difference between date and current (real) time
    # as yfinance may refuse to download old data with small intervals
    def __get_cur_time_diff(self, date):
        tzinfo = date.tzinfo
        cur_time = datetime.now(tzinfo)
        return cur_time - date


    # check if yfinance is able to download the data
    def __check_interval_requirements(self, interval, date):
        delta = self.__get_cur_time_diff(date)
        if interval == "1m":
            return delta.days < 30
        if interval in ["2m", "5m", "15m", "30m", "90m"]:
            return delta.days < 60
        if interval in ["60m", "1h"]:
            return delta.days < 730
        return True


    # what min interval is available for the date given
    def __get_min_interval(self, date):
        delta = self.__get_cur_time_diff(date)
        if delta.days < 30:
            return "1m"
        if delta.days < 60:
            return "2m"
        if delta.days < 730:
            return "1h"
        return "1d"


    # get data for the period
    def get_data(self, ticker, start_date, end_date, interval):
        if end_date > self.__date or start_date > end_date:
            return pd.DataFrame()   # or exception?
        if not self.__check_interval_requirements(interval, start_date):
            return pd.DataFrame()
        data = get_data(ticker, interval)

        return data.loc[start_date : end_date]


    def get_stock_data(self, ticker):
        return yf.Ticker(ticker)


    def get_high_day_price(self, ticker, date):
        data = self.get_data(ticker, date, date+timedelta(days=1), "1d")
        if data.empty:
            return -1
        return data['High'].iloc[0]

    def get_low_day_price(self, ticker, date):
        data = self.get_data(ticker, date, date+timedelta(days=1), "1d")
        if data.empty:
            return -1
        return data['Low'].iloc[0]

    def get_open_day_price(self, ticker, date):
        data = self.get_data(ticker, date, date+timedelta(days=1), "1d")
        if data.empty:
            return -1
        return data['Open'].iloc[0]

    def get_close_day_price(self, ticker, date):
        data = self.get_data(ticker, date, date+timedelta(days=1), "1d")
        if data.empty:
            return -1
        return data['Close'].iloc[0]


    # returns the price for the datetime requested
    def get_price(self, ticker, date):
        if date > self.__date:
            return -1

        if date.hour < 9 or (date.hour == 9 and date.minute == 30):  # returns open time of the day
            return self.get_open_day_price(ticker, date)

        delta = self.__get_cur_time_diff(date)
        if date.minute == 30 or delta.days > 60:
            interval = "1h"
        else:
            interval = "30m"

        if not self.__check_interval_requirements(interval, date):
            return -1
             
        data = get_data(ticker, interval)
        if data.empty:
            return -1

        if not pd.Timestamp(date) in data.index:   # holiday, for example on 02.04.21 market finished working earlier
            return data['Open'].iloc[len(data.index) - 1]

        return data['Open'].loc[pd.Timestamp(date)]


    # returns the price of the current market date
    def get_current_price(self, ticker):
        return self.get_price(ticker, self.__date)
