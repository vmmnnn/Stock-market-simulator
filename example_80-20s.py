from simulator import AccountSimulator
from datetime import date, timedelta, datetime
from market import Market
from pandas.tseries.offsets import BDay


class Algorithm8020(AccountSimulator):
    def __init__(self, start_money, tickers, file_name):
        super(MyAccountSimulator, self).__init__(start_money)
        self.__tickers = tickers
        self.__tickers_to_sell = {}  # ticker -> price
        self.__tickers_to_buy = {}   # ticker -> price
        self.__file = open(file_name, "w")

    # get stocks that complies with algorithm conditions
    def __get_suitable_tickers(self, date, market):
        yesterday = date - BDay(1)

        self.__tickers_to_sell = {}
        self.__tickers_to_buy = {}

        for ticker in self.__tickers:
                yesterday_high = market.get_high_day_price(ticker, yesterday)
                yesterday_low = market.get_low_day_price(ticker, yesterday)
                yesterday_open = market.get_open_day_price(ticker, yesterday)
                yesterday_close = market.get_close_day_price(ticker, yesterday)
                range = yesterday_high - yesterday_low

                if (yesterday_open <= 0.2 * range + yesterday_low) and (yesterday_close >= 0.8 * range + yesterday_low): # sell today
                    if self.get_quantity(ticker) > 0:
                        self.__tickers_to_sell[ticker] = yesterday_close
                elif (yesterday_close <= 0.2 * range + yesterday_low) and (yesterday_open >= 0.8 * range + yesterday_low): # buy today
                    self.__tickers_to_buy[ticker] = yesterday_close

    def check_and_buy(self, market):
        tickers_to_del = []
        for ticker in self.__tickers_to_buy.keys():
            # buy as soon as we reach yesterday's price
            if market.get_current_price(ticker) <= self.__tickers_to_buy[ticker]:
                self.buy(ticker, 1)
                tickers_to_del.append(ticker)
        # remove tickers that have been already bought
        for ticker in tickers_to_del:
            del self.__tickers_to_buy[ticker]

    def check_and_sell(self, market):
        tickers_to_del = []
        for ticker in self.__tickers_to_sell.keys():
            # sell as soon as we reach yesterday's price
            if market.get_current_price(ticker) >= self.__tickers_to_sell[ticker]:
                n = self.get_quantity(ticker)
                self.sell(ticker, n)
                tickers_to_del.append(ticker)
        # remove tickers that have been already sold
        for ticker in tickers_to_del:
            del self.__tickers_to_sell[ticker]

    # 80-20's algorithm:
    # If ('Open' of the day is in the lowest 20% of the range of this day) and
    #    ('Close' of the day is in the highest 80% of the range of this day) then
    #    on the next day this stock should be sold as there will be reverse
    # Vice verse for a purchase
    def algorithm(self):
        date = self.get_date()
        market = self.get_market()

        # new day => define tickers that fit the 80-20 condition
        if date.hour == 9 and date.minute == 30:
            self.__get_suitable_tickers(date, market)
            return

        self.check_and_buy(market)
        self.check_and_sell(market)

        if date.hour == 15 and date.minute == 30:
            self.print_day_results(self.__file)

        end_date = self.get_end_date()
        if date >= end_date:
            self.__file.close()


start_date = datetime(year=2021, month=3, day=4)
end_date = datetime(year=2021, month=6, day=5)
file_name = "run_80_20" + start_date.strftime('%Y-%m-%d_%H-%M-%S') + "_" + end_date.strftime('%Y-%m-%d_%H-%M-%S') + "_" + str(datetime.now().strftime('%Y-%m-%d_%H-%M-%S')) + ".txt"

tickers = ['IDCC', 'SAP', 'SBUX', 'SGEN']
ms = Algorithm8020(1000, tickers, file_name)
ms.run(start_date, end_date)
