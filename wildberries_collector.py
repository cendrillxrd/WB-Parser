import io
import time
import uuid
import logging
from datetime import datetime
from typing import Dict, Literal, Optional

import pandas as pd
import pytz

from converters.avg_position_converter import convert_get_avg_position_to_df
from converters.cards_converter import convert_cards_list_to_df_for_funnel
from converters.correct_columns import (correct_funnel_columns,
                                        correct_stocks_by_size_columns)
from converters.stocks_converter import (convert_get_stocks_result_to_df,
                                         convert_stocks_by_size)
from converters.prices_converter import convert_prices_result_to_df
from mergers.all_merge import all_merge

from utils.api_helpers import get_analytics_report_status
from utils.date_helpers import (get_last_two_months, get_today_date,
                                get_week_number, get_yesterday_date)
from utils.file_helpers import is_csv_empty, zip_file_converter_to_df
from wildberries_api import WildberriesAPIClient
from config import FILE_PATH
from logging_config import setup_logging

logger = logging.getLogger(__name__)

REPORT_TEMP = 5
TIME_SLEEP = 20
WAITING_OF_ANALYTICS_REPORT_TRIES = 100


class WildberriesDataCollector:
    def __init__(self):
        self.api = WildberriesAPIClient()
        self.today = datetime.now(pytz.utc).date()
        self.todayDate = get_today_date()
        self.yesterdayDate = get_yesterday_date()
        self.cards_list = self.api.get_cards_list()

    def collect_daily_stats(self) -> Dict[str, pd.DataFrame]:
        """Собирает данные для таблиц."""
        logger.debug(f'Начало сбора данных')
        return {
            'Воронка продаж': self.get_final_funnel_data_frame(),
            'Остатки': self.get_stocks_fbs_fbw_by_size()
        }

    def save_info(self):
        """Сохраняет таблицы в csv файл."""
        info = self.collect_daily_stats()
        for key, value in info.items():
            file_name = f'{FILE_PATH}{key}.csv'
            file_name = f'{key}.csv'
            if is_csv_empty(file_name):
                value.to_csv(file_name, index=False, encoding='cp1251')
            else:
                value.to_csv(file_name, mode='a', index=False, encoding='cp1251', header=False)
            logger.debug(f'Таблица {key}, сохранена в {file_name}')

    def get_stocks_FBW_stats(self, nm_ids: list) -> pd.DataFrame:
        """Получение и преобразование данных об остатках на складах WB."""
        fbw_list = self.api.get_stocks(self.todayDate, self.todayDate, 'wb', nm_ids)
        fbw_df = convert_get_stocks_result_to_df(fbw_list, 'wb')
        logger.debug(f'Данные об остатках FBW загружены')
        return fbw_df

    def get_stocks_FBS_stats(self, nm_ids: list) -> pd.DataFrame:
        """Получение и преобразование данных об остатках на складах Продавца."""
        fbs_list = self.api.get_stocks(self.todayDate, self.todayDate, 'mp', nm_ids)
        fbs_df = convert_get_stocks_result_to_df(fbs_list, 'mp')
        logger.debug(f'Данные об остатках FBS загружены')
        return fbs_df

    def get_avg_pos(self, nm_ids: list, period: Literal['m', 't']) -> pd.DataFrame:
        """Получение и преобразование данных о средней позиции в поиске."""
        avg_pos_list = []
        if period == 't':
            logger.debug(f'Получение данных о средней позиции в поиске за день')
            avg_pos_list = self.api.get_avg_position(self.todayDate, self.todayDate, self.yesterdayDate,
                                                     self.yesterdayDate, nm_ids)
            logger.debug(f'Данные о средней позиции в поиске за день загружены')
        elif period == 'm':
            logger.debug(f'Получение данных о средней позиции в поиске за месяц')
            current_start_date, current_end_date, past_start_date, past_end_date = get_last_two_months()
            avg_pos_list = self.api.get_avg_position(current_start_date, current_end_date, past_start_date,
                                                     past_end_date, nm_ids)  # период Месяц
            logger.debug(f'Данные о средней позиции в поиске за день загружены')
        avg_pos_df = convert_get_avg_position_to_df(avg_pos_list, period)
        return avg_pos_df

    def get_characteristic(self):
        """Получение и преобразование данных об основных параметрах товаров."""
        logger.debug(f'Получение и преобразование данных об основных параметрах товаров')
        characteristic_df = convert_cards_list_to_df_for_funnel(self.cards_list)
        logger.debug(f'Данные об основных параметрах товаров загружены')
        return characteristic_df

    def waiting_of_analytics_report(self, id: str):
        """Ожидание создания отчета."""
        logger.debug(f'Ожидание создания отчета.')
        tries = 0
        while tries < WAITING_OF_ANALYTICS_REPORT_TRIES:
            logger.info(f'Попытка {tries}/{WAITING_OF_ANALYTICS_REPORT_TRIES}')
            time.sleep(TIME_SLEEP)
            reports = self.api.get_reports_list([id])
            report_status = get_analytics_report_status(reports)
            if report_status == 'SUCCESS':
                logger.info(f'Статус {report_status}')
                return True
            elif report_status == 'FAILED':
                logger.info(f'Статус {report_status}')
                self.api.retry_create_report(id)
            else:
                tries += 1
        return False

    def get_report_response(self, start_date_time: str, end_date_time: str,
                            resport_type: Literal['stocks', 'funnel']) -> pd.DataFrame:
        """Получение отчета по воронке продаж или остаткам."""
        if resport_type == 'stocks':
            logger_report_type = 'остаткам поразмерно'
        else:
            logger_report_type = 'воронке продаж'
        logger.debug(f'Получение отчета по {logger_report_type}')
        for temp in range(REPORT_TEMP):
            # id = '7f4a6bce-51de-40b7-9775-c859a104e73b'
            id = str(uuid.uuid4())
            pd.DataFrame({'ID': [id], 'date': start_date_time}).to_csv(f'ids_{resport_type}.csv',
                                                                       mode='a',
                                                                       index=False)
            self.api.create_report(id, start_date_time, end_date_time, resport_type)
            time.sleep(TIME_SLEEP)
            if not self.waiting_of_analytics_report(id):
                logger.exception('Не удалось загрузить отчет')
                raise Exception('Не удалось загрузить отчет')
            response = self.api.get_report_response(id)
            zip_file = io.BytesIO(response.content)
            report = zip_file_converter_to_df(zip_file, resport_type)
            logger.debug(f'Отчет загружен')
            return report

    def get_stocks_fbs_fbw_by_size(self) -> pd.DataFrame:  # для второй таблицы
        """Получение данных об остатках поразмерно."""
        logger.debug(f'Начало сбора данных поразмерным остаткам')
        stocks = self.get_report_response(self.todayDate, self.todayDate, 'stocks')
        stocks_by_size = convert_stocks_by_size(stocks)
        final_data_frame = correct_stocks_by_size_columns(stocks_by_size)
        return final_data_frame

    def collect_info(self):
        """Сбор данных для финальной таблицы."""
        funnel = self.get_report_response(self.todayDate, self.todayDate, 'funnel')  # Воронка
        funnel['Неделя'] = get_week_number()
        nm_ids = funnel['Артикул WB'].unique().tolist()

        fbs_df = self.get_stocks_FBS_stats(nm_ids)  # Остатки FBS
        fbw_df = self.get_stocks_FBW_stats(nm_ids)  # Остатки FBW
        avg_pos_month_df = self.get_avg_pos(nm_ids, 'm')  # Средняя позиция за месяц
        avg_pos_today_df = self.get_avg_pos(nm_ids, 't')  # Средняя позиция за день
        characteristic_df = self.get_characteristic()  # Данные о карточке
        prices_df = self.get_prices()  # Цены

        info = {
            'funnel': funnel,
            'fbs': fbs_df,
            'fbw': fbw_df,
            'avg_pos_today': avg_pos_today_df,
            'avg_pos_month': avg_pos_month_df,
            'characteristic': characteristic_df,
            'prices': prices_df,
        }

        return info

    def get_final_funnel_data_frame(self) -> pd.DataFrame:
        """Получение итоговой таблицы по воронке продаж."""
        logger.debug(f'Начало сбора данных по воронке продаж')
        info = self.collect_info()
        final_data_frame = all_merge(info)
        corrected_final_data_frame = correct_funnel_columns(final_data_frame)
        return corrected_final_data_frame

    def get_prices(self):
        logger.debug(f'Получение данных о ценах')
        prices_response = self.api.get_prices()
        prices_df = convert_prices_result_to_df(prices_response)
        return prices_df
