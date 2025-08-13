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

    columns_for_merges = ['Cтоимость товара со скидкой продавца', 'Доступность товара']

    for col in columns_for_merges:
        def get_not_zero_info_price(row):
            if row[f'{col}_x'] in (0, 'Не рассчитано'):
                return row[f'{col}_y']
            return row[f'{col}_x']

        funnel_fbs_fbw[col] = funnel_fbs_fbw.apply(get_not_zero_info_price, axis=1)
        funnel_fbs_fbw.drop([f'{col}_x', f'{col}_y'],
                            inplace=True,
                            axis=1)

    funnel_fbs_fbw['Cтоимость товара со скидкой продавца'] = pd.to_numeric(
        funnel_fbs_fbw['Cтоимость товара со скидкой продавца'], downcast="integer")

    funnel_fbs_fbw['Доступность товара'] = funnel_fbs_fbw['Доступность товара'].replace(0, 'Не рассчитано')

    return funnel_fbs_fbw
