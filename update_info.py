import pandas as pd
import logging

from wildberries_collector import WildberriesDataCollector
from mergers.funnel_new_info_merge import merge_funnel_and_new_info
from logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


class InfoUpdater:
    def __init__(self, file_path):
        self.file_path = file_path
        self.previous_funnel = pd.read_csv(file_path, encoding='cp1251')
        self.collector = WildberriesDataCollector()

    def get_last_two_week_dates(self) -> list[str]:
        """Возвращает последние 14 дат из таблицы. Если дат меньше, вернет все, что есть."""
        dates = self.previous_funnel['Дата'].unique()
        sorted_dates = pd.to_datetime(dates).sort_values(ascending=False)
        sorted_str_dates = [str(date.date()) for date in sorted_dates]
        return sorted_str_dates[0:14]

    def update_info(self):
        logger.info(f'Обновление информации по воронке продаж')
        """Обновляет информацию в воронке продаж за последние 14 дат."""
        dates = self.get_last_two_week_dates()
        for date in dates:
            logger.debug(f'Обновление воронки {date}')
            new_info = self.collector.get_report_response(date, date, 'funnel')

            columns_to_update = [
                'Просмотры товара', 'Добавления в корзину', 'Заказали товаров',
                'Заказали на сумму', 'Выкупили товаров', 'Выкупили на сумму',
                'Отменили товаров', 'Отменили на сумму', 'Конверсия в корзину',
                'Конверсия в заказ', 'Процент выкупа'
            ]

            merged_df = merge_funnel_and_new_info(self.previous_funnel, new_info, columns_to_update)

            for column in columns_to_update:
                merged_df[column] = merged_df[column + '_new'].combine_first(merged_df[column])
                merged_df.drop(column + '_new', axis=1, inplace=True)

            self.previous_funnel = merged_df
            for col in columns_to_update:
                self.previous_funnel[col] = pd.to_numeric(self.previous_funnel[col], downcast="integer")
            logger.debug(f'Воронка {date} обновилась')
        self.previous_funnel.to_csv(self.file_path, index=False, encoding='cp1251')
