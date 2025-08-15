import logging
import pandas as pd

from update_info import InfoUpdater
from utils.date_helpers import is_sunday
from wildberries_collector import WildberriesDataCollector
from config import FILE_PATH
from logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def main():
    logger.info(f'Запуск программы')
    datacollector = WildberriesDataCollector()
    if is_sunday():
        logger.info(f'Обновление воронки продаж')
        updater = InfoUpdater(f'{FILE_PATH}Воронка продаж.csv')
        updater.update_info()
    datacollector.save_info()
    logger.info(f'Данные успешно загружены')


if __name__ == "__main__":
    main()
