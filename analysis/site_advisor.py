"""
ИИ рекомендации по сайту на основе данных Вебвизора и лидов.
Claude анализирует поведение пользователей и формулирует конкретные советы.
"""
import anthropic
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from metrica.webvisor import get_webvisor_summary
from web.storage import get_lead_stats, get_feedback

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def get_site_recommendations(
    date_from: str,
    date_to: str,
    extra_context: str = "",
) -> str:
    """
    Анализирует данные Вебвизора и лиды, возвращает рекомендации по сайту.
    """
    webvisor = get_webvisor_summary(date_from, date_to)
    lead_stats = get_lead_stats()
    feedback = get_feedback(limit=10)

    # Форматируем данные для Claude
    data_summary = _format_data(webvisor, lead_stats, feedback, extra_context)

    response = _client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": f"""Ты опытный UX-аналитик и маркетолог. Проанализируй данные о поведении пользователей на сайте и дай конкретные, приоритизированные рекомендации.

{data_summary}

Дай рекомендации в формате:

РЕКОМЕНДАЦИИ ПО САЙТУ:

Мобильные устройства:
- [рекомендация с обоснованием]

Десктоп:
- [рекомендация с обоснованием]

Контент и доверие:
- [рекомендация с обоснованием]

Форма и конверсия:
- [рекомендация с обоснованием]

ПРИОРИТЕТ #1 (сделать в первую очередь):
- [самое важное действие]

Будь конкретным. Указывай на реальные данные. Не пиши общих слов."""
        }],
    )
    return response.content[0].text


def _format_data(webvisor: dict, lead_stats: dict, feedback: list, extra: str) -> str:
    lines = [f"ПЕРИОД: {webvisor.get('period', '—')}", ""]

    # Устройства
    devices = webvisor.get("devices", {})
    if devices:
        lines.append("УСТРОЙСТВА:")
        for device, data in devices.items():
            lines.append(f"  {device}: {data.get('visits', 0)} визитов, {data.get('conversions', 0)} конверсий")
        lines.append("")

    # Страницы с высоким отказом
    bounce_pages = webvisor.get("high_bounce_pages", [])
    if bounce_pages:
        lines.append("СТРАНИЦЫ С ВЫСОКИМ ОТКАЗОМ (>40%):")
        for p in bounce_pages:
            lines.append(f"  {p['url']}: {p['bounce_rate']}% отказов, {p['visits']} визитов")
        lines.append("")

    # Страницы выхода
    exit_pages = webvisor.get("top_exit_pages", [])
    if exit_pages:
        lines.append("СТРАНИЦЫ ВЫХОДА:")
        for p in exit_pages:
            lines.append(f"  {p['url']}: {p['exits']} выходов")
        lines.append("")

    # Качество лидов
    lines.append(f"КАЧЕСТВО ЛИДОВ:")
    lines.append(f"  Всего: {lead_stats.get('total', 0)}")
    lines.append(f"  Целевых: {lead_stats.get('qualified', 0)} ({lead_stats.get('qualified_pct', 0)}%)")
    by_source = lead_stats.get("by_source", [])
    for s in by_source:
        pct = round(s.get("qual", 0) / s.get("cnt", 1) * 100, 1) if s.get("cnt") else 0
        lines.append(f"  {s['source']}: {s['cnt']} лидов, {pct}% целевых")
    lines.append("")

    # Обратная связь клиента
    if feedback:
        lines.append("КОММЕНТАРИИ КЛИЕНТА:")
        for f in feedback[:5]:
            lines.append(f"  — {f['message']}")
        lines.append("")

    if extra:
        lines.append(f"ДОПОЛНИТЕЛЬНЫЙ КОНТЕКСТ:\n{extra}\n")

    return "\n".join(lines)
