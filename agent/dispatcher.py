"""
Маршрутизация: имя инструмента → Python-функция.
Добавить новый инструмент: внести в TOOL_MAP + в agent/tools.py.
"""
from yandex.campaigns import (
    list_campaigns, create_campaign, create_master_campaign, update_campaign_budget
)
from yandex.adgroups import create_adgroup, batch_pause_adgroups
from yandex.ads import create_ad
from yandex.keywords import add_keywords, add_negative_keywords, get_keywords
from yandex.bids import set_keyword_bids
from yandex.exclusions import add_site_exclusions
from yandex.audiences import create_retargeting_campaign
from yandex.reports import get_campaign_stats, get_keyword_stats
from metrica.webvisor import get_webvisor_summary
from analysis.funnel import analyze_full_funnel
from analysis.site_advisor import get_site_recommendations
from analysis.feedback_processor import process_client_feedback
from web.storage import get_lead_stats, get_reports


def _get_last_report() -> dict | None:
    reports = get_reports(limit=1)
    return reports[0] if reports else None


TOOL_MAP: dict = {
    # Кампании
    "list_campaigns":           list_campaigns,
    "create_campaign":          create_campaign,
    "create_master_campaign":   create_master_campaign,
    "update_campaign_budget":   update_campaign_budget,
    # Группы
    "create_adgroup":           create_adgroup,
    "batch_pause_adgroups":     batch_pause_adgroups,
    # Объявления
    "create_ad":                create_ad,
    # Ключи
    "add_keywords":             add_keywords,
    "add_negative_keywords":    add_negative_keywords,
    "get_keywords":             get_keywords,
    # Ставки
    "set_keyword_bids":         set_keyword_bids,
    # Исключения / ретаргетинг
    "add_site_exclusions":      add_site_exclusions,
    "create_retargeting_campaign": create_retargeting_campaign,
    # Статистика
    "get_campaign_stats":       get_campaign_stats,
    "get_keyword_stats":        get_keyword_stats,
    # Аналитика
    "get_webvisor_insights":    lambda date_from, date_to: get_webvisor_summary(date_from, date_to),
    "analyze_full_funnel":      analyze_full_funnel,
    "get_site_recommendations": get_site_recommendations,
    # Лиды и фидбэк
    "get_lead_stats":           lambda: get_lead_stats(),
    "process_client_feedback":  lambda: process_client_feedback(),
    "get_last_report":          lambda: _get_last_report(),
}


def dispatch_tool(name: str, inputs: dict):
    if name not in TOOL_MAP:
        raise ValueError(f"Неизвестный инструмент: {name}")
    return TOOL_MAP[name](**inputs)
