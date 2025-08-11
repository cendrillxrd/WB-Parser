import pandas as pd

from wildberries_collector import WildberriesDataCollector


class InfoUpdater:
    def __init__(self, file_path):
        self.file_path = file_path
        self.previous_funnel = pd.read_csv(file_path, encoding='cp1251')
        self.collector = WildberriesDataCollector()

    def get_last_two_week_dates(self):
        dates = self.previous_funnel['Дата'].unique()
        sorted_dates = pd.to_datetime(dates).sort_values(ascending=False)
        sorted_str_dates = [str(date.date()) for date in sorted_dates]
        return sorted_str_dates[0:14]

    def update_info(self):
        dates = self.get_last_two_week_dates()
        for date in dates:
            new_info = self.collector.get_report_response(date, date, 'funnel')

            columns_to_update = [
                'Просмотры товара', 'Добавления в корзину', 'Заказали товаров',
                'Заказали на сумму', 'Выкупили товаров', 'Выкупили на сумму',
                'Отменили товаров', 'Отменили на сумму', 'Конверсия в корзину',
                'Конверсия в заказ', 'Процент выкупа'
            ]

            merged_df = pd.merge(
                self.previous_funnel,
                new_info[['Артикул WB', 'Дата'] + columns_to_update],
                on=['Артикул WB', 'Дата'],
                how='left',
                suffixes=('', '_new')
            )

            for column in columns_to_update:
                merged_df[column] = merged_df[column + '_new'].combine_first(merged_df[column])
                merged_df.drop(column + '_new', axis=1, inplace=True)

            self.previous_funnel = merged_df
            for col in columns_to_update:
                self.previous_funnel[col] = pd.to_numeric(self.previous_funnel[col], downcast="integer")
            print(f'Обновилась дата {date}')
        self.previous_funnel.to_csv(self.file_path, index=False, encoding='cp1251')
