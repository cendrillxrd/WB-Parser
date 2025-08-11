from typing import Literal

import pandas as pd


def convert_get_avgPosition_to_df(get_avgPosition_result: list[dict], period: Literal['m', 't']) -> pd.DataFrame:
    """Преобразует данные о средней позиции в DataFrame."""
    df = pd.DataFrame(get_avgPosition_result)
    df = df.assign(avgPosition=df['avgPosition'].apply(lambda x: x['current']))
    df = df[['nmId', 'avgPosition']]
    match period:
        case 'm':
            df.rename({'nmId': 'Артикул WB',
                       'avgPosition': 'Средняя позиция в поиске (Период 30 дней)'},
                      inplace=True,
                      axis=1)
        case 't':
            df.rename({'nmId': 'Артикул WB',
                       'avgPosition': 'Средняя позиция в поиске'},
                      inplace=True,
                      axis=1)
    return df
