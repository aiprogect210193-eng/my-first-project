import time
import requests
from config import YANDEX_TOKEN, YANDEX_LOGIN

REPORTS_URL = "https://api.direct.yandex.com/json/v5/reports"

_HEADERS = {
    "Authorization": f"Bearer {YANDEX_TOKEN}",
    "Client-Login": YANDEX_LOGIN,
    "Accept-Language": "ru",
    "Content-Type": "application/json; charset=utf-8",
    "returnMoneyInMicros": "false",
    "skipReportHeader": "true",
    "skipColumnHeader": "false",
    "skipReportSummary": "true",
}


def _request_report(body: dict, max_wait: int = 60) -> list[dict]:
    """
    Отправляет запрос отчёта и ждёт результата (async polling).
    Возвращает список строк как список словарей.
    """
    resp = requests.post(REPORTS_URL, json=body, headers=_HEADERS, timeout=30)

    waited = 0
    while resp.status_code == 202 and waited < max_wait:
        retry_after = int(resp.headers.get("retryIn", "5"))
        time.sleep(retry_after)
        waited += retry_after
        resp = requests.post(REPORTS_URL, json=body, headers=_HEADERS, timeout=30)

    resp.raise_for_status()

    lines = resp.text.strip().split("\n")
    if not lines:
        return []

    headers = lines[0].split("\t")
    result = []
    for line in lines[1:]:
        if not line.strip():
            continue
        values = line.split("\t")
        result.append(dict(zip(headers, values)))
    return result


def get_campaign_stats(
    campaign_ids: list[int],
    date_from: str,
    date_to: str,
) -> list[dict]:
    """
    Статистика по кампаниям: клики, показы, CTR, расход.
    date_from / date_to: 'YYYY-MM-DD'
    """
    body = {
        "params": {
            "SelectionCriteria": {
                "DateFrom": date_from,
                "DateTo": date_to,
                "Filter": [{"Field": "CampaignId", "Operator": "IN", "Values": [str(i) for i in campaign_ids]}],
            },
            "FieldNames": ["CampaignId", "CampaignName", "Clicks", "Impressions", "Ctr", "Cost"],
            "ReportName": f"campaign_stats_{date_from}_{date_to}",
            "ReportType": "CAMPAIGN_PERFORMANCE_REPORT",
            "DateRangeType": "CUSTOM_DATE",
            "Format": "TSV",
            "IncludeVAT": "NO",
            "IncludeDiscount": "NO",
        }
    }
    rows = _request_report(body)
    # Конвертируем числа
    for row in rows:
        for field in ("Clicks", "Impressions"):
            if field in row:
                row[field] = int(row[field]) if row[field] != "--" else 0
        for field in ("Ctr", "Cost"):
            if field in row:
                try:
                    row[field] = float(row[field])
                except ValueError:
                    row[field] = 0.0
    return rows


def get_keyword_stats(
    campaign_id: int,
    date_from: str,
    date_to: str,
) -> list[dict]:
    """Статистика по ключевым словам кампании."""
    body = {
        "params": {
            "SelectionCriteria": {
                "DateFrom": date_from,
                "DateTo": date_to,
                "Filter": [{"Field": "CampaignId", "Operator": "EQUALS", "Values": [str(campaign_id)]}],
            },
            "FieldNames": [
                "Keyword", "AdGroupId", "Clicks", "Impressions",
                "Ctr", "Cost", "AvgCpc", "BounceRate",
            ],
            "ReportName": f"keyword_stats_{campaign_id}_{date_from}",
            "ReportType": "SEARCH_QUERY_PERFORMANCE_REPORT",
            "DateRangeType": "CUSTOM_DATE",
            "Format": "TSV",
            "IncludeVAT": "NO",
            "IncludeDiscount": "NO",
        }
    }
    rows = _request_report(body)
    for row in rows:
        for field in ("Clicks", "Impressions"):
            if field in row:
                row[field] = int(row[field]) if row[field] != "--" else 0
        for field in ("Ctr", "Cost", "AvgCpc", "BounceRate"):
            if field in row:
                try:
                    row[field] = float(row[field])
                except ValueError:
                    row[field] = 0.0
    return rows
