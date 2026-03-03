"""
Генерация еженедельного отчёта в формате клиента.
Claude формирует полный текст на основе всех собранных данных.
"""
import anthropic
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from web.storage import save_report

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def generate_report(
    date_from: str,
    date_to: str,
    funnel_data: dict,
    optimization_actions: dict,
    site_recommendations: str,
    project_name: str = "Проект",
    datalens_url: str = "",
) -> str:
    """
    Генерирует полный отчёт за период. Сохраняет в БД. Возвращает текст.
    """
    prompt = _build_prompt(
        date_from, date_to, funnel_data, optimization_actions,
        site_recommendations, project_name, datalens_url,
    )

    response = _client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}],
    )
    report_text = response.content[0].text

    save_report(
        title=f"Отчёт | {project_name} | {date_from} — {date_to}",
        content=report_text,
        period_from=date_from,
        period_to=date_to,
    )
    return report_text


def _build_prompt(
    date_from: str,
    date_to: str,
    funnel: dict,
    actions: dict,
    site_recs: str,
    project_name: str,
    datalens_url: str,
) -> str:
    adv = funnel.get("advertising", {})
    site = funnel.get("site", {})
    leads = funnel.get("leads", {})
    bottlenecks = funnel.get("bottlenecks", [])

    paused = actions.get("paused_groups", [])
    bid_changes = actions.get("bid_changes", [])
    recommendations = actions.get("recommendations", [])

    lines = [
        "Ты опытный маркетолог. Составь подробный еженедельный отчёт для клиента.",
        "Используй профессиональный но понятный язык. Будь конкретным — называй цифры и факты.",
        "",
        f"ПЕРИОД: {date_from} — {date_to}",
        f"ПРОЕКТ: {project_name}",
    ]
    if datalens_url:
        lines.append(f"ДАШБОРД: {datalens_url}")
    lines.append("")

    lines.extend([
        "ДАННЫЕ О РЕКЛАМЕ:",
        f"  Клики: {adv.get('total_clicks', 0)}",
        f"  Расход: {adv.get('total_cost_rub', 0):.0f} руб",
        f"  CPC: {adv.get('cost_per_click', 0):.2f} руб",
        "",
        "ДАННЫЕ О КОНВЕРСИЯХ:",
        f"  Конверсии (цели Метрики): {site.get('conversions', 0)}",
        f"  CR сайта: {site.get('conversion_rate_pct', 0):.2f}%",
        f"  CPL: {site.get('cpl_rub') or '—'} руб",
        "",
        "ДАННЫЕ О ЛИДАХ (от клиента):",
        f"  Всего лидов: {leads.get('total', 0)}",
        f"  Целевых: {leads.get('qualified', 0)} ({leads.get('qualified_pct', 0)}%)",
        "",
    ])

    if paused:
        lines.append("ОСТАНОВЛЕННЫЕ ГРУППЫ:")
        for g in paused:
            lines.append(f"  - {g}")
        lines.append("")

    if bid_changes:
        lines.append("ИЗМЕНЕНИЯ СТАВОК:")
        for b in bid_changes:
            lines.append(f"  - «{b['keyword']}»: {b['old_bid']:.2f} → {b['new_bid']:.2f} руб ({b['reason']})")
        lines.append("")

    if bottlenecks:
        lines.append("УЗКИЕ МЕСТА ВОРОНКИ:")
        for b in bottlenecks:
            lines.append(f"  - {b}")
        lines.append("")

    if recommendations:
        lines.append("РЕКОМЕНДАЦИИ ПО БЮДЖЕТАМ:")
        for r in recommendations:
            lines.append(f"  - {r}")
        lines.append("")

    if site_recs:
        lines.extend(["РЕКОМЕНДАЦИИ ПО САЙТУ:", site_recs, ""])

    lines.extend([
        "Составь отчёт в формате:",
        "",
        "═══════════════════════════════════════════════",
        "ОТЧЁТ | [Проект] | [период]",
        "[если есть — ссылка на дашборд]",
        "═══════════════════════════════════════════════",
        "",
        "ВЫПОЛНЕННЫЕ РАБОТЫ:",
        "- [что сделано и зачем]",
        "",
        "ОСТАНОВЛЕННЫЕ ГРУППЫ:",
        "- [название группы — причина]",
        "",
        "РЕЗУЛЬТАТЫ:",
        "- CPL: X руб (динамика)",
        "- Лиды: X | Целевых: X (X%)",
        "- Расход: X руб",
        "",
        "АНАЛИЗ СЕССИЙ ПОЛЬЗОВАТЕЛЕЙ:",
        "[наблюдения по ПК и мобильным]",
        "",
        "РЕКОМЕНДАЦИИ ПО САЙТУ:",
        "- [конкретная рекомендация с обоснованием]",
        "",
        "ПЛАН ДАЛЬНЕЙШЕЙ РАБОТЫ:",
        "- [следующие шаги]",
        "═══════════════════════════════════════════════",
    ])

    return "\n".join(lines)
