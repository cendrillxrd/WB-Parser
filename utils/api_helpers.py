def get_analytics_report_status(reports: dict) -> str:
    """Возвращает статус готовности отчета."""
    return reports['data'][0]['status']


def update_params_for_pagination(response: dict, limit: int):
    """Обновляет параметры для пагинации."""
    updated_at, nm_id, total = response['cursor'].values()
    payload = {
        'settings': {
            'cursor': {
                'limit': limit,
                'updatedAt': updated_at,
                'nmID': nm_id
            },
            'filter': {
                'withPhoto': -1
            }
        }
    }
    return payload, total
