from typing import Literal

import pandas as pd


def merge_funnel_and_avg_pos(funnel: pd.DataFrame, avg_pos: pd.DataFrame, period: Literal['m', 't']) -> pd.DataFrame:
    """Объединяет таблицы Воронка продаж и Средняя позиция в поиске"""
    funnel_avg_pos = pd.merge(funnel, avg_pos, on='Артикул WB', how='left')
    funnel_avg_pos = funnel_avg_pos.fillna(0)
    match period:
        case 't':
            funnel_avg_pos['Средняя позиция в поиске'] = pd.to_numeric(
                funnel_avg_pos['Средняя позиция в поиске'],
                downcast="integer")
        case 'm':
            funnel_avg_pos['Средняя позиция в поиске (Период 30 дней)'] = pd.to_numeric(
                funnel_avg_pos['Средняя позиция в поиске (Период 30 дней)'],
                downcast="integer")
    return funnel_avg_pos
