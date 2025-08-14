import os
import zipfile
from typing import Optional

import pandas as pd


def zip_file_converter_to_df(zip_file, reportType: str) -> Optional[pd.DataFrame]:
    """Преобразует архивированный csv файл в DataFrame."""
    with zipfile.ZipFile(zip_file) as z:
        csv_files = [f for f in z.namelist() if f.endswith('.csv')]

        if csv_files:
            csv_filename = csv_files[0]

            with z.open(csv_filename) as csv_file:
                match reportType:
                    case 'funnel':
                        sales_funnel = pd.read_csv(csv_file)
                        sales_funnel.rename({
                            'nmID': 'Артикул WB',
                            'dt': 'Дата',
                            'openCardCount': 'Просмотры товара',
                            'addToCartCount': 'Добавления в корзину',
                            'ordersCount': 'Заказали товаров',
                            'ordersSumRub': 'Заказали на сумму',
                            'buyoutsCount': 'Выкупили товаров',
                            'buyoutsSumRub': 'Выкупили на сумму',
                            'cancelCount': 'Отменили товаров',
                            'cancelSumRub': 'Отменили на сумму',
                            'buyoutPercent': 'Процент выкупа',
                            'addToCartConversion': 'Конверсия в корзину',
                            'cartToOrderConversion': 'Конверсия в заказ'},
                            axis=1,
                            inplace=True)
                        return sales_funnel
                    case 'stocks':
                        stocks = pd.read_csv(csv_file)
                        return stocks


def is_csv_empty(file_path: str) -> bool:
    """Проверяет, пустой ли файл."""
    if not os.path.exists(file_path):
        return True
    df = pd.read_csv(file_path, encoding='cp1251')
    return df.empty
