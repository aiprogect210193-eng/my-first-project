"""
Полный анализ маркетинговой воронки:
Директ (трафик/CTR) → Метрика (поведение) → Лиды (качество)
"""
from yandex.reports import get_campaign_stats
from metrica.webvisor import get_webvisor_summary
from metrica.conversions import get_conversions, get_conversion_rate
from web.storage import get_lead_stats


def analyze_full_funnel(
    campaign_ids: list[int],
    date_from: str,
    date_to: str,
) -> dict:
    """
    Собирает полную картину воронки из всех источников данных.
    Возвращает структурированный словарь для анализа агентом.
    """
    # 1. Данные из Яндекс Директ
    campaign_stats = get_campaign_stats(campaign_ids, date_from, date_to)
    total_clicks = sum(c.get("Clicks", 0) for c in campaign_stats)
    total_cost = sum(c.get("Cost", 0.0) for c in campaign_stats)

    # 2. Данные из Метрики
    webvisor = get_webvisor_summary(date_from, date_to)
    conversions = get_conversions(date_from, date_to)
    cr = get_conversion_rate(date_from, date_to)

    # 3. Данные о лидах от клиента
    lead_stats = get_lead_stats()

    # 4. Вычисляем ключевые метрики
    cpl = round(total_cost / conversions, 2) if conversions > 0 else None
    cost_per_click = round(total_cost / total_clicks, 2) if total_clicks > 0 else None

    # 5. Находим узкие места
    bottlenecks = _find_bottlenecks(
        cr=cr,
        lead_stats=lead_stats,
        webvisor=webvisor,
        campaign_stats=campaign_stats,
    )

    return {
        "period": f"{date_from} — {date_to}",
        "advertising": {
            "total_clicks": total_clicks,
            "total_cost_rub": total_cost,
            "cost_per_click": cost_per_click,
            "campaigns": campaign_stats,
        },
        "site": {
            "conversions": conversions,
            "conversion_rate_pct": cr,
            "cpl_rub": cpl,
            "webvisor": webvisor,
        },
        "leads": lead_stats,
        "bottlenecks": bottlenecks,
    }


def _find_bottlenecks(
    cr: float,
    lead_stats: dict,
    webvisor: dict,
    campaign_stats: list[dict],
) -> list[str]:
    """Определяет узкие места в воронке."""
    issues = []

    if cr < 1.0:
        issues.append(
            f"Конверсия сайта низкая ({cr:.2f}%) — трафик есть, но пользователи не оставляют заявки. "
            "Проблема на стороне сайта (форма, контент, UX)."
        )

    high_bounce = webvisor.get("high_bounce_pages", [])
    if high_bounce:
        worst = max(high_bounce, key=lambda p: p["bounce_rate"])
        issues.append(
            f"Высокий отказ на странице {worst['url']} ({worst['bounce_rate']}%) — "
            "пользователи не находят нужную информацию."
        )

    devices = webvisor.get("devices", {})
    mobile_visits = devices.get("mobile", {}).get("visits", 0)
    desktop_visits = devices.get("desktop", {}).get("visits", 0)
    total_visits = mobile_visits + desktop_visits
    if total_visits > 0 and mobile_visits / total_visits > 0.55:
        mobile_cr = devices.get("mobile", {}).get("conversions", 0) / mobile_visits * 100 if mobile_visits else 0
        desktop_cr = devices.get("desktop", {}).get("conversions", 0) / desktop_visits * 100 if desktop_visits else 0
        if desktop_cr > 0 and mobile_cr < desktop_cr * 0.5:
            issues.append(
                f"Мобильные пользователи ({mobile_visits} визитов, {mobile_cr:.1f}% CR) конвертируются "
                f"хуже десктопа ({desktop_cr:.1f}% CR). Проверьте мобильную версию сайта и форму."
            )

    qualified_pct = lead_stats.get("qualified_pct", 100)
    if qualified_pct < 50:
        issues.append(
            f"Только {qualified_pct}% лидов целевые — вероятно, реклама привлекает нерелевантную аудиторию. "
            "Нужна корректировка ключевых слов и таргетинга."
        )

    for camp in campaign_stats:
        if camp.get("Ctr", 0) < 1.0 and camp.get("Clicks", 0) > 100:
            issues.append(
                f"Кампания «{camp.get('CampaignName', camp.get('CampaignId'))}» — "
                f"CTR {camp.get('Ctr', 0):.2f}%, объявления нерелевантны запросам."
            )

    return issues
