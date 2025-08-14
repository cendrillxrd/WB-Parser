import pandas as pd


def merge_funnel_and_prices(funnel: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    """Объединяет таблицы Воронка продаж и Цены."""
    funnel_prices = pd.merge(funnel, prices, on='Артикул WB', how='left')
    return funnel_prices
