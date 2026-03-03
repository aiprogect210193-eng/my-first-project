from config import METRICA_COUNTER_ID, METRICA_GOAL_ID
from .client import client


def get_conversions(date_from: str, date_to: str, goal_id: int | None = None) -> int:
    """Количество конверсий за период."""
    gid = goal_id or int(METRICA_GOAL_ID)
    data = client.get("stat/v1/data", {
        "id": METRICA_COUNTER_ID,
        "date1": date_from,
        "date2": date_to,
        "metrics": f"ym:s:goal{gid}reaches",
        "dimensions": "",
    })
    totals = data.get("totals", [0])
    return int(totals[0]) if totals else 0


def get_cpl_by_campaign(
    campaign_ids: list[int],
    date_from: str,
    date_to: str,
) -> dict[int, float]:
    """
    CPL (стоимость лида) по каждой кампании.
    Возвращает {campaign_id: cpl_in_rubles}.
    Данные о расходах берём из метрики через UTM/click ID разбивку.
    """
    goal_id = int(METRICA_GOAL_ID)
    data = client.get("stat/v1/data", {
        "id": METRICA_COUNTER_ID,
        "date1": date_from,
        "date2": date_to,
        "metrics": f"ym:s:goal{goal_id}reaches,ym:s:goal{goal_id}conversionRate",
        "dimensions": "ym:s:DirectClickOrder",
        "filters": f"ym:s:DirectClickOrder=={'||'.join(str(i) for i in campaign_ids)}",
    })

    result: dict[int, float] = {}
    rows = data.get("data", [])
    for row in rows:
        dims = row.get("dimensions", [])
        metrics = row.get("metrics", [])
        if not dims or not metrics:
            continue
        try:
            cid = int(dims[0].get("id", 0))
            conversions = float(metrics[0]) if metrics[0] else 0
            # CPL требует данных о расходах — здесь заглушка, реальные данные из yandex/reports
            result[cid] = conversions
        except (ValueError, IndexError):
            continue
    return result


def get_conversion_rate(date_from: str, date_to: str) -> float:
    """Общий CR сайта за период (%)."""
    goal_id = int(METRICA_GOAL_ID)
    data = client.get("stat/v1/data", {
        "id": METRICA_COUNTER_ID,
        "date1": date_from,
        "date2": date_to,
        "metrics": f"ym:s:goal{goal_id}conversionRate",
    })
    totals = data.get("totals", [0])
    return float(totals[0]) if totals else 0.0
