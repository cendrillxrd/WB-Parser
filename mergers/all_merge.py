import pandas as pd
import logging

from mergers.funnel_avg_position_merge import merge_funnel_and_avg_pos
from mergers.funnel_characteristics_merge import \
    merge_funnel_and_characteristic
from mergers.funnel_prices_merge import merge_funnel_and_prices
from mergers.funnel_stocks_merge import merge_funnel_and_stock
from logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def all_merge(info: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Объединение всех данных."""
    logger.info(f'Объединение всех данных')
    funnel, fbs_df, fbw_df, avg_pos_today_df, avg_pos_month_df, characteristic_df, prices_df = info.values()

    funnel_fbw_fbs = merge_funnel_and_stock(funnel, fbs_df, fbw_df)
    funnel_fbw_fbs_avg_pos_m = merge_funnel_and_avg_pos(funnel_fbw_fbs, avg_pos_today_df, 't')
    funnel_fbw_fbs_avg_pos_m_t = merge_funnel_and_avg_pos(funnel_fbw_fbs_avg_pos_m,
                                                          avg_pos_month_df, 'm')
    funnel_fbw_fbs_avg_pos_characteristic = merge_funnel_and_characteristic(
        funnel_fbw_fbs_avg_pos_m_t, characteristic_df)

    funnel_fbw_fbs_avg_pos_characteristic_price = merge_funnel_and_prices(funnel_fbw_fbs_avg_pos_characteristic,
                                                                          prices_df)
    return funnel_fbw_fbs_avg_pos_characteristic_price
