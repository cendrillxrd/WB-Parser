import logging
import time
from typing import Dict, Literal, Optional, List

import pandas as pd
import requests

from config import API_KEYS, BASE_URLS
from utils.api_helpers import update_params_for_pagination
from logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
logging.getLogger("urllib3").propagate = False

LIMIT_CARDS = 100  # <= 100
LIMIT_STOCKS = 1000  # <= 1000
LIMIT_AVG_POS = 1000  # <= 1000
LIMIT_PRICE = 1000  # <= 1000
TIME_SLEEP_CARDS = 0.7  # >= 0.6
TIME_SLEEP_REPORTS = 20  # >= 20
TIME_SLEEP_PRICE = 1  # >= 0.6


class WildberriesAPIClient:
    def __init__(self):
        self.base_url = BASE_URLS
        self.api_key = API_KEYS
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})

    def _make_request(
            self,
            api_type: Literal['Analytics_Statistics_API_KEY', 'Content_Marketplace_API_KEY',
                              'Price_discount_API_KEY'],
            url_key: Literal['suppliers', 'content', 'seller-analytics', 'statistics',
                             'marketplace', 'dp-calendar', 'discounts-prices'],
            method: Literal['GET', 'POST'],
            endpoint: str,
            params: Optional[Dict] = None,
            payload: Optional[Dict] = None,
            retries: int = 5):
        """
            Делает запрос по API.

            Args:
                api_type (str): Тип апи ключа.
                url_key (str): Тип URL адреса запроса.
                method (str): Метод API запроса.
                endpoint (str): Эндпоинт запроса
                params (Optional[Dict]): Параметры запроса, по умолчанию None
                payload (Optional[Dict]): Данные, передаваемые в POST запрос, по умолчанию None
                retries (int): Количество попыток для повторения запроса, по умолчанию 5

            Returns:
                Возвращает либо словарь с данными или ZIP файл
            """
        url = f'{self.base_url[url_key]}{endpoint}'
        logger.info(f'Выполнение запроса по адресу {url}')

        for attempt in range(retries):
            self.session.headers.update({'Authorization': self.api_key[api_type]})
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=payload,
                timeout=10
            )
            try:
                response.raise_for_status()
                logger.info(f'Запрос выполнен успешно')
                if self.session.headers['Content-Type'] == 'application/zip':
                    return response
                return response.json()

            except requests.exceptions.HTTPError as err:
                logger.info(f'Запрос не удался, ошибка {err.response.status_code}'
                            f'Попытка {attempt + 1}/{retries}')
                if err.response.status_code in (429, 500, 502, 503, 504):
                    wait_time = min(2 ** attempt, 10)
                    logger.debug(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                raise err

            except requests.exceptions.RequestException as err:
                logger.info(f'Запрос не удался, ошибка {err.response.status_code}')
                if attempt == retries - 1:
                    raise err
                time.sleep(1)

        return None

    def get_cards_list(self) -> list[dict]:
        """
           Запрос карточек товаров.
           Например
           {
            "nmID": 12345678,
            "imtID": 123654789,
            "nmUUID": "01bda0b1-5c0b-736c-b2be-d0a6543e9be",
            "subjectID": 7771,
            "subjectName": "AKF системы",
            "vendorCode": "wb7f6mumjr1",
            "brand": "Тест",
            ...
            }
           Returns:
               list[dict]: Список словарей в которых хранится информация о товарах.
           """
        logger.info(f'Запрос карточек товаров')
        endpoint = '/content/v2/get/cards/list'
        payload = {
            'settings': {
                'cursor': {
                    'limit': LIMIT_CARDS
                },
                'filter': {
                    'withPhoto': -1
                }
            }
        }
        response = self._make_request(method='POST',
                                      api_type='Content_Marketplace_API_KEY',
                                      url_key='content',
                                      endpoint=endpoint,
                                      payload=payload)

        payload, total = update_params_for_pagination(response, LIMIT_CARDS)
        loaded_cards = LIMIT_CARDS
        logger.debug(f'Карточек загружено {loaded_cards}')
        while total >= LIMIT_CARDS:
            time.sleep(TIME_SLEEP_CARDS)
            resp = self._make_request(method='POST',
                                      api_type='Content_Marketplace_API_KEY',
                                      url_key='content',
                                      endpoint=endpoint,
                                      payload=payload)
            payload, total = update_params_for_pagination(resp, LIMIT_CARDS)
            response['cards'].extend(resp['cards'])

            loaded_cards += total
            logger.debug(f'Карточек загружено {loaded_cards}')
        return response['cards']

    def get_nm_ids(self) -> list:
        """Запрос WB артикулов товаров."""
        logger.info(f'Запрос WB артикулов товаров')
        cards_list_data = self.get_cards_list()
        df = pd.DataFrame(cards_list_data)
        cards_nm_id_lst = df['nmID'].unique().to_list()
        return cards_nm_id_lst

    def get_barcodes(self) -> list:
        """Запрос баркодов товаров."""
        logger.info(f'Запрос баркодов товаров')
        product_cards = self.get_cards_list()
        barcodes = []
        count = 0
        for card in product_cards:
            for size in card['sizes']:
                try:
                    barcodes.append(size['skus'][0])
                except IndexError:
                    pass
                count += 1
        return barcodes

    def get_reports_list(self, ids: list) -> dict:
        """
        Запрос на получение списка отчетов.

        Используется для получения статуса созданных отчетов.

        Args:
            ids (list): список состоящий из ID отчётов в UUID-формате.

        Returns:
            ZIP-FILE в котором лежит CSV файл отчета
        """
        logger.info(f'Запрос на получение списка отчетов')
        endpoint = '/api/v2/nm-report/downloads'
        params = {
            'filter[downloadIds]': ids
        }
        response = self._make_request(method='GET',
                                      api_type='Analytics_Statistics_API_KEY',
                                      url_key='seller-analytics',
                                      params=params,
                                      endpoint=endpoint)
        return response

    def get_report_response(self, id: str):
        """
        Запрос на получение отчета.

        После удачной генерации отчета (статус SUCCESS) делает запрос на получение созданного отчета.

        Args:
            id (str): ID отчёта в UUID-формате.

        Returns:
            ZIP-FILE в котором лежит CSV файл отчета
        """
        logger.info(f'Запрос на получение отчета')
        self.session.headers.update({
            'Content-Type': 'application/zip'
        })
        endpoint = f'/api/v2/nm-report/downloads/file/{id}'
        response = self._make_request(method='GET',
                                      api_type='Analytics_Statistics_API_KEY',
                                      url_key='seller-analytics',
                                      endpoint=endpoint)
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
        return response

    def retry_create_report(self, id: str):
        """
            Запрос на повторную генерацию отчета.

            В случае статуса FAILED при генерации отчета делает запрос на повторную генерацию отчета

            Args:
                id (str): ID отчёта в UUID-формате.
            """
        logger.info(f'Запрос на повторную генерацию отчета')
        endpoint = '/api/v2/nm-report/downloads/retry'
        payload = {
            "downloadId": id
        }
        self._make_request(method='POST',
                           api_type='Analytics_Statistics_API_KEY',
                           url_key='seller-analytics',
                           payload=payload,
                           endpoint=endpoint)

    def create_report(self, id: str, start_date: str, end_date: str, report_type: Literal['stocks', 'funnel'],
                      skip_deleted_nm: bool = True):
        """
        Запрос на генерацию отчета.

        Запрос на генерацию отчета с расширенной аналитикой продавца по воронке продаж или остаткам в виде csv файла.

        Args:
            id (str): ID отчёта в UUID-формате.
            start_date (str): Начало периода.
            end_date (str): Второе значение, что оно означает.
            report_type (str): Тип отчёта (Воронка продаж или Остатки)
            skip_deleted_nm (bool): Скрыть удалённые карточки товаров, по умолчанию None
        """
        endpoint = '/api/v2/nm-report/downloads'
        if report_type == 'stocks':
            logger.info(f'Запрос на генерацию отчета по остаткам поразмерно')
            report_type = 'STOCK_HISTORY_REPORT_CSV'
            payload = {
                'id': id,
                'reportType': report_type,
                'params': {
                    'currentPeriod': {
                        'start': start_date,
                        'end': end_date,
                    },
                    'skipDeletedNm': skip_deleted_nm,
                    'stockType': '',
                    'availabilityFilters': [
                        'deficient',
                        'balanced',
                        'actual',
                        'nonActual',
                        'nonLiquid',
                        'invalidData'
                    ],
                    'orderBy': {
                        'field': 'stockCount',
                        'mode': 'desc'
                    }
                }

            }
        else:
            logger.info(f'Запрос на генерацию отчета по воронке продаж')
            report_type = 'DETAIL_HISTORY_REPORT'
            payload = {
                'id': id,
                'reportType': report_type,
                'params': {
                    'startDate': start_date,
                    'endDate': end_date,
                    'skipDeletedNm': skip_deleted_nm
                }
            }

        self._make_request(method='POST',
                           api_type='Analytics_Statistics_API_KEY',
                           url_key='seller-analytics',
                           payload=payload,
                           endpoint=endpoint)

    def get_stocks(self, start_date: str, end_date: str, stock_type: Literal['', 'wb', 'mp'],
                   nm_ids: Optional[List] = None) -> list:
        """
        Запрос данных об остатках по артикулам WB.

        Запрос данных об остатках FBS, FBW по артикулам WB.
        Например:
        {
        ----"nmID": 123456789,
        ----"isDeleted": false,
        ----"subjectName": "Принтеры",
        ----"name": "Печатник 3000",
        ----...
        ----"stockCount": 50,
        ----"stockSum": 50000,
        ----...
        ----"toClientCount": 20,
        ----"fromClientCount": 30,
        ----...
        ----"availability": "deficient"
        ----}
        }

        Args:
            start_date (int): Дата начала периода. Не позднее end. Не ранее 3 месяцев от текущей даты
            end_date (str): Дата окончания периода. Не ранее 3 месяцев от текущей даты
            stock_type (str): Тип складов хранения товаров:
                                                    "" — все
                                                    wb — FBW
                                                    mp — FBS
            nm_ids (Optional[List]): Список артикулов WB, по умолчанию None.

        Returns:
            list: Список словарей с информацией о товарах
        """
        logger_stock_type = ''
        if stock_type == 'wb':
            logger_stock_type = ' FBW'
        elif stock_type == 'mp':
            logger_stock_type = ' FBS'
        logger.info(f'Запрос данных об остатках{logger_stock_type} по артикулам WB')

        endpoint = '/api/v2/stocks-report/products/products'
        response = []
        offset = 0
        count = 0
        payload = {
            'currentPeriod': {
                'start': start_date,
                'end': end_date
            },
            'stockType': stock_type,
            'skipDeletedNm': True,
            'orderBy': {
                'field': 'stockCount',
                'mode': 'desc'
            },
            'availabilityFilters': [
                'deficient',
                'balanced',
                'actual',
                'nonActual',
                'nonLiquid',
                'invalidData'
            ],
            'limit': LIMIT_STOCKS,
            'offset': offset
        }
        if nm_ids is not None:
            payload['nmIDs'] = nm_ids

        resp = self._make_request(method='POST',
                                  api_type='Analytics_Statistics_API_KEY',
                                  url_key='seller-analytics',
                                  payload=payload,
                                  endpoint=endpoint)
        items = resp['data']['items']
        antifreeze = 1000

        while items and antifreeze:
            antifreeze -= 1
            offset += LIMIT_STOCKS
            response.extend(items)
            time.sleep(TIME_SLEEP_REPORTS)
            count += len(items)
            logger.debug(f'Карточек загружено {count}')

            payload = {
                'currentPeriod': {
                    'start': start_date,
                    'end': end_date
                },
                'stockType': stock_type,
                'skipDeletedNm': True,
                'orderBy': {
                    'field': 'stockCount',
                    'mode': 'desc'
                },
                'availabilityFilters': [
                    'deficient',
                    'balanced',
                    'actual',
                    'nonActual',
                    'nonLiquid',
                    'invalidData'
                ],
                'limit': LIMIT_STOCKS,
                'offset': offset
            }
            if nm_ids is not None:
                payload['nmIDs'] = nm_ids

            resp = self._make_request(method='POST',
                                      api_type='Analytics_Statistics_API_KEY',
                                      url_key='seller-analytics',
                                      payload=payload,
                                      endpoint=endpoint)
            items = resp['data']['items']
        return response

    def get_avg_position(self, current_start_date: str, current_end_date: str, past_start_date: str, past_end_date: str,
                         nm_ids: Optional[List] = None) -> List:
        """
           Запрос данных о средней позиции в поиске.

           Запрашивает данные по поисковым запросам с:
                - общей информацией
                - позициями товаров
                - данными по видимости и переходам в карточку
                - данными для таблицы по группам
           Например:
            {
            ----"subjectName": "Phones",
            ----"subjectId": 50,
            ----"brandName": "Apple",
            ----"tagName": "phones",
            ----"tagId": 65,
            ----"metrics": {
            --------------------"avgPosition": {
            ------------------------------------"current": 5,
            ------------------------------------"dynamics": 50
            --------------------},
            --------------------...
            ----------------},
            ----"items": [
            ----------------{
            ----------------"nmId": 268913787,
            ----------------"name": "iPhone 13 256 ГБ Серебристый",
            ----------------"vendorCode": "wb3ha2668w",
            ----------------"subjectName": "Смартфоны",
            ----------------...
            ----------------}
            ------------]
            }
           Args:
               current_start_date (str): Дата начала текущего периода. Не позднее end. Не ранее 365 суток от сегодня
               current_end_date (str): Дата окончания текущего периода. Не ранее 365 суток от сегодня
               past_start_date (str): Дата начала прошлого периода. Не позднее end. Не ранее 365 суток от сегодня
               past_end_date (str): Дата окончания прошлого периода. Не ранее 365 суток от сегодня
               nm_ids (Optional[List]): Список артикулов WB, по умолчанию None.

           Returns:
               list: Список словарей с информацией о товарах.
           """
        logger.info(f'Запрос данных о средней позиции в поиске')
        endpoint = '/api/v2/search-report/report'
        results = []
        offset = 0
        count = 0
        payload = {
            'currentPeriod': {
                'start': current_start_date,
                'end': current_end_date
            },
            'pastPeriod': {
                'start': past_start_date,
                'end': past_end_date
            },
            'positionCluster': 'all',
            'orderBy': {
                'field': 'avgPosition',
                'mode': 'desc'
            },
            'limit': LIMIT_AVG_POS,
            'offset': offset
        }

        if nm_ids is not None:
            payload['nmIDs'] = nm_ids

        resp = self._make_request(method='POST',
                                  api_type='Analytics_Statistics_API_KEY',
                                  url_key='seller-analytics',
                                  payload=payload,
                                  endpoint=endpoint)
        groups = resp['data']['groups']
        antifreeze = 1000

        while groups and antifreeze:
            antifreeze -= 1
            items = groups[-1]['items']
            offset += LIMIT_AVG_POS
            results.extend(items)
            time.sleep(TIME_SLEEP_REPORTS)
            count += len(items)
            logger.debug(f'Карточек загружено {count}')

            payload = {
                'currentPeriod': {
                    'start': current_start_date,
                    'end': current_end_date
                },
                'pastPeriod': {
                    'start': past_start_date,
                    'end': past_end_date
                },
                'positionCluster': 'all',
                'orderBy': {
                    'field': 'avgPosition',
                    'mode': 'desc'
                },
                'limit': LIMIT_AVG_POS,
                'offset': offset
            }

            if nm_ids is not None:
                payload['nmIDs'] = nm_ids

            resp = self._make_request(method='POST',
                                      api_type='Analytics_Statistics_API_KEY',
                                      url_key='seller-analytics',
                                      payload=payload,
                                      endpoint=endpoint)
            groups = resp['data']['groups']
        return results

    def get_prices(self) -> list[dict]:
        """
           Запрос данных о ценах на товары.

           Запрашивает данные о товарах по их артикулам: цены, валюту, общие скидки и скидки для WB Клуба.
           Например:
            {
            --------"nmID": 98486,
            --------"vendorCode": "07326060",
            --------"sizes": [
            --------------------{
            ------------------------"sizeID": 3123515574,
            ------------------------"price": 500,
            ------------------------"discountedPrice": 350,
            ------------------------"clubDiscountedPrice": 332.5,
            ------------------------"techSizeName": "42"
            --------------------}
            --------],
            --------"currencyIsoCode4217": "RUB",
            --------"discount": 30,
            --------"clubDiscount": 5,
            --------"editableSizePrice": true
            ----}
           Returns:
               list[dict]: Список словарей в которых хранится информация о товарах.
           """
        logger.info(f'Получение данных о ценах на товары')
        endpoint = '/api/v2/list/goods/filter'
        offset = 0
        result = []
        count = 0

        params = {
            'limit': LIMIT_PRICE,
            'offset': offset
        }
        response = self._make_request(method='GET',
                                      api_type='Price_discount_API_KEY',
                                      url_key='discounts-prices',
                                      params=params,
                                      endpoint=endpoint)
        list_goods = response['data']['listGoods']
        antifreeze = 1000

        while list_goods and antifreeze:
            antifreeze -= 1
            offset += LIMIT_PRICE
            result.extend(list_goods)
            time.sleep(TIME_SLEEP_PRICE)
            count += len(list_goods)
            logger.debug(f'Карточек загружено {count}')

            params = {
                'limit': LIMIT_PRICE,
                'offset': offset
            }
            response = self._make_request(method='GET',
                                          api_type='Price_discount_API_KEY',
                                          url_key='discounts-prices',
                                          params=params,
                                          endpoint=endpoint)
            list_goods = response['data']['listGoods']
        return result
