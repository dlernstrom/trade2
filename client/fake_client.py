import os

from constants import KLINE_PATH


class FakeClient:
    """This is a fake client stub used for running offline simulations"""
    def __init__(self, starting_cash):
        self.cash = starting_cash

    def get_historical_klines(self, *args, **kwargs):
        """This is effectively a no-op in order to meet the API spec."""
        return []

    def get_account(self):
        """Return an account info from the historical data"""
        balances = [
            {'asset': 'USD', 'free': str(self.cash), 'locked': '0.0'}
        ]
        for entry in os.listdir(KLINE_PATH):
            balances.append({'asset': entry, 'free': '0.0', 'locked': '0.0'})
        print(f'Fake balances returned as: {balances}')
        return {'balances': balances}
