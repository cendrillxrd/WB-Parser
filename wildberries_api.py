import logging
import time
from typing import Any, Dict, Literal, Optional

import pandas as pd
import requests

from config import API_KEYS, BASE_URLS

logger = logging.getLogger(__name__)


class WildberriesAPIClient:
    def __init__(self):
        self.base_url = BASE_URLS
        self.api_key = API_KEYS
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        self.LIMIT_cards = 100

    def _make_request(
            self,
            api_type: str,
            url_key: Literal['suppliers', 'content', 'seller-analytics', 'statistics', 'marketplace', 'dp-calendar'],
            method: str,
            endpoint: str,
            params: Optional[Dict] = None,
            payload: Optional[Dict] = None,
            retries: int = 3) -> Optional[Dict]:
        url = f'{self.base_url[url_key]}{endpoint}'

        for attempt in range(retries):
            try:
                self.session.headers.update({'Authorization': self.api_key[api_type]})
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=payload,
                    timeout=10
                )

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

    def _update_params_for_pagination(self, response):
        updated_at, nmID, total = response['cursor'].values()
        payload = {
            'settings': {
                'cursor': {
                    'limit': self.LIMIT_cards,
                    'updatedAt': updated_at,
                    'nmID': nmID
                },
                'filter': {
                    'withPhoto': -1
                }
            }
        }
        return payload, total

    def get_cards_list(self) -> Dict[str, Any]:
        endpoint = '/content/v2/get/cards/list'
        temp = 100
        payload = {
            'settings': {
                'cursor': {
                    'limit': self.LIMIT_cards
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

        payload, total = self._update_params_for_pagination(response)
        while total >= self.LIMIT_cards:
            time.sleep(0.7)
            resp = self._make_request(method='POST',
                                      api_type='Content_Marketplace_API_KEY',
                                      url_key='content',
                                      endpoint=endpoint,
                                      payload=payload)
            payload, total = self._update_params_for_pagination(resp)
            response['cards'] += resp['cards']

            temp += total
            print(temp)
        return response['cards']

    def get_nmIds(self) -> list:
        cards_list_data = self.get_cards_list()
        df = pd.DataFrame(cards_list_data)
        cards_nmID_lst = df['nmID'].unique().to_list()
        return cards_nmID_lst

    def get_barcodes(self) -> list:
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

    # def get_promotions(self, startDateTime, endDateTime):
    #     endpoint = '/api/v1/calendar/promotions'
    #     params = {
    #         'startDateTime': startDateTime,
    #         'endDateTime': endDateTime,
    #         'allPromo': True,
    #     }
    #     response = self._make_request(method='GET',
    #                                   api_type='API_KEY3',
    #                                   url_key='dp-calendar',
    #                                   params=params,
    #                                   endpoint=endpoint)
    #     promotions = response['data']['promotions']
    #     return promotions
    #
    # def get_active_promotions_ids(self, startDateTime, endDateTime):
    #     df = self.get_promotions(startDateTime, endDateTime)
    #     df = pd.DataFrame(df)
    #     df['startDateTime'] = pd.to_datetime(df['startDateTime'])
    #     df['endDateTime'] = pd.to_datetime(df['endDateTime'])
    #
    #     now = pd.to_datetime(datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))
    #
    #     # Фильтрация активных акций
    #     active_promotions = df[(df['startDateTime'] <= now) & (df['endDateTime'] >= now)]
    #     id_active_promotions = active_promotions['id'].to_list()
    #     return id_active_promotions

    def get_reports_list(self, ids: list):
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

    def get_report_response(self, id):
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

    def retry_create_report(self, id):
        endpoint = '/api/v2/nm-report/downloads/retry'
        payload = {
            "downloadId": id
        }
        self._make_request(method='POST',
                           api_type='Analytics_Statistics_API_KEY',
                           url_key='seller-analytics',
                           payload=payload,
                           endpoint=endpoint)

    def create_report(self, id, start_date, end_date, report_type: Literal['stocks', 'funnel'],
                      skipDeletedNm=True):
        match report_type:
            case 'stocks':
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
            case 'funnel':
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

        endpoint = '/api/v2/nm-report/downloads'
        self._make_request(method='POST',
                           api_type='Analytics_Statistics_API_KEY',
                           url_key='seller-analytics',
                           payload=payload,
                           endpoint=endpoint)

    def get_stocks(self, start_date, end_date, stock_type: Literal['', 'wb', 'mp'], nmIDs=None) -> list:
        endpoint = '/api/v2/stocks-report/products/products'
        response = []
        offset = 0
        while True:
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
                'limit': 1000,
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
            if items == []:
                break
            offset += 1000
            response += items
            time.sleep(20)
        return response

    def get_avgPosition(self, currentStartDate, currentEndDate, pastStartDate, pastWndDate, nmIDs=None) -> list:
        endpoint = '/api/v2/search-report/report'
        results = []
        offset = 0
        while True:
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
                'limit': 1000,
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
            if groups == []:
                break
            items = groups[-1]['items']
            offset += 1000
            results += items
            time.sleep(20)
        return results
