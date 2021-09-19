from datetime import date, timedelta
import yfinance as yf
from stock import Stock
from market import Market
import sys
import pytz


class AccountSimulator:
    # algorithm will decide what to buy and to sell and when
    def __init__(self, start_funds):
        self.__start_money = start_funds
        self.__money = start_funds
        self.__stocks = {}    # ticker -> Stock(ticker)
        self.__history = {}   # ticker -> [(date, 'buy'/'sell', quantity, price)]
        self.__date = None    # will be set during run
        self.__market = None  # will be set according to the date


    def get_free_money(self):
        return self.__money
    def get_active_money(self):  # how much all stocks cost now in total
        res = [self.get_stock_total_cost(ticker) for ticker in self.__stocks.keys()]
        return sum(res)
    def get_stock_total_cost(self, ticker):
        stock = self.__stocks[ticker]
        n = stock.get_quantity()
        price = self.__market.get_current_price(ticker)
        date = self.__date
        while price == None:
            date = date - timedelta(1)
            price = self.__market.get_price(ticker, date)
        return n * price
    def get_portfolio_cost(self):
        return self.get_free_money() + self.get_active_money()
    def get_owned_stocks(self):
        return self.__stocks
    def get_owned_stock(self, ticker):
        return self.__stocks[ticker]
    def get_operations_history(self):
        return self.__history
    def get_ticker_operation_history(self, ticker):
        return self.__history[ticker]
    def get_date(self):
        return self.__date
    def get_market(self):
        return self.__market
    def get_quantity(self, ticker):
        if not ticker in self.__stocks.keys():
            return 0
        else:
            return self.__stocks[ticker].get_quantity()

    def set_algorithm(self, new_algorithm):
        self.__algorithm = new_algorithm

    def print_operations_history(self):
        keys = self.__history.keys()
        if len(keys) == 0:
            print("no history")
        else:
            for ticker in keys:
                self.print_ticker_operation_history(ticker)
    def print_ticker_operation_history(self, ticker):
        ticker_history = self.__history[ticker]
        print(ticker + ":")
        for event in ticker_history:
            print(f"{event[0]}: {event[1]} {event[2]} stock(s) for {event[3]:.2f} each")
    def print_stocks(self):
        keys = self.__stocks.keys()
        if len(keys) == 0:
            print("no stocks")
        else:
            for ticker in keys:
                n = self.__stocks[ticker].get_quantity()
                if n != 0:
                    print(f"{ticker}: {n}")


    def __add_to_history(self, ticker, event, n, price):
        new_data = (self.__date, event, n, price)
        if not ticker in self.__history:
            self.__history[ticker] = [new_data]
        else:
            self.__history[ticker].append(new_data)


    def buy(self, ticker, n):
        if n <= 0:
            return

        price = self.__market.get_current_price(ticker)

        if price == None or price == -1:
            print(f"No data available for {ticker} for {self.__date}", file = self.__file)
            print("Buy operation cannot be completed", file = self.__file) # or exception?
            return

        if self.__money < price * n:
            print(f"Not enough money to buy {n} x {ticker} for {price:.2f}", file = self.__file)
            print("Buy operation cannot be completed", file = self.__file) # or exception?
            return

        self.__money -= price * n
        self.__add_to_history(ticker, 'buy', n, price)
        if ticker in self.__stocks.keys():
            self.__stocks[ticker].buy(price, n)
        else:
            stock = Stock(ticker)
            stock.buy(price, n)
            self.__stocks[ticker] = stock


    def sell(self, ticker, n):
        if n <= 0:
            return

        if not ticker in self.__stocks.keys():
            print(f"There are no stocks with ticker {ticker}", file = self.__file)
            print("Sell operation cannot be completed", file = self.__file) # or exception?
            return

        if self.__stocks[ticker].get_quantity() < n:
            print(f"There are not enough {ticker} stocks", file = self.__file)
            print("Sell operation cannot be completed", file = self.__file) # or exception?
            return

        price = self.__market.get_current_price(ticker)
        if price == None or price == -1:
            print(f"No data available for {ticker} for {self.__date}", file = self.__file)
            print("Sell operation cannot be completed", file = self.__file) # or exception?
            return

        self.__money += price * n
        self.__add_to_history(ticker, 'sell', n, price)
        self.__stocks[ticker].sell(n)

    # working hours 9:30 - 15:59
    def is_working_hour(self, date):
        return not (self.__date.hour >= 16 or self.__date.hour < 9 or (self.__date.hour == 9 and self.__date.minute < 30))


    def is_working_date(self, date):
        if date.weekday > 4:
            return False
        if not self.is_working_hour(date):
            return False
        return True


    def __upd_date(self):
        weekday = self.__date.weekday() # 0 - Mon ... 6 - Sun
        # weekends or the end of the friday
        if weekday > 4 or (self.__date.hour == 15 and self.__date.minute == 30 and weekday == 4):
            self.__date = self.__date + timedelta(days=7-weekday)
            self.__date = self.__date.replace(hour = 9, minute = 30)
        # the end of the day
        elif (self.__date.hour == 15 and self.__date.minute == 30) or self.__date.hour >= 16:
            self.__date = self.__date + timedelta(days=1)
            self.__date = self.__date.replace(hour = 9, minute = 30)
        elif self.__date.hour < 9 or  (self.__date.hour == 9 and self.__date.minute < 30):
            self.__date = self.__date.replace(hour = 9, minute = 30)
        else:
            self.__date = self.__date + timedelta(hours=1)

    def algorithm(self):
        print(f"     {self.__date}: hour is over")
        print(f"portfolio costs {self.get_portfolio_cost():.2f} = {self.get_free_money():.2f} free money left + {self.get_active_money():.2f} stocks cost in total")
        print("  portfolio:")
        self.print_stocks()
        print("  history:")
        self.print_operations_history()
        print()

    # run hours from start_date up to end_date exclusively
    def run(self, start_date, end_date, file_name = ""):
        if file_name != "":
            self.__file = open(file_name, 'w')
        else:
            self.__file = sys.stdout

        self.__date = start_date
        self.__date = pytz.timezone("America/New_York").localize(self.__date)
        end_date = pytz.timezone("America/New_York").localize(end_date)
        while self.__date < end_date:
            self.__upd_date()
            self.__market = Market(self.__date)
            self.algorithm()

        self.__file.close()
