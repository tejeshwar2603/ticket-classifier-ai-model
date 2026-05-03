import csv
from pathlib import Path
import re

DATA_PATH = Path(__file__).parent / 'data' / 'logs.csv'


def load_logs():
    data = set()
    if not DATA_PATH.exists():
        return data
    with DATA_PATH.open(newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            log = row.get('log')
            if log:
                data.add(log)
    return data


data = load_logs()


def classify_log(log):
    if log in data:
        return 'Log entry found in data'
    if re.search(r'ERROR', log):
        return 'Error'
    elif re.search(r'WARNING', log):
        return 'Warning'
    elif re.search(r'INFO', log):
        return 'Info'
    elif re.search(r'DEBUG', log):
        return 'Debug'
    else:
        return 'Unknown'


if __name__ == '__main__':
    log_entry = "2024-06-01 12:00:00 ERROR Something went wrong"
    classification = classify_log(log_entry)
    print(f"The log entry is classified as: {classification}")
