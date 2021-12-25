from simulator import AccountSimulator
from datetime import date, timedelta, datetime
from market import Market
from pandas.tseries.offsets import BDay
import ta


class AlgorithmMomentumPinball(AccountSimulator):
    def __init__(self, start_money, tickers, file_name):
        super(AlgorithmMomentumPinball, self).__init__(start_money)
        self.__tickers = tickers
        self.__tickers_to_sell = {}  # ticker -> price
        self.__tickers_to_buy = {}   # ticker -> price
        self.__buying_stops = {}  # ticker -> price for buying
        self.__selling_saving_stops = {}  # ticker -> price
        self.__first_hour_min = {}  # ticker -> min price
        self.__file = open(file_name, "w")

    # get stocks that complies with algorithm conditions
    def __get_suitable_tickers(self, date, market):
        self.__tickers_to_sell = {}
        self.__tickers_to_buy = {}

        for ticker in self.__tickers:
            yesterday_min_1 = date - BDay(2)
            yesterday = date - BDay(1)
            close = market.get_data(ticker, yesterday_min_1, yesterday, "1d")['Close']

            roc_res = ta.momentum.roc(close, 1, True)
            lbr_rsi = ta.momentum.rsi(roc_res, 3, True)

            if len(lbr_rsi) == 0:
                continue


            # if yesterday we had lbr_rsi < 30 => today we do some buying actions
            if lbr_rsi[0] < 30:
                first_hour_range = market.get_data(ticker, yesterday, date, "1h")['Close']  # ???
                self.__first_hour_min[ticker] = min(first_hour_range)
                self.__buying_stops[ticker] = max(first_hour_range)


    def check_and_buy(self, date, market):
        eps = 0.5
        for tickers in self.__buying_stops:
            if market.get_price(ticker, date) in range(self.__buying_stops[ticker] - eps, self.__buying_stops[ticker] + eps):
                self.buy(ticker, 1)
                del self.__buying_stops[ticker]
                self.__selling_saving_stops[ticker] = self.__first_hour_min[ticker]


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

        if date.hour == 15 and date.minute == 30:
            self.print_day_results(self.__file)

        end_date = self.get_end_date()
        if date >= end_date:
            self.__file.close()


start_date = datetime(year=2021, month=3, day=4)
end_date = datetime(year=2021, month=6, day=5)
file_name = "run_momentum-pinball" + start_date.strftime('%Y-%m-%d_%H-%M-%S') + "_" + end_date.strftime('%Y-%m-%d_%H-%M-%S') + "_" + str(datetime.now().strftime('%Y-%m-%d_%H-%M-%S')) + ".txt"

tickers = ['IDCC']#, 'SAP', 'SBUX', 'SGEN']
ms = AlgorithmMomentumPinball(1000, tickers, file_name)
ms.run(start_date, end_date)
