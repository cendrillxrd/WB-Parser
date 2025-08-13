import os

from dotenv import load_dotenv

load_dotenv()

API_KEYS = {
    'Analytics_Statistics_API_KEY': os.getenv('ANALYTICS_STATISTICS_API_KEY'),
    'Content_Marketplace_API_KEY': os.getenv('CONTENT_MARKETPLACE_API_KEY'),
    'API_PAPA': os.getenv('API_PAPA')
}

BASE_URLS = {
    'suppliers': 'https://suppliers-api.wildberries.ru',
    'content': 'https://content-api.wildberries.ru',
    'seller-analytics': 'https://seller-analytics-api.wildberries.ru',
    'statistics': 'https://statistics-api.wildberries.ru',
    'marketplace': 'https://marketplace-api.wildberries.ru',
    'dp-calendar': 'https://dp-calendar-api.wildberries.ru',
    'discounts-prices': 'https://discounts-prices-api.wildberries.ru'
}

FILE_PATH = 'C:/Users/Admin/Desktop/'
