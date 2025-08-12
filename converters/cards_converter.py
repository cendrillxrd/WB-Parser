from typing import Any, Dict

import pandas as pd


def convert_cards_list_to_df_for_funnel(cards_list: Dict[str, Any]) -> pd.DataFrame:
    """Преобразует данные о карточках товаров в DataFrame для воронки продаж."""
    df = pd.DataFrame(cards_list)

    def get_sex(row):
        for characteristic in row:
            if characteristic['name'] == 'Пол':
                return characteristic['value'][0]
        return 'Пол не указан'

    df = df.assign(sex=df['characteristics'].apply(get_sex))
    assigned_df = df[['nmID', 'vendorCode', 'brand', 'subjectName', 'sex']]
    assigned_df.rename({'nmID': 'Артикул WB',
                        'vendorCode': 'Артикул продавца',
                        'brand': 'Бренд',
                        'subjectName': 'Название предмета',
                        'sex': 'Пол'},
                       inplace=True,
                       axis=1)
    return assigned_df
