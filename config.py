from typing import TypedDict
from dotenv import load_dotenv
import os

load_dotenv()


class ApiKeys(TypedDict):
    Analytics_Statistics_API_KEY: str
    Content_Marketplace_API_KEY: str


API_KEYS = {
    'Analytics_Statistics_API_KEY': os.getenv('ANALYTICS_STATISTICS_API_KEY'),
    'Content_Marketplace_API_KEY': os.getenv('CONTENT_MARKETPLACE_API_KEY')
}

BASE_URLS = {
    'suppliers': 'https://suppliers-api.wildberries.ru',
    'content': 'https://content-api.wildberries.ru',
    'seller-analytics': 'https://seller-analytics-api.wildberries.ru',
    'statistics': 'https://statistics-api.wildberries.ru',
    'marketplace': 'https://marketplace-api.wildberries.ru',
    'dp-calendar': 'https://dp-calendar-api.wildberries.ru'
}
