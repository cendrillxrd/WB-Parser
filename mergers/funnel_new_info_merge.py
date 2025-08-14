import pandas as pd


def merge_funnel_and_new_info(previous_funnel: pd.DataFrame, new_info: pd.DataFrame, columns_to_update: list) -> pd.DataFrame:
    merged_df = pd.merge(
        previous_funnel,
        new_info[['Артикул WB', 'Дата'] + columns_to_update],
        on=['Артикул WB', 'Дата'],
        how='left',
        suffixes=('', '_new')
    )
    return merged_df
