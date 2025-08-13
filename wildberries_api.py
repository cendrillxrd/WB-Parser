import logging
import time
from typing import Any, Dict, Literal, Optional

import pandas as pd
import requests

from config import API_KEYS, BASE_URLS
from utils.api_helpers import update_params_for_pagination

logger = logging.getLogger(__name__)
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
            api_type: str,
            url_key: Literal['suppliers', 'content', 'seller-analytics', 'statistics', 'marketplace', 'dp-calendar', 'discounts-prices'],
            method: str,
            endpoint: str,
            params: Optional[Dict] = None,
            payload: Optional[Dict] = None,
            retries: int = 3) -> Optional[Dict]:
        """Делает запрос по API."""
        url = f'{self.base_url[url_key]}{endpoint}'

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
                if self.session.headers['Content-Type'] == 'application/zip':
                    return response
                return response.json()

            except requests.exceptions.HTTPError as err:
                logger.warning(
                    f"Attempt {attempt + 1}/{retries} failed. "
                    f"URL: {url}, Status: {err.response.status_code}, "
                    f"Error: {str(err)}"
                )
                if err.response.status_code in (429, 500, 502, 503, 504):
                    wait_time = min(2 ** attempt, 10)
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                raise err

            except requests.exceptions.RequestException as err:
                if attempt == retries - 1:
                    raise err
                time.sleep(1)

        return None

    def get_cards_list(self) -> Dict[str, Any]:
        """Получение карточек товаров."""
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
        print(loaded_cards)
        while total >= LIMIT_CARDS:
            time.sleep(TIME_SLEEP_CARDS)
            resp = self._make_request(method='POST',
                                      api_type='Content_Marketplace_API_KEY',
                                      url_key='content',
                                      endpoint=endpoint,
                                      payload=payload)
            payload, total = update_params_for_pagination(resp, LIMIT_CARDS)
            response['cards'] += resp['cards']

            loaded_cards += total
            print(loaded_cards)
        return response['cards']

    def get_nmIds(self) -> list:
        """Получение артикулов WB."""
        cards_list_data = self.get_cards_list()
        df = pd.DataFrame(cards_list_data)
        cards_nmID_lst = df['nmID'].unique().to_list()
        return cards_nmID_lst

    def get_barcodes(self) -> list:
        """Получение баркодов"""
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

    def get_reports_list(self, ids: list):
        """Получение списка отчетов."""
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
        """Получение отчета."""
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
        """Повторная генерация отчета"""
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
                      skipDeletedNm=True):
        """Генерация отчета."""
        endpoint = '/api/v2/nm-report/downloads'
        if report_type == 'stocks':
            report_type = 'STOCK_HISTORY_REPORT_CSV'
            payload = {
                'id': id,
                'reportType': report_type,
                'params': {
                    'currentPeriod': {
                        'start': start_date,
                        'end': end_date,
                    },
                    'skipDeletedNm': skipDeletedNm,
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
            report_type = 'DETAIL_HISTORY_REPORT'
            payload = {
                'id': id,
                'reportType': report_type,
                'params': {
                    'startDate': start_date,
                    'endDate': end_date,
                    'skipDeletedNm': skipDeletedNm
                }
            }

        self._make_request(method='POST',
                           api_type='Analytics_Statistics_API_KEY',
                           url_key='seller-analytics',
                           payload=payload,
                           endpoint=endpoint)

    def get_stocks(self, start_date: str, end_date: str, stock_type: Literal['', 'wb', 'mp'], nmIDs=None) -> list:
        """Получение данных об остатках по товарам."""
        endpoint = '/api/v2/stocks-report/products/products'
        response = []
        offset = 0
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
        if nmIDs is not None:
            payload['nmIDs'] = nmIDs

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
            if nmIDs is not None:
                payload['nmIDs'] = nmIDs

            resp = self._make_request(method='POST',
                                      api_type='Analytics_Statistics_API_KEY',
                                      url_key='seller-analytics',
                                      payload=payload,
                                      endpoint=endpoint)
            items = resp['data']['items']
        return response

    def get_avg_position(self, currentStartDate: str, currentEndDate: str, pastStartDate: str, pastWndDate: str,
                         nmIDs=None) -> list:
        """Получение данных о средней позиции в поиске."""
        endpoint = '/api/v2/search-report/report'
        results = []
        offset = 0
        payload = {
            'currentPeriod': {
                'start': currentStartDate,
                'end': currentEndDate
            },
            'pastPeriod': {
                'start': pastStartDate,
                'end': pastWndDate
            },
            'positionCluster': 'all',
            'orderBy': {
                'field': 'avgPosition',
                'mode': 'desc'
            },
            'limit': LIMIT_AVG_POS,
            'offset': offset
        }

        if nmIDs is not None:
            payload['nmIDs'] = nmIDs

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

            payload = {
                'currentPeriod': {
                    'start': currentStartDate,
                    'end': currentEndDate
                },
                'pastPeriod': {
                    'start': pastStartDate,
                    'end': pastWndDate
                },
                'positionCluster': 'all',
                'orderBy': {
                    'field': 'avgPosition',
                    'mode': 'desc'
                },
                'limit': LIMIT_AVG_POS,
                'offset': offset
            }

            if nmIDs is not None:
                payload['nmIDs'] = nmIDs

            resp = self._make_request(method='POST',
                                      api_type='Analytics_Statistics_API_KEY',
                                      url_key='seller-analytics',
                                      payload=payload,
                                      endpoint=endpoint)
            groups = resp['data']['groups']
        return results

    def get_prices(self):
        endpoint = '/api/v2/list/goods/filter'
        offset = 0
        result = []

        params = {
            'limit': LIMIT_PRICE,
            'offset': offset
        }
        response = self._make_request(method='GET',
                                      api_type='API_PAPA',
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
            print(len(list_goods))

            params = {
                'limit': LIMIT_PRICE,
                'offset': offset
            }
            response = self._make_request(method='GET',
                                          api_type='API_PAPA',
                                          url_key='discounts-prices',
                                          params=params,
                                          endpoint=endpoint)
            list_goods = response['data']['listGoods']
        return result


