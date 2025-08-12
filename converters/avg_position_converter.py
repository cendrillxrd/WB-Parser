from typing import Literal

import pandas as pd


def convert_get_avg_position_to_df(get_avg_position_result: list[dict], period: Literal['m', 't']) -> pd.DataFrame:
    """Преобразует данные о средней позиции в DataFrame."""
    df = pd.DataFrame(get_avg_position_result)
    assigned_df = df.assign(avgPosition=df['avgPosition'].apply(lambda x: x['current']))
    cleaned_df = assigned_df[['nmId', 'avgPosition']]
    match period:
        case 'm':
            cleaned_df.rename({'nmId': 'Артикул WB',
                               'avgPosition': 'Средняя позиция в поиске (Период 30 дней)'},
                              inplace=True,
                              axis=1)
        case 't':
            cleaned_df.rename({'nmId': 'Артикул WB',
                               'avgPosition': 'Средняя позиция в поиске'},
                              inplace=True,
                              axis=1)
    return cleaned_df
