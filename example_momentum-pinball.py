from simulator import AccountSimulator
from datetime import date, timedelta, datetime
from market import Market
from pandas.tseries.offsets import BDay
import ta
import matplotlib.pyplot as plt


class AlgorithmMomentumPinball(AccountSimulator):
    def __init__(self, start_money, tickers, file_name):
        super(AlgorithmMomentumPinball, self).__init__(start_money)
        self.__tickers = tickers
        self.__buying_stops = {}  # ticker -> price for buying
        self.__selling_stops = {}  # ticker -> price for selling
        self.__selling_saving_stops = {}  # ticker -> price
        self.__first_hour_min = {}  # ticker -> min price
        self.__file = open(file_name, "w")

    # get stocks that complies with algorithm conditions
    def __get_suitable_tickers(self, date, market):
        for ticker in self.__tickers:
            date_min_7 = date - BDay(7)
            yesterday = date - BDay(1)
            close = market.get_data(ticker, date_min_7, yesterday, "1d")['Close']

            roc_res = ta.momentum.roc(close, 1, True)
            lbr_rsi = ta.momentum.rsi(roc_res, 3, True)

            if len(lbr_rsi) == 0:
                continue

            # if yesterday we had lbr_rsi < 30 => today we set stop for buiying
            # if yesterday we had lbr_rsi > 70 => today we set stop for selling
            if lbr_rsi[-1] < 30:
                first_hour_range = market.get_data(ticker, yesterday, date, "1h")['Close']
                self.__first_hour_min[ticker] = min(first_hour_range)
                self.__buying_stops[ticker] = max(first_hour_range)
            elif lbr_rsi[-1] > 70:
                first_hour_range = market.get_data(ticker, yesterday, date, "1h")['Close']
                self.__selling_stops[ticker] = min(first_hour_range)


    def check_and_buy(self, date, market):
        tickers_to_del = []
        for ticker in self.__buying_stops:
            price = market.get_price(ticker, date)
            if price > self.__buying_stops[ticker]:
                self.buy(ticker, 1)
                tickers_to_del.append(ticker)
                self.__selling_saving_stops[ticker] = self.__first_hour_min[ticker]
        # remove tickers that have been already bought
        for ticker in tickers_to_del:
            del self.__buying_stops[ticker]


    def check_and_sell(self, date, market):
        tickers_to_del = []
        for ticker in self.__selling_stops:
            price = market.get_price(ticker, date)
            if price < self.__selling_stops[ticker]:
                self.sell(ticker, 1)
                tickers_to_del.append(ticker)
        # remove tickers that have been already sold
        for ticker in tickers_to_del:
            del self.__selling_stops[ticker]

        # saving stop check
        tickers_to_del = []
        for ticker in self.__selling_saving_stops:
            price = market.get_price(ticker, date)
            if price == self.__selling_saving_stops[ticker]:
                self.sell(ticker, 1)
                tickers_to_del.append(ticker)
        for ticker in tickers_to_del:
            del self.__selling_saving_stops[ticker]


    def algorithm(self):
        date = self.get_date()
        market = self.get_market()

        if date.hour < 10:
            return

        # new day:
        # if yesterday lbr_rsi was less than 30 =>
        #  today we set buying stop higher than maximum of the first hour
        if date.hour == 10 and date.minute == 30:
            self.__get_suitable_tickers(date, market)
            return

        self.check_and_buy(date, market)
        self.check_and_sell(date, market)

        if date.hour == 15 and date.minute == 30:
            self.__buying_stops = {}
            self.print_day_results(self.__file)

        end_date = self.get_end_date()
        if date >= end_date:
            self.__file.close()


start_date = datetime(year=2021, month=3, day=1)
end_date = datetime(year=2021, month=6, day=27)
file_name = "run_momentum-pinball" + start_date.strftime('%Y-%m-%d_%H-%M-%S') + "_" + end_date.strftime('%Y-%m-%d_%H-%M-%S') + "_" + str(datetime.now().strftime('%Y-%m-%d_%H-%M-%S')) + ".txt"

tickers = ['IDCC', 'SAP', 'SBUX', 'SGEN']
ms = AlgorithmMomentumPinball(1000, tickers, file_name)
ms.run(start_date, end_date)
ms.history_plot()
