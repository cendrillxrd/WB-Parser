import pandas as pd

from update_info import InfoUpdater
from utils.date_helpers import is_sunday
from wildberries_collector import WildberriesDataCollector
from config import FILE_PATH


def main():
    datacollector = WildberriesDataCollector()
    if is_sunday():
        updater = InfoUpdater(f'{FILE_PATH}Воронка продаж.csv')
        updater.update_info()
    datacollector.save_info()


if __name__ == "__main__":
    main()
