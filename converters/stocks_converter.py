from typing import Literal

import pandas as pd

from utils.date_helpers import get_today_date, get_week_number


def convert_get_stocks_result_to_df(new_get_stocks_result: list[dict],
                                    stock_type: Literal['', 'wb', 'mp']) -> pd.DataFrame:
    """Преобразует данные об остатках в DataFrame для воронки продаж."""
    df = pd.DataFrame(new_get_stocks_result)

    def correct_availability_names(row):
        availability = row['availability']

        names = {
            'deficient': 'Дефицит',
            'actual': 'Актуальный',
            'balanced': 'Баланс',
            'nonActual': 'Неактуальный',
            'nonLiquid': 'Неликвид',
            'invalidData': 'Не рассчитано'}
        if availability in names:
            return names[availability]

    assigned_df = df.assign(stockCount=df['metrics'].apply(lambda x: x['stockCount']),
                            currentPrice=df['metrics'].apply(lambda x: x['currentPrice']['minPrice']),
                            availability=df['metrics'].apply(correct_availability_names)
                            )
    if stock_type in ('wb', ''):
        assigned_df_2 = assigned_df.assign(toClientCount=df['metrics'].apply(lambda x: x['toClientCount']),
                                           fromClientCount=df['metrics'].apply(lambda x: x['fromClientCount'])
                                           )
        corrected_df = assigned_df_2[['nmID', 'stockCount', 'toClientCount', 'fromClientCount',
                                      'currentPrice', 'availability']].copy()
    else:
        corrected_df = assigned_df[['nmID', 'stockCount', 'currentPrice', 'availability']].copy()

    if stock_type == '':
        corrected_df.rename({'nmID': 'Артикул WB',
                             'stockCount': 'Общий остаток',
                             'toClientCount': 'В пути к клиенту',
                             'fromClientCount': 'В пути от клиента',
                             'currentPrice': 'Cтоимость товара со скидкой продавца',
                             'availability': 'Доступность товара'},
                            inplace=True,
                            axis=1)
    elif stock_type == 'wb':
        corrected_df.rename({'nmID': 'Артикул WB',
                             'stockCount': 'Остатки FBW',
                             'toClientCount': 'В пути к клиенту',
                             'fromClientCount': 'В пути от клиента',
                             'currentPrice': 'Cтоимость товара со скидкой продавца',
                             'availability': 'Доступность товара'},
                            inplace=True,
                            axis=1)
    else:
        corrected_df.rename({'nmID': 'Артикул WB',
                             'stockCount': 'Остатки FBS',
                             'currentPrice': 'Cтоимость товара со скидкой продавца',
                             'availability': 'Доступность товара'},
                            inplace=True,
                            axis=1)
    return corrected_df


def convert_stocks_by_size(stocks: pd.DataFrame) -> pd.DataFrame:
    """Преобразует данные о поразмерных остатках в DataFrame."""
    stocks_sizes = {}

    def get_fbw_fbs_by_size(row):
        articul = row['NmID']
        size = row['SizeName']
        region = row['RegionName']
        stock = row['StockCount']
        brand = row['BrandName']
        subject_name = row['SubjectName']
        vendor_code = row['VendorCode']

        if articul in stocks_sizes:
            if size in stocks_sizes[articul]['Sizes']:
                if region == 'Маркетплейс':
                    stocks_sizes[articul]['Sizes'][size]['FBS'] = stock
                else:
                    stocks_sizes[articul]['Sizes'][size]['FBW'] += stock
            else:
                stocks_sizes[articul]['Sizes'][size] = {}
                stocks_sizes[articul]['Sizes'][size]['FBS'] = 0
                stocks_sizes[articul]['Sizes'][size]['FBW'] = 0
                if region == 'Маркетплейс':
                    stocks_sizes[articul]['Sizes'][size]['FBS'] = stock
                else:
                    stocks_sizes[articul]['Sizes'][size]['FBW'] += stock
        else:
            stocks_sizes[articul] = {
                'VendorCode': vendor_code,
                'BrandName': brand,
                'SubjectName': subject_name,
                'Sizes': {}
            }
            stocks_sizes[articul]['Sizes'][size] = {}
            stocks_sizes[articul]['Sizes'][size]['FBS'] = 0
            stocks_sizes[articul]['Sizes'][size]['FBW'] = 0
            if region == 'Маркетплейс':
                stocks_sizes[articul]['Sizes'][size]['FBS'] += stock
            else:
                stocks_sizes[articul]['Sizes'][size]['FBW'] += stock

    stocks.apply(get_fbw_fbs_by_size, axis=1)

    stocks_list = []
    for articul, value in stocks_sizes.items():
        for size, stock in value['Sizes'].items():
            stocks_list.append({'Артикул WB': articul,
                                'Артикул продавца': value['VendorCode'],
                                'Бренд': value['BrandName'],
                                'Название предмета': value['SubjectName'],
                                'Размер': size,
                                'Остаток FBS': stock['FBS'],
                                'Остаток FBW': stock['FBW']})
    stocks = pd.DataFrame(stocks_list)
    stocks = stocks[(stocks['Остаток FBS'] > 0) | (stocks['Остаток FBW'] > 0)]
    stocks['Дата'] = get_today_date()
    stocks['Неделя'] = get_week_number()
    return stocks
