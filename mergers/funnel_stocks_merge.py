import pandas as pd


def merge_funnel_and_stock(funnel: pd.DataFrame, fbs: pd.DataFrame, fbw: pd.DataFrame) -> pd.DataFrame:
    """Объединяет таблицы Воронка продаж, Остатки FBW и Остатки FBS."""
    funnel_fbs = pd.merge(funnel, fbs, on='Артикул WB', how='left')
    funnel_fbs_fbw = pd.merge(funnel_fbs, fbw, on='Артикул WB', how='left')
    funnel_fbs_fbw = funnel_fbs_fbw.fillna(0)

    columns_to_update = ['Остатки FBS', 'Остатки FBW', 'В пути к клиенту', 'В пути от клиента']
    for col in columns_to_update:
        funnel_fbs_fbw[col] = pd.to_numeric(funnel_fbs_fbw[col], downcast="integer")

    funnel_fbs_fbw['Общий остаток'] = funnel_fbs_fbw['Остатки FBW'] + funnel_fbs_fbw['Остатки FBS']

    # Функция для объединения значений стоимости товаров
    def get_not_zero_info(row):
        if row['Cтоимость товара со скидкой продавца_x'] == 0:
            return row['Cтоимость товара со скидкой продавца_y']
        return row['Cтоимость товара со скидкой продавца_x']

    funnel_fbs_fbw['Cтоимость товара со скидкой продавца'] = funnel_fbs_fbw.apply(get_not_zero_info, axis=1)
    funnel_fbs_fbw.drop(['Cтоимость товара со скидкой продавца_x', 'Cтоимость товара со скидкой продавца_y'],
                        inplace=True,
                        axis=1)

    funnel_fbs_fbw['Cтоимость товара со скидкой продавца'] = pd.to_numeric(
        funnel_fbs_fbw['Cтоимость товара со скидкой продавца'], downcast="integer")
    return funnel_fbs_fbw
