from datetime import datetime, timedelta


def get_today_date() -> str:
    """Возвращает текущую дату в формате 'YYYY-MM-DD'."""
    return datetime.now().strftime('%Y-%m-%d')


def get_yesterday_date() -> str:
    """Возвращает вчерашнюю дату в формате 'YYYY-MM-DD'."""
    return (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')


def get_last_two_months() -> tuple[str, str, str, str]:
    """Возвращает даты для сравнения текущего и прошлого месяца в формате 'YYYY-MM-DD'."""
    current_end = datetime.now()
    current_start = current_end - timedelta(days=30)
    past_end = current_start - timedelta(days=1)
    past_start = current_start - timedelta(days=30)
    return (
        current_start.strftime('%Y-%m-%d'),
        current_end.strftime('%Y-%m-%d'),
        past_end.strftime('%Y-%m-%d'),
        past_start.strftime('%Y-%m-%d')
    )


def get_week_number() -> int:
    return datetime.now().isocalendar()[1]
