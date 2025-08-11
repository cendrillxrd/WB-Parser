from typing import Literal

import pandas as pd

from utils.date_helpers import get_today_date


def convert_get_stocks_result_to_df(new_get_stocks_result: list[dict],
                                    stock_type: Literal['', 'wb', 'mp']) -> pd.DataFrame:
    """Преобразует данные об остатках в DataFrame для воронки продаж."""
    df = pd.DataFrame(new_get_stocks_result)
    df = df.assign(stockCount=df['metrics'].apply(lambda x: x['stockCount']),
                   currentPrice=df['metrics'].apply(lambda x: x['currentPrice']['minPrice'])
                   )
    if stock_type in ('wb', ''):
        df = df.assign(toClientCount=df['metrics'].apply(lambda x: x['toClientCount']),
                       fromClientCount=df['metrics'].apply(lambda x: x['fromClientCount'])
                       )
        df = df[['nmID', 'stockCount', 'toClientCount', 'fromClientCount', 'currentPrice']]
    else:
        df = df[['nmID', 'stockCount', 'currentPrice']]
    match stock_type:
        case '':
            df.rename({'nmID': 'Артикул WB',
                       'stockCount': 'Общий остаток',
                       'toClientCount': 'В пути к клиенту',
                       'fromClientCount': 'В пути от клиента',
                       'currentPrice': 'Cтоимость товара со скидкой продавца'},
                      inplace=True,
                      axis=1)
        case 'wb':
            df.rename({'nmID': 'Артикул WB',
                       'stockCount': 'Остатки FBW',
                       'toClientCount': 'В пути к клиенту',
                       'fromClientCount': 'В пути от клиента',
                       'currentPrice': 'Cтоимость товара со скидкой продавца'},
                      inplace=True,
                      axis=1)
        case 'mp':
            df.rename({'nmID': 'Артикул WB',
                       'stockCount': 'Остатки FBS',
                       'currentPrice': 'Cтоимость товара со скидкой продавца'},
                      inplace=True,
                      axis=1)
    return df


def convert_stocks_by_size(stocks: pd.DataFrame) -> pd.DataFrame:
    """Преобразует данные о поразмерных остатках в DataFrame."""
    stocks_sizes = {}

    def foo(row):
        articul = row['NmID']
        size = row['SizeName']
        region = row['RegionName']
        stock = row['StockCount']
        brand = row['BrandName']
        subject_name = row['SubjectName']
        vendor_code = row['VendorCode']

        if articul in stocks_sizes.keys():
            if size in stocks_sizes[articul]['Sizes'].keys():
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

    stocks.apply(foo, axis=1)

    stocks_lst = []
    for articul, value in stocks_sizes.items():
        for size, stock in value['Sizes'].items():
            stocks_lst.append({'Артикул WB': articul,
                               'Артикул продавца': value['VendorCode'],
                               'Бренд': value['BrandName'],
                               'Название предмета': value['SubjectName'],
                               'Размер': size,
                               'Остаток FBS': stock['FBS'],
                               'Остаток FBW': stock['FBW']})
    stocks = pd.DataFrame(stocks_lst)
    stocks = stocks[(stocks['Остаток FBS'] > 0) | (stocks['Остаток FBW'] > 0)]
    stocks['Дата'] = get_today_date()
    return stocks
