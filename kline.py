import csv
import datetime
import os

from constants import KLINE_HEADERS


def get_kline(as_of_time, history_path):
    fname = get_file_for_time(as_of_time)
    with open(os.path.join(history_path, fname)) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if int(row['open_time']) <= as_of_time <= int(row['close_time']):
                print(f'Kline for time {as_of_time} was {row}')
                return row
    return None


def get_file_for_time(when_ms):
    """Returns the desired filename for the provided millisecond utc timestamp"""
    event_start_as_datetime = datetime.datetime.utcfromtimestamp(when_ms / 1000)
    return f"{event_start_as_datetime.strftime('%Y-%m-%d')}.csv"


def get_last_trans_close_time(path):
    contents = os.listdir(path)
    contents.sort()
    if not contents or '.csv' not in contents[-1]:
        return None
    last_entry = None
    with open(os.path.join(path, contents[-1])) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            last_entry = row
    if last_entry is None:
        return None
    print(f'last_entry was {last_entry}')
    return int(last_entry['close_time'])


def kline_row_to_dict(row):
    response = {}
    for header, val in zip(KLINE_HEADERS, row):
        response[header] = val
    return response
