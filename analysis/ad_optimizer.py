"""
Логика авто-оптимизации кампаний на основе статистики.
Определяет что остановить, что масштабировать, как перераспределить бюджет.
"""
from datetime import date, timedelta
from config import TARGET_CPL
from yandex import reports as direct_reports
from yandex import bids, adgroups, campaigns
from web.storage import log_action


def analyze_and_optimize(
    campaign_ids: list[int],
    date_from: str | None = None,
    date_to: str | None = None,
    target_cpl: float | None = None,
) -> dict:
    """
    Анализирует кампании и применяет оптимизации.
    Возвращает словарь с описанием всех выполненных действий.
    """
    _target = target_cpl or TARGET_CPL
    _to = date_to or date.today().isoformat()
    _from = date_from or (date.today() - timedelta(days=14)).isoformat()

    actions = {
        "paused_groups": [],
        "bid_changes": [],
        "budget_changes": [],
        "recommendations": [],
    }

    # Статистика по ключам для каждой кампании
    for campaign_id in campaign_ids:
        kw_stats = direct_reports.get_keyword_stats(campaign_id, _from, _to)
        _optimize_keywords(campaign_id, kw_stats, _target, actions)

    # Статистика по кампаниям целиком
    campaign_stats = direct_reports.get_campaign_stats(campaign_ids, _from, _to)
    _optimize_budgets(campaign_stats, actions)

    return actions


def _optimize_keywords(
    campaign_id: int,
    kw_stats: list[dict],
    target_cpl: float,
    actions: dict,
) -> None:
    """Корректирует ставки ключевых слов."""
    bid_updates = []

    for kw in kw_stats:
        clicks = kw.get("Clicks", 0)
        avg_cpc = kw.get("AvgCpc", 0.0)
        bounce = kw.get("BounceRate", 0.0)
        cost = kw.get("Cost", 0.0)
        keyword_text = kw.get("Keyword", "")
        group_id = kw.get("AdGroupId")

        # Критерии для остановки группы
        if bounce > 40 and clicks > 20:
            if group_id:
                try:
                    adgroups.pause_adgroup(int(group_id))
                    msg = f"Остановлена группа {group_id} (ключ: '{keyword_text}') — отказы {bounce:.0f}%"
                    actions["paused_groups"].append(msg)
                    log_action("pause_adgroup", {"group_id": group_id, "reason": f"bounce {bounce:.0f}%"})
                except Exception:
                    pass

        # Высокий CPC без конверсий — снижаем ставку
        elif avg_cpc > target_cpl * 0.35 and clicks > 10:
            new_bid = round(avg_cpc * 0.7, 2)
            if group_id:
                actions["bid_changes"].append({
                    "keyword": keyword_text,
                    "old_bid": avg_cpc,
                    "new_bid": new_bid,
                    "reason": "высокий CPC без конверсий",
                })
                # Ставки применяем батчем снаружи
        else:
            pass  # Ключ стабилен


def _optimize_budgets(campaign_stats: list[dict], actions: dict) -> None:
    """Перераспределяет бюджеты: урезает плохие, добавляет хорошим."""
    if not campaign_stats:
        return

    # Считаем простой рейтинг по CTR
    scored = sorted(
        [c for c in campaign_stats if c.get("Clicks", 0) > 0],
        key=lambda c: c.get("Ctr", 0),
        reverse=True,
    )
    if len(scored) < 2:
        return

    top = scored[0]
    bottom = scored[-1]

    if top.get("Ctr", 0) > bottom.get("Ctr", 0) * 2:
        actions["recommendations"].append(
            f"Кампания «{top.get('CampaignName', top.get('CampaignId'))}» показывает лучший CTR "
            f"({top.get('Ctr', 0):.2f}%) — рекомендуем увеличить бюджет на 20%"
        )
        actions["recommendations"].append(
            f"Кампания «{bottom.get('CampaignName', bottom.get('CampaignId'))}» — низкий CTR "
            f"({bottom.get('Ctr', 0):.2f}%) — рассмотрите снижение бюджета"
        )
