import pandas as pd


def merge_funnel_and_stock(funnel: pd.DataFrame, fbs: pd.DataFrame, fbw: pd.DataFrame) -> pd.DataFrame:
    """Объединяет таблицы Воронка продаж, Остатки FBW и Остатки FBS"""
    funnel_fbs = pd.merge(funnel, fbs, on='Артикул WB', how='left')
    funnel_fbs_fbw = pd.merge(funnel_fbs, fbw, on='Артикул WB', how='left')
    funnel_fbs_fbw = funnel_fbs_fbw.fillna(0)
    funnel_fbs_fbw['Остатки FBS'] = pd.to_numeric(funnel_fbs_fbw['Остатки FBS'], downcast="integer")
    funnel_fbs_fbw['Остатки FBW'] = pd.to_numeric(funnel_fbs_fbw['Остатки FBW'], downcast="integer")
    funnel_fbs_fbw['В пути к клиенту'] = pd.to_numeric(funnel_fbs_fbw['В пути к клиенту'], downcast="integer")
    funnel_fbs_fbw['В пути от клиента'] = pd.to_numeric(funnel_fbs_fbw['В пути от клиента'], downcast="integer")
    funnel_fbs_fbw['Общий остаток'] = funnel_fbs_fbw['Остатки FBW'] + funnel_fbs_fbw['Остатки FBS']

    # Функция для объединения значений стоимости товаров
    def foo(row):
        if row['Cтоимость товара со скидкой продавца_x'] == row['Cтоимость товара со скидкой продавца_y']:
            return row['Cтоимость товара со скидкой продавца_x']
        elif row['Cтоимость товара со скидкой продавца_x'] == 0:
            return row['Cтоимость товара со скидкой продавца_y']
        else:
            return row['Cтоимость товара со скидкой продавца_x']

    funnel_fbs_fbw['Cтоимость товара со скидкой продавца'] = funnel_fbs_fbw.apply(foo, axis=1)
    funnel_fbs_fbw.drop(['Cтоимость товара со скидкой продавца_x'], inplace=True, axis=1)
    funnel_fbs_fbw.drop(['Cтоимость товара со скидкой продавца_y'], inplace=True, axis=1)

    funnel_fbs_fbw['Cтоимость товара со скидкой продавца'] = pd.to_numeric(
        funnel_fbs_fbw['Cтоимость товара со скидкой продавца'], downcast="integer")
    return funnel_fbs_fbw
