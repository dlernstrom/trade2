import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
KLINE_PATH = os.path.join(PROJECT_ROOT, 'historical_kline')
KLINE_HEADERS = ['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume',
                 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'can_be_ignored']
