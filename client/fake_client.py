class FakeClient:
    """This is a fake client stub used for running offline simulations"""
    def __init__(self, starting_cash):
        self.cash = starting_cash

    def get_historical_klines(self, *args, **kwargs):
        return []
