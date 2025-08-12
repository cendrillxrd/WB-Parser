import io
import time
import uuid
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
from mergers.funnel_avg_position_merge import merge_funnel_and_avg_pos
from mergers.funnel_characteristics_merge import \
    merge_funnel_and_characteristic
from mergers.funnel_stocks_merge import merge_funnel_and_stock
from utils.api_helpers import get_analytics_report_status
from utils.date_helpers import (get_last_two_months, get_today_date,
                                get_week_number, get_yesterday_date)
from utils.file_helpers import is_csv_empty, zip_file_converter_to_df
from wildberries_api import WildberriesAPIClient

REPORT_TEMP = 5
TIME_SLEEP = 20


class WildberriesDataCollector:
    def __init__(self):
        self.api = WildberriesAPIClient()
        self.today = datetime.now(pytz.utc).date()
        self.todayDate = get_today_date()
        self.yesterdayDate = get_yesterday_date()
        self.cards_list = self.api.get_cards_list()

    def collect_daily_stats(self) -> Dict[str, pd.DataFrame]:
        """Собирает данные для таблиц."""
        return {
            'Воронка продаж': self.get_funnel_fbw_fbs_avg_pos_characteristic(),
            'Остатки': self.get_stocks_fbs_fbw_by_size()
        }

    def save_info(self):
        """Сохраняет таблицы в csv файл."""
        info = self.collect_daily_stats()
        for key, value in info.items():
            file_name = f'{key}.csv'
            if is_csv_empty(file_name):
                value.to_csv(file_name, index=False, encoding='cp1251')
            else:
                value.to_csv(file_name, mode='a', index=False, encoding='cp1251', header=False)

    def get_stocks_FBW_stats(self, nmIDs: list) -> pd.DataFrame:
        """Получение и преобразование данных об остатках на складах WB."""
        fbw_list = self.api.get_stocks(self.todayDate, self.todayDate, 'wb', nmIDs)
        fbw_df = convert_get_stocks_result_to_df(fbw_list, 'wb')
        print('Данные FBW загружены')
        return fbw_df

    def get_stocks_FBS_stats(self, nmIDs: list) -> pd.DataFrame:
        """Получение и преобразование данных об остатках на складах Продавца."""
        fbs_list = self.api.get_stocks(self.todayDate, self.todayDate, 'mp', nmIDs)
        fbs_df = convert_get_stocks_result_to_df(fbs_list, 'mp')
        print('Данные FBS загружены')
        return fbs_df

    def get_avg_pos(self, nmIDs: list, period: Literal['m', 't']) -> pd.DataFrame:
        """Получение и преобразование данных о средней позиции в поиске."""
        avg_pos_list = self.api.get_avg_position(self.todayDate, self.todayDate, self.yesterdayDate,
                                                 self.yesterdayDate, nmIDs)
        if period == 'm':
            current_start_date, current_end_date, past_start_date, past_end_date = get_last_two_months()
            avg_pos_list = self.api.get_avg_position(current_start_date, current_end_date, past_start_date,
                                                     past_end_date, nmIDs)  # период Месяц
        avg_pos_df = convert_get_avg_position_to_df(avg_pos_list, period)
        print(f'Данные AVG POS {period} загружены')
        return avg_pos_df

    def get_characteristic(self):
        """Получение и преобразование данных об основных параметрах товаров."""
        characteristic_df = convert_cards_list_to_df_for_funnel(self.cards_list)
        print('Данные characteristic загружены')
        return characteristic_df

    def waiting_of_analytics_report(self, id: str):
        """Ожидание создания отчета."""
        tries = 0
        while tries < 100:
            time.sleep(TIME_SLEEP)
            reports = self.api.get_reports_list([id])
            report_status = get_analytics_report_status(reports)
            match report_status:
                case 'SUCCESS':
                    return True
                case 'FAILED':
                    print('Отчет не сгенерировался')
                    self.api.retry_create_report(id)
                case _:
                    tries += 1
                    print('Ожидание готовности отчета')
        return False

    def get_report_response(self, start_date_time: str, end_date_time: str,
                            resport_type: Literal['stocks', 'funnel']) -> Optional[pd.DataFrame]:
        """Создание отчета по воронке продаж или остаткам."""
        for temp in range(REPORT_TEMP):
            # id = '71e96117-228d-4331-8a76-d0d7dd4b52c1'
            id = str(uuid.uuid4())
            pd.DataFrame({'ID': [id], 'date': start_date_time}).to_csv(f'ids_{resport_type}.csv',
                                                                       mode='a',
                                                                       index=False)
            self.api.create_report(id, start_date_time, end_date_time, resport_type)
            time.sleep(TIME_SLEEP)
            if self.waiting_of_analytics_report(id):
                response = self.api.get_report_response(id)
                zip_file = io.BytesIO(response.content)
                report = zip_file_converter_to_df(zip_file, resport_type)
                report['Неделя'] = get_week_number()
                print(f'Отчет загружен {start_date_time}')
                return report
            else:
                print('Не удалось загрузить отчет')
            return None

    def get_stocks_fbs_fbw_by_size(self) -> pd.DataFrame:  # для второй таблицы
        """Получение данных об остатках поразмерно."""
        stocks = self.get_report_response(self.todayDate, self.todayDate, 'stocks')
        stocks_by_size = convert_stocks_by_size(stocks)
        final_data_frame = correct_stocks_by_size_columns(stocks_by_size)
        return final_data_frame

    def get_funnel_fbw_fbs_avg_pos_characteristic(self) -> pd.DataFrame:
        """Получение итоговой таблицы по воронке продаж."""
        funnel = self.get_report_response(self.todayDate, self.todayDate, 'funnel')

        nmIDs = funnel['Артикул WB'].unique().tolist()
        fbs_df = self.get_stocks_FBS_stats(nmIDs)

        fbw_df = self.get_stocks_FBW_stats(nmIDs)

        avg_pos_month_df = self.get_avg_pos(nmIDs, 'm')
        avg_pos_today_df = self.get_avg_pos(nmIDs, 't')

        characteristic_df = convert_cards_list_to_df_for_funnel(self.cards_list)

        funnel_fbw_fbs = merge_funnel_and_stock(funnel, fbs_df, fbw_df)
        funnel_fbw_fbs_avg_pos_m = merge_funnel_and_avg_pos(funnel_fbw_fbs, avg_pos_today_df, 't')
        funnel_fbw_fbs_avg_pos_m_t = merge_funnel_and_avg_pos(funnel_fbw_fbs_avg_pos_m,
                                                              avg_pos_month_df, 'm')
        funnel_fbw_fbs_avg_pos_characteristic = merge_funnel_and_characteristic(
            funnel_fbw_fbs_avg_pos_m_t, characteristic_df)

        final_data_frame = correct_funnel_columns(funnel_fbw_fbs_avg_pos_characteristic)
        return final_data_frame
