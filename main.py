import datetime
import os

from binance.helpers import interval_to_milliseconds

from assets import Assets
from client.fake_client import FakeClient
from client.live_client import LiveClient
from config import API_KEY, API_SECRET
from constants import PROJECT_ROOT

# Critical to change the current working directory to the project root.  Makes images and such importable.
os.chdir(PROJECT_ROOT)


def run_app():
    online = False
    if online:
        client = LiveClient(API_KEY, API_SECRET, tld='us')
    else:
        starting_cash = 1000  # USD
        client = FakeClient(starting_cash)

    assets = Assets(client)
    if not online:
        # if we are running offline, we want to iterate through the ticker so that we can pretend to make transactions
        start_time = datetime.datetime(year=2019, month=1, day=1, tzinfo=datetime.timezone.utc)
        start_timestamp = int(start_time.timestamp() * 1000)
        interval = interval_to_milliseconds(client.KLINE_INTERVAL_15MINUTE)
        current_time = start_timestamp
        while current_time < int(datetime.datetime.now().astimezone(datetime.timezone.utc).timestamp() * 1000):
            assets.process(current_time)
            assets.print_position()
            current_time += interval

    # assets.update_tickers()
    # by_change_percent = assets.assets_by_price_change_percent
    # by_trade_count = assets.assets_by_trade_count


if __name__ == '__main__':
    run_app()

# get all symbol prices
# prices = client.get_all_tickers()
# for entry in prices:
#    if entry['symbol'][-3:] != 'USD':
#        continue
#    print(entry)

# get exchange info
# info = client.get_exchange_info()
# print(info)
