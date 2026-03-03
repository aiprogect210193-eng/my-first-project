"""
Полный еженедельный цикл оптимизации:
1. Получить статистику за 7 дней
2. Оптимизировать кампании (ставки, паузы, бюджеты)
3. Проанализировать воронку и сайт
4. Сформировать отчёт
"""
import logging
from datetime import date, timedelta
from yandex.campaigns import list_campaigns
from analysis.ad_optimizer import analyze_and_optimize
from analysis.funnel import analyze_full_funnel
from analysis.site_advisor import get_site_recommendations
from automation.reporter import generate_report
from web.storage import log_action

logger = logging.getLogger(__name__)


def run_weekly_cycle(
    project_name: str = "Проект",
    datalens_url: str = "",
) -> str:
    """
    Запускает полный недельный цикл. Возвращает текст отчёта.
    """
    date_to = date.today().isoformat()
    date_from = (date.today() - timedelta(days=7)).isoformat()

    logger.info(f"Запуск недельного цикла: {date_from} — {date_to}")

    # 1. Получить список активных кампаний
    try:
        all_campaigns = list_campaigns(states=["ON"])
        campaign_ids = [c["Id"] for c in all_campaigns]
    except Exception as e:
        logger.error(f"Ошибка получения кампаний: {e}")
        campaign_ids = []

    if not campaign_ids:
        logger.warning("Нет активных кампаний для оптимизации")
        log_action("weekly_cycle", {"status": "no_campaigns"})
        return "Нет активных кампаний."

    # 2. Оптимизация кампаний
    opt_actions = {}
    try:
        opt_actions = analyze_and_optimize(campaign_ids, date_from, date_to)
        log_action("optimization_complete", {
            "paused": len(opt_actions.get("paused_groups", [])),
            "bid_changes": len(opt_actions.get("bid_changes", [])),
        })
    except Exception as e:
        logger.error(f"Ошибка оптимизации: {e}")
        opt_actions = {"paused_groups": [], "bid_changes": [], "recommendations": []}

    # 3. Анализ воронки
    funnel_data = {}
    try:
        funnel_data = analyze_full_funnel(campaign_ids, date_from, date_to)
    except Exception as e:
        logger.error(f"Ошибка анализа воронки: {e}")

    # 4. Рекомендации по сайту
    site_recs = ""
    try:
        site_recs = get_site_recommendations(date_from, date_to)
    except Exception as e:
        logger.error(f"Ошибка рекомендаций по сайту: {e}")

    # 5. Формируем отчёт
    report_text = generate_report(
        date_from=date_from,
        date_to=date_to,
        funnel_data=funnel_data,
        optimization_actions=opt_actions,
        site_recommendations=site_recs,
        project_name=project_name,
        datalens_url=datalens_url,
    )

    log_action("report_generated", {"period": f"{date_from}—{date_to}"})
    logger.info("Недельный цикл завершён")
    return report_text


def run_daily_check(campaign_ids: list[int] | None = None) -> None:
    """
    Ежедневная быстрая проверка: только критические показатели.
    Не генерирует отчёт.
    """
    date_to = date.today().isoformat()
    date_from = (date.today() - timedelta(days=1)).isoformat()

    if campaign_ids is None:
        try:
            all_campaigns = list_campaigns(states=["ON"])
            campaign_ids = [c["Id"] for c in all_campaigns]
        except Exception:
            return

    if not campaign_ids:
        return

    try:
        # Только быстрая оптимизация ставок, без отчёта
        analyze_and_optimize(campaign_ids, date_from, date_to)
        log_action("daily_check", {"campaigns": len(campaign_ids)})
    except Exception as e:
        logger.error(f"Ошибка ежедневной проверки: {e}")
