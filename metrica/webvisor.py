from config import METRICA_COUNTER_ID
from .client import client


def get_bounce_rate_by_page(date_from: str, date_to: str) -> list[dict]:
    """Страницы с высоким процентом отказов."""
    data = client.get("stat/v1/data", {
        "id": METRICA_COUNTER_ID,
        "date1": date_from,
        "date2": date_to,
        "metrics": "ym:s:bounceRate,ym:s:visits",
        "dimensions": "ym:s:startURL",
        "sort": "-ym:s:bounceRate",
        "limit": 20,
    })
    result = []
    for row in data.get("data", []):
        dims = row.get("dimensions", [])
        metrics = row.get("metrics", [])
        if dims and metrics:
            result.append({
                "url": dims[0].get("name", ""),
                "bounce_rate": round(float(metrics[0]), 1),
                "visits": int(metrics[1]),
            })
    return result


def get_device_split(date_from: str, date_to: str) -> dict:
    """Соотношение устройств: desktop / mobile / tablet."""
    data = client.get("stat/v1/data", {
        "id": METRICA_COUNTER_ID,
        "date1": date_from,
        "date2": date_to,
        "metrics": "ym:s:visits,ym:s:goal{}reaches".format(
            __import__("config").METRICA_GOAL_ID
        ),
        "dimensions": "ym:s:deviceCategory",
    })
    result: dict[str, dict] = {}
    for row in data.get("data", []):
        dims = row.get("dimensions", [])
        metrics = row.get("metrics", [])
        if dims and metrics:
            device = dims[0].get("name", "unknown")
            result[device] = {
                "visits": int(metrics[0]),
                "conversions": int(float(metrics[1])) if len(metrics) > 1 else 0,
            }
    return result


def get_exit_pages(date_from: str, date_to: str) -> list[dict]:
    """Страницы, с которых чаще всего уходят."""
    data = client.get("stat/v1/data", {
        "id": METRICA_COUNTER_ID,
        "date1": date_from,
        "date2": date_to,
        "metrics": "ym:s:exits",
        "dimensions": "ym:s:exitURL",
        "sort": "-ym:s:exits",
        "limit": 10,
    })
    result = []
    for row in data.get("data", []):
        dims = row.get("dimensions", [])
        metrics = row.get("metrics", [])
        if dims and metrics:
            result.append({
                "url": dims[0].get("name", ""),
                "exits": int(metrics[0]),
            })
    return result


def get_traffic_sources(date_from: str, date_to: str) -> list[dict]:
    """Источники трафика с конверсиями."""
    goal_id = __import__("config").METRICA_GOAL_ID
    data = client.get("stat/v1/data", {
        "id": METRICA_COUNTER_ID,
        "date1": date_from,
        "date2": date_to,
        "metrics": f"ym:s:visits,ym:s:goal{goal_id}reaches,ym:s:bounceRate",
        "dimensions": "ym:s:trafficSource",
        "sort": "-ym:s:visits",
    })
    result = []
    for row in data.get("data", []):
        dims = row.get("dimensions", [])
        metrics = row.get("metrics", [])
        if dims and metrics:
            visits = int(metrics[0])
            convs = int(float(metrics[1])) if len(metrics) > 1 else 0
            result.append({
                "source": dims[0].get("name", ""),
                "visits": visits,
                "conversions": convs,
                "cr": round(convs / visits * 100, 2) if visits > 0 else 0,
                "bounce_rate": round(float(metrics[2]), 1) if len(metrics) > 2 else 0,
            })
    return result


def get_webvisor_summary(date_from: str, date_to: str) -> dict:
    """
    Сводные данные о поведении пользователей на сайте.
    Возвращает структурированные данные для анализа агентом.
    """
    bounce_pages = get_bounce_rate_by_page(date_from, date_to)
    devices = get_device_split(date_from, date_to)
    exit_pages = get_exit_pages(date_from, date_to)
    sources = get_traffic_sources(date_from, date_to)

    return {
        "period": f"{date_from} — {date_to}",
        "devices": devices,
        "high_bounce_pages": [p for p in bounce_pages if p["bounce_rate"] > 40],
        "top_exit_pages": exit_pages[:5],
        "traffic_sources": sources,
    }
