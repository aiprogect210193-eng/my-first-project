"""
Планировщик задач: ежедневная проверка + еженедельный полный цикл.
Запускается отдельно от веб-сервера: python automation/scheduler.py
"""
import logging
import os
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

scheduler = BlockingScheduler(timezone="Europe/Moscow")

PROJECT_NAME = os.getenv("PROJECT_NAME", "Проект")
DATALENS_URL = os.getenv("DATALENS_URL", "")


def _daily():
    from automation.weekly_cycle import run_daily_check
    logger.info("Запуск ежедневной проверки")
    run_daily_check()


def _weekly():
    from automation.weekly_cycle import run_weekly_cycle
    logger.info("Запуск еженедельного цикла")
    report = run_weekly_cycle(project_name=PROJECT_NAME, datalens_url=DATALENS_URL)
    logger.info(f"Отчёт сформирован ({len(report)} символов)")


# Ежедневно в 08:00 МСК
scheduler.add_job(_daily, CronTrigger(hour=8, minute=0), id="daily_check")

# Каждый понедельник в 08:30 МСК
scheduler.add_job(_weekly, CronTrigger(day_of_week="mon", hour=8, minute=30), id="weekly_cycle")


if __name__ == "__main__":
    logger.info("Планировщик запущен. Ежедневная проверка: 08:00, Еженедельный цикл: понедельник 08:30 (МСК)")
    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Планировщик остановлен")
