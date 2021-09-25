# Stock-market-simulator

#### stock.py
File with Stock class. It stores ticker and quantity

#### market.py
Stock market in a particular day. It can download stock data and get price of a stock at a particular time

#### simulator.py
The main function there is `run`. It goes over a given period with an hourly interval and calls an `algorithm` function that should buy and sell stocks according to the method  that is supposed to be tested. `buy` and `sell` methods can also be found in this class. 

#### example_80-20s.py
The example of the classes usage is given there. The algorithm there is 80-20s. If ('Open' of the day is in the lowest 20% of the range of this day) and ('Close' of the day is in the highest 80% of the range of this day) then on the next day this stock should be sold as there will be reverse. Vice verse for a purchase

How to run: `python3 example_80-20s.py`
