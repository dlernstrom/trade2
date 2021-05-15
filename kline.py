import csv
import datetime
import os

from constants import KLINE_HEADERS
from exceptions import KlineFileDoesNotExistError


def get_kline(as_of_time, history_path):
    fname = get_file_for_time(as_of_time)
    desired_file = os.path.join(history_path, fname)
    if not os.path.exists(desired_file):
        raise KlineFileDoesNotExistError(f'requested kline file does not exist: {desired_file}')
    with open(desired_file) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if int(row['open_time']) <= as_of_time <= int(row['close_time']):
                print(f'Kline for time {as_of_time} was {row}')
                return row
    raise KlineFileDoesNotExistError(f'requested kline does not exist')


def get_first_kline(history_path):
    desired_file = get_first_kline_file(history_path)
    with open(desired_file) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            print(f'First Kline entry was {row}')
            return row
    raise KlineFileDoesNotExistError(f'requested kline was empty')


def get_first_trans_open_time(path):
    kline = get_first_kline(path)
    return int(kline['open_time'])


def get_file_for_time(when_ms):
    """Returns the desired filename for the provided millisecond utc timestamp"""
    event_start_as_datetime = datetime.datetime.utcfromtimestamp(when_ms / 1000)
    return f"{event_start_as_datetime.strftime('%Y-%m-%d')}.csv"


def get_first_kline_file(path):
    contents = os.listdir(path)
    contents.sort()
    if not contents or '.csv' not in contents[0]:
        raise KlineFileDoesNotExistError(f'requested kline file does not exist')
    return os.path.join(path, contents[0])


def get_last_kline_file(path):
    contents = os.listdir(path)
    contents.sort()
    if not contents or '.csv' not in contents[-1]:
        raise KlineFileDoesNotExistError(f'requested kline file does not exist')
    return os.path.join(path, contents[-1])


def get_last_kline(history_path):
    last_kline_file = get_last_kline_file(history_path)
    last_entry = None
    with open(last_kline_file) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            last_entry = row
    if last_entry is None:
        raise KlineFileDoesNotExistError(f'requested kline file does not exist')


def get_last_trans_close_time(path):
    last_entry = get_last_kline(path)
    print(f'last_entry was {last_entry}')
    return int(last_entry['close_time'])


def kline_row_to_dict(row):
    response = {}
    for header, val in zip(KLINE_HEADERS, row):
        response[header] = val
    return response
