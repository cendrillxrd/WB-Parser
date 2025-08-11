from update_info import InfoUpdater
from utils.date_helpers import is_monday
from wildberries_collector import WildberriesDataCollector


def main():
    datacollector = WildberriesDataCollector()
    if is_monday():
        updater = InfoUpdater('C:/Users/Admin/Desktop/Воронка продаж.csv')
        updater.update_info()
    datacollector.save_info()


if __name__ == "__main__":
    main()
