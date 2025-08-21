import pandas as pd


def merge_funnel_and_characteristic(funnel: pd.DataFrame, characteristic: pd.DataFrame) -> pd.DataFrame:
    """Объединяет таблицы Воронка продаж и Характеристики."""
    funnel_characteristic = pd.merge(funnel, characteristic, on='Артикул WB', how='left')
    return funnel_characteristic
