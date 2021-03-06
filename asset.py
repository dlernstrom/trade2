import csv
import os
from decimal import Decimal

from constants import KLINE_PATH, KLINE_HEADERS
from exceptions import KlineFileDoesNotExistError
from kline import get_kline, get_file_for_time, get_last_trans_close_time, kline_row_to_dict, get_first_kline
from orders.order import Order

DESIRED_SELL_PERCENTAGE = 1.1
DESIRED_SELL_RECAPTURE = 0.01


class Asset:
    """The strategy behind an asset is that we will track the peak price locally.
    If the peak price goes higher (such that we are outside of any open order protection ranges),
        then we up our limit buy to 10% below the peak price.
    If the peak price falls (such that our limit buy is executed),
        then we place a new limit buy at 10% lower than that.
    """
    def __init__(self, balance_entry, client):
        self.client = client
        self.name = balance_entry['asset']
        self.free = Decimal(balance_entry['free'])  # our accumulation of this asset
        self.locked = Decimal(balance_entry['locked'])  # locked up in buy/sell limit orders
        self.orders = []
        self.tracked_peak = None  # the highest price that we've seen that is 10% above our open buy order
        self.recent_ticker = None
        self.recent_kline = None

    def __str__(self):
        return self.name

    @property
    def ticker(self):
        return f'{self.name}USD'

    @property
    def protected_range(self):
        """returns the lower->upper bounds where the price can float without any action required from us.  There are
        a couple of scenarios:
        1 - no holdings, that means we are tracking a buy price at 10% below the 24 hour peak
        2 - have holdings, protected by spread.  New limit buy placed at 10% below the lowest holdings.
        """
        if self.locked == Decimal('0'):
            return None

    def update_24_hour_ticker(self, ticker):
        """{'symbol': 'DOGEUSD', 'priceChange': '0.1343', 'priceChangePercent': '24.485', 'weightedAvgPrice': '0.6345',
        'prevClosePrice': '0.5485', 'lastPrice': '0.6828', 'lastQty': '711.00000000', 'bidPrice': '0.6828',
        'bidQty': '19191.00000000', 'askPrice': '0.6836', 'askQty': '189.00000000', 'openPrice': '0.5485',
        'highPrice': '0.7332', 'lowPrice': '0.5167', 'volume': '902720521.00000000', 'quoteVolume': '572782138.3562',
        'openTime': 1620349679763, 'closeTime': 1620436079763, 'firstId': 8247889, 'lastId': 8613703, 'count': 365815
        }
        """
        self.recent_ticker = ticker

    @property
    def count(self):
        return self.recent_ticker['count']

    @property
    def change_percent(self):
        return Decimal(self.recent_ticker['priceChangePercent'])

    @property
    def history_path(self):
        return os.path.join(KLINE_PATH, self.name)

    def update_historical_klines(self):
        """Saves Kline data as CSV in our working directory
        [
            1499040000000,      # Open time
            "0.01634790",       # Open
            "0.80000000",       # High
            "0.01575800",       # Low
            "0.01577100",       # Close
            "148976.11427815",  # Volume
            1499644799999,      # Close time
            "2434.19055334",    # Quote asset volume
            308,                # Number of trades
            "1756.87402397",    # Taker buy base asset volume
            "28.46694368",      # Taker buy quote asset volume
            "17928899.62484339" # Can be ignored
        ]
        For example:
        [1614386700000, '0.0515', '0.0520', '0.0514', '0.0517', '3426026.00000000', 1614387599999, '177002.3079', 221,
         '904724.00000000', '46841.8320', '0']
        """
        os.makedirs(self.history_path, exist_ok=True)
        last_close_time = get_last_trans_close_time(self.history_path)
        print(f'Updating historical klines for {self.ticker}; last_close_time was {last_close_time}')
        open_file = None
        open_file_name = None
        for entry in self.client.get_historical_klines(symbol=self.ticker, interval=self.client.KLINE_INTERVAL_15MINUTE,
                                                       start_str=last_close_time if last_close_time is not None else 0):
            kline_dict = kline_row_to_dict(entry)
            desired_fname = get_file_for_time(kline_dict['open_time'])
            if open_file is not None and open_file_name != desired_fname:
                open_file.close()
                open_file = None
            if open_file is None:
                full_path = os.path.join(self.history_path, desired_fname)
                if os.path.exists(full_path):
                    open_file = open(full_path, 'a')
                    writer = csv.DictWriter(open_file, fieldnames=KLINE_HEADERS)
                else:
                    open_file = open(full_path, 'w')
                    writer = csv.DictWriter(open_file, fieldnames=KLINE_HEADERS)
                    writer.writeheader()
                open_file_name = desired_fname
            writer.writerow(kline_dict)
        if open_file is not None:
            open_file.close()

    def update_from_first_kline(self):
        self.recent_kline = get_first_kline(self.history_path)

    def update_from_exchange(self, as_of_time):
        """Update the values that we store locally, assumes that the kline in question exists"""
        self.update_historical_klines()
        try:
            kline = get_kline(as_of_time, self.history_path)
        except KlineFileDoesNotExistError:
            return False
        """
        if self.recent_kline is None:
            self.recent_kline = kline
            self.tracked_peak = self.current
            return True
        """
        self.recent_kline = kline
        return True

    @property
    def current(self):
        return Decimal(self.recent_kline['close'])

    def get_order_for_range(self):
        # if no open orders, and price is higher than the tracked high, then raise the tracked high
        if self.current > self.tracked_peak:
            self.tracked_peak = self.current
        for order in self.orders:
            if order.top >= self.current >= order.bottom:
                return order
        # if price is lower than our lowest order, then put in a new limit buy

    def check_orders(self):
        """Check open orders to see if any of the limit sell or limit buy orders have been filled"""
        if self.tracked_peak is None:
            self.tracked_peak = self.current
        # iterate through orders, capitalize on any limit sell or limit buy that existed within the range
        for order in self.orders:
            if order.order_type == Order.LIMIT_BUY and Decimal(self.recent_kline['low']) < order.limit_price:
                print('order was filled')
                self.orders.remove(order)
                self.place_limit_sell(order.limit_price * DESIRED_SELL_PERCENTAGE)
            if order.order_type == Order.LIMIT_SELL and Decimal(self.recent_kline['high']) > order.limit_price:
                print('sell order was filled')

    def place_limit_buy(self, desired_price):
        """Place a limit buy"""

    def place_limit_sell(self, desired_price):
        """Place a limit sell, sell all but recaptured amount"""

    def place_new_orders(self):
        """Here's where we look at our tracked price and place limit buy orders (if we have cash to tie up)
        or limit sell orders (if we've taken a position).
        """
        # here are scenarios...
        # if there are no orders at all, then we place a limit buy that is 10% below the tracked peak
        if len(self.orders) == 0:
            self.place_limit_buy(self.tracked_peak * 0.9)
        # if we are within the buy/sell point of an existing order, we just ride it.
        # if we are below any recent orders by more than 10%, we need to place a new order

