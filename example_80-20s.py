from simulator import AccountSimulator
from datetime import date, timedelta, datetime
from market import Market, EmptyDataError
from pandas.tseries.offsets import BDay
import sys

class MyAccountSimulator(AccountSimulator):
    def __init__(self, start_money, tickers):
        super(MyAccountSimulator, self).__init__(start_money)
        self.ticker = tickers
        self.tickers_to_sell = {}  # ticker -> price
        self.tickers_to_buy = {}   # ticker -> price
        self.data_available = True # May be False for holidays (2.04.21, for example)

    def __get_suitable_tickers(self, date, market):
        yesterday = date - BDay(1)

        self.tickers_to_sell = {}
        self.tickers_to_buy = {}
        self.data_available = True

        for ticker in self.ticker:
            try:
                yesterday_high = market.get_high_day_price(ticker, yesterday)
                yesterday_low = market.get_low_day_price(ticker, yesterday)
                yesterday_open = market.get_open_day_price(ticker, yesterday)
                yesterday_close = market.get_close_day_price(ticker, yesterday)
                range = yesterday_high - yesterday_low

                if (yesterday_open <= 0.2 * range + yesterday_low) and (yesterday_close >= 0.8 * range + yesterday_low): # sell today
                    if self.get_quantity(ticker) > 0:
                        self.tickers_to_sell[ticker] = yesterday_close
                elif (yesterday_close <= 0.2 * range + yesterday_low) and (yesterday_open >= 0.8 * range + yesterday_low): # buy today
                    self.tickers_to_buy[ticker] = yesterday_close
            except EmptyDataError:
                self.data_available = False

    def check_and_buy(self, market):
        tickers_to_del = []
        for ticker in self.tickers_to_buy.keys():
            if market.get_current_price(ticker) <= self.tickers_to_buy[ticker]:
                self.buy(ticker, 1)
                tickers_to_del.append(ticker)
        for ticker in tickers_to_del:
            del self.tickers_to_buy[ticker]

    def check_and_sell(self, market):
        tickers_to_del = []
        for ticker in self.tickers_to_sell.keys():
            if market.get_current_price(ticker) >= self.tickers_to_sell[ticker]:
                n = self.get_quantity(ticker)
                self.sell(ticker, n)
                tickers_to_del.append(ticker)
        for ticker in tickers_to_del:
            del self.tickers_to_sell[ticker]

    def print_day_results(self, date):
        print()
        print(f"      {date.strftime('%Y-%m-%d')}: day is over")
        print(f"portfolio costs {self.get_portfolio_cost():.2f} = {self.get_free_money():.2f} free money left + {self.get_active_money():.2f} stocks cost in total")
        print("  portfolio:")
        self.print_stocks()
        print("  history:")
        self.print_operations_history()
        print()
        sys.stdout.flush()

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

        if not self.data_available:
            return

        self.check_and_buy(market)
        self.check_and_sell(market)

        if date.hour == 15 and date.minute == 30:
            self.print_day_results(date)


start_date = datetime(year=2021, month=3, day=4)
end_date = datetime(year=2021, month=6, day=5)
file_name = "run_" + start_date.strftime('%Y-%m-%d_%H-%M-%S') + "_" + end_date.strftime('%Y-%m-%d_%H-%M-%S') + "_" + str(datetime.now().strftime('%Y-%m-%d_%H-%M-%S')) + ".txt"

tickers = ['IDCC', 'SAP', 'SBUX', 'SGEN']
ms = MyAccountSimulator(1000, tickers)
ms.run(start_date, end_date, file_name)
