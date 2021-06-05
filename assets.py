from operator import attrgetter

from asset import Asset


class Assets:
    def __init__(self, client):
        self.client = client
        info = client.get_account()
        self._assets = {balance_entry['asset']: Asset(balance_entry, client) for balance_entry in info['balances']
                        if balance_entry['asset'] != 'USD'}
        self.update_historical_klines()
        self._current_as_of_time = None

    def process(self, as_of_time):
        """Run the process, putting in orders and such"""
        self._current_as_of_time = as_of_time
        assets = list(self._assets.values())
        # The process activity is 2 part, first we update the exchange information
        for asset in assets:
            if asset.update_from_exchange(as_of_time) is False:
                # returns False if there is either no kline available or the as_of_time is before we have data
                continue
            # then we check orders (from the "assets" level)
            asset.check_orders()
            # then we place new orders
            asset.place_new_orders()

    def print_position(self):
        print(f'current position {self._current_as_of_time}')

    def update_tickers(self):
        """Updates each asset with the 24 hour ticker data, weight: 40"""
        for ticker in self.client.get_ticker():
            symbol = symbol_to_asset(ticker['symbol'])
            if symbol in self._assets:
                self._assets[symbol].update_24_hour_ticker(ticker)
                print(ticker)

    @property
    def assets_by_price_change_percent(self):
        assets = list(self._assets.values())
        result = sorted(assets, key=attrgetter('change_percent'))
        print('change_percent')
        for entry in result[:4]:
            print(f'{entry} - {entry.change_percent}')
        for entry in result[-4:]:
            print(f'{entry} - {entry.change_percent}')
        return result

    @property
    def assets_by_trade_count(self):
        assets = list(self._assets.values())
        result = sorted(assets, key=attrgetter('count'))
        print('count')
        for entry in result[:4]:
            print(f'{entry} - {entry.count}')
        for entry in result[-4:]:
            print(f'{entry} - {entry.count}')
        return result

    def update_historical_klines(self):
        for asset in list(self._assets.values()):
            asset.update_historical_klines()


def symbol_to_asset(symbol):
    """Filter out USD suffix, eliminate non USD suffix items"""
    if symbol[-3:] != 'USD':
        return None
    return symbol[:-3]