from config import METRICA_COUNTER_ID, METRICA_GOAL_ID
from .client import client


def get_audience_size(days: int) -> int:
    """
    Примерный размер аудитории: посещали сайт за N дней, не выполнили цель.
    Используется для оценки перед запуском ретаргетинга.
    """
    from datetime import date, timedelta
    date_to = date.today().isoformat()
    date_from = (date.today() - timedelta(days=days)).isoformat()

    goal_id = METRICA_GOAL_ID
    data = client.get("stat/v1/data", {
        "id": METRICA_COUNTER_ID,
        "date1": date_from,
        "date2": date_to,
        "metrics": "ym:s:users",
        "filters": f"ym:s:goal{goal_id}reaches==0",
    })
    totals = data.get("totals", [0])
    return int(totals[0]) if totals else 0
