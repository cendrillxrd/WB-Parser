def get_analytics_report_status(reports: dict) -> str:
    """Возвращает статус готовности отчета"""
    return reports['data'][0]['status']
