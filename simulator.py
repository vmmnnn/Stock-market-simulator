from datetime import date, timedelta
import yfinance as yf
from stock import Stock
from market import Market, EmptyDataError
from pandas.tseries.offsets import BDay
import sys
import pytz
import matplotlib.pyplot as plt


class SimulatorError(Exception):
    pass

class InvalidInterval(SimulatorError):
    pass


class AccountSimulator:
    # algorithm will decide what to buy and to sell and when
    def __init__(self, start_funds, comission = 0):
        if comission < 0 or comission > 1:
            raise ValueError("comission must be in range [0.0, 1.0]")
        self.__start_money = start_funds
        self.__money = start_funds
        self.__comission_percent = comission
        self.__stocks = {}    # ticker -> Stock(ticker)
        self.__history = {}   # ticker -> [(date, 'buy'/'sell', quantity, price, comission)]
        self.__date = None    # will be set during run
        self.__start_date = None
        self.__end_date = None
        self.__market = None  # will be set according to the date
        self.__total_comission_loss = 0


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
        total_price = n * price
        comission = total_price * self.__comission_percent
        return total_price - comission
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
    def get_start_date(self):
        return self.__start_date
    def get_end_date(self):
        return self.__end_date
    def get_market(self):
        return self.__market
    def get_total_comission_loss(self):
        return self.__total_comission_loss
    def get_quantity(self, ticker):
        if not ticker in self.__stocks.keys():
            return 0
        else:
            return self.__stocks[ticker].get_quantity()

    def set_algorithm(self, new_algorithm):
        self.__algorithm = new_algorithm

    def print_operations_history(self, file):
        keys = self.__history.keys()
        if len(keys) == 0:
            file.write("no history\n")
        else:
            for ticker in keys:
                self.print_ticker_operation_history(ticker, file)
    def print_ticker_operation_history(self, ticker, file):
        ticker_history = self.__history[ticker]
        file.write(ticker + ":\n")
        for event in ticker_history:
            file.write(f"{event[0]}: {event[1]} {event[2]} stock(s) for {event[3]:.3f} each with {event[4]:.3f} comission\n")
    def print_stocks(self, file):
        keys = self.__stocks.keys()
        if len(keys) == 0:
            file.write("no stocks\n")
        else:
            for ticker in keys:
                n = self.__stocks[ticker].get_quantity()
                if n != 0:
                    file.write(f"{ticker}: {n}\n")

    def stock_plot(self, ticker, start_date, end_date, interval = "1d"):
        market = Market(end_date)
        data = market.get_data(ticker, start_date, end_date, interval)['Close']
        plt.plot(data)
        plt.title(ticker + ": " + str(start_date) + " - " + str(end_date) + "; interval " + interval)
        plt.show()

    def ticker_history_plot(self, ticker, show = False):
        if len(self.__history) == 0 or self.__start_date is None or self.__end_date is None:
            print(f"WARNING: no history available", file=sys.stderr)
            return
        history_data = self.__history[ticker]
        market = Market(self.__end_date)
        data = market.get_data(ticker, self.__start_date, self.__end_date, "1h")['Close']
        plt.clf()
        plt.plot(data)

        buy_dates, buy_prices = self.__get_stock_buy_history(ticker)
        plt.scatter(buy_dates, buy_prices, color='green')

        sell_dates, sell_prices = self.__get_stock_sell_history(ticker)
        plt.scatter(sell_dates, sell_prices, color='red')

        title = f"{ticker} history: {self.__start_date} - {self.__end_date}"
        plt.title(title)

        png_name = f"{ticker}_{self.__start_date.strftime('%Y-%m-%d_%H-%M-%S')}_{self.__end_date.strftime('%Y-%m-%d_%H-%M-%S')}"
        plt.savefig(png_name + ".png")

        if show:
            plt.show()

    def history_plot(self, show = False):
        for ticker in self.__history:
            self.ticker_history_plot(ticker, show)

    def __get_stock_buy_history(self, ticker):
        data = self.__history[ticker]
        dates = []
        prices = []
        for tup in data:
            # tup: (date, 'buy'/'sell', quantity, price)
            if tup[1] == 'buy':
                dates.append(tup[0])
                prices.append(tup[3])
        return (dates, prices)

    def __get_stock_sell_history(self, ticker):
        data = self.__history[ticker]
        dates = []
        prices = []
        for tup in data:
            # tup: (date, 'buy'/'sell', quantity, price)
            if tup[1] == 'sell':
                dates.append(tup[0])
                prices.append(tup[3])
        return (dates, prices)


    def __add_to_history(self, ticker, event, n, price, comission):
        new_data = (self.__date, event, n, price, comission)
        if not ticker in self.__history:
            self.__history[ticker] = [new_data]
        else:
            self.__history[ticker].append(new_data)


    def buy(self, ticker, n):
        if n <= 0:
            return

        price = self.__market.get_current_price(ticker)
        total_price = price * n
        comission = total_price * self.__comission_percent

        if self.__money < total_price + comission:
            print(f"WARNING: not enough money to buy {n} {ticker} stocks ${price} each with total comission {comission}", file=sys.stderr)
            print(f"No {ticker} stocks bought", file=sys.stderr)
            return

        self.__money -= total_price
        self.__money -= comission
        self.__add_to_history(ticker, 'buy', n, price, comission)
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
            print(f"WARNING: no {ticker} stocks are available for selling", file=sys.stderr)
            print(f"No {ticker} stocks sold", file=sys.stderr)
            return

        n_stocks_available = self.__stocks[ticker].get_quantity()
        if n_stocks_available < n:
            print(f"WARNING: {n_stocks_available} {ticker} stocks out of {n} requested are available for selling", file=sys.stderr)
            print(f"No {ticker} stocks sold", file=sys.stderr)
            return

        price = self.__market.get_current_price(ticker)
        total_price = price * n
        comission = total_price * self.__comission_percent

        self.__money += total_price
        self.__money -= comission
        self.__add_to_history(ticker, 'sell', n, price, comission)
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

    def __skip_day(self):
        self.__date = self.__date + BDay(1)
        self.__date = self.__date.replace(hour = 9, minute = 30)


    def print_day_results(self, file):
        file.write("\n")
        file.write(f"      {self.__date.strftime('%Y-%m-%d')}: day is over\n")
        file.write(f"portfolio costs {self.get_portfolio_cost():.2f} = {self.get_free_money():.2f} free money left + {self.get_active_money():.2f} stocks cost in total\n")
        file.write("  portfolio:\n")
        self.print_stocks(file)
        file.write("  history:\n")
        self.print_operations_history(file)
        file.write("\n")


    def algorithm(self):
        print(f"     {self.__date}: hour is over")
        print(f"portfolio costs {self.get_portfolio_cost():.2f} = {self.get_free_money():.2f} free money left + {self.get_active_money():.2f} stocks cost in total")
        print("  portfolio:")
        self.print_stocks()
        print("  history:")
        self.print_operations_history()
        print()

    # run hours from start_date up to end_date exclusively
    def run(self, start_date, end_date):
        if end_date <= start_date:
            raise InvalidInterval()

        self.__date = start_date
        self.__start_date = start_date
        self.__end_date = end_date
        while self.__date < end_date:
            self.__upd_date()
            self.__market = Market(self.__date)
            try:
                self.algorithm()
            except EmptyDataError:
                self.__skip_day()
