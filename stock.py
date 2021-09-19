
class Stock:
    def __init__(self, ticker):
        self.__ticker = ticker
        self.__quantity = 0
        self.__prices = []
        self.__average_price = 0

    def get_quantity(self):
        return self.__quantity

    def buy(self, price, n=1):
        self.__quantity += n
        self.__prices = self.__prices + [price for i in range(n)]
        self.__average_price = self.__get_average_price()

    def sell(self, n=1):
        self.__quantity -= n
        self.__prices = self.__prices[n:]  # as Tinkoff does
        self.__average_price = self.__get_average_price()

    def __get_average_price(self):
        if len(self.__prices) == 0:
            return 0
        return sum(self.__prices) / len(self.__prices)
