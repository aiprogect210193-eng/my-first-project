"""
Обработка обратной связи клиента о качестве лидов.
Claude анализирует данные и генерирует конкретный план действий.
"""
import anthropic
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from web.storage import get_lead_stats, get_feedback

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def process_client_feedback() -> str:
    """
    Анализирует всю обратную связь клиента + статистику лидов.
    Возвращает план действий: что нужно изменить в рекламе и на сайте.
    """
    lead_stats = get_lead_stats()
    feedback = get_feedback(limit=20)

    if not lead_stats.get("total") and not feedback:
        return "Нет данных о лидах или обратной связи клиента для анализа."

    prompt = _build_prompt(lead_stats, feedback)

    response = _client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def _build_prompt(lead_stats: dict, feedback: list) -> str:
    lines = [
        "Ты опытный маркетолог-аналитик. Клиент предоставил данные о качестве лидов и свои комментарии.",
        "Проанализируй данные и дай КОНКРЕТНЫЙ план действий для оптимизации рекламы и сайта.",
        "",
        "ДАННЫЕ О ЛИДАХ:",
        f"  Всего лидов: {lead_stats.get('total', 0)}",
        f"  Целевых: {lead_stats.get('qualified', 0)} ({lead_stats.get('qualified_pct', 0)}%)",
        f"  Нецелевых: {lead_stats.get('not_qualified', 0)}",
        "",
    ]

    by_source = lead_stats.get("by_source", [])
    if by_source:
        lines.append("По источникам:")
        for s in by_source:
            pct = round(s.get("qual", 0) / s.get("cnt", 1) * 100, 1) if s.get("cnt") else 0
            lines.append(f"  {s['source']}: {s['cnt']} лидов, {pct}% целевых")
        lines.append("")

    reasons = lead_stats.get("rejection_reasons", [])
    if reasons:
        lines.append("Причины отказов:")
        for r in reasons:
            lines.append(f"  {r['rejection_reason']}: {r['cnt']} раз")
        lines.append("")

    if feedback:
        lines.append("КОММЕНТАРИИ КЛИЕНТА:")
        for f in feedback:
            lines.append(f"  [{f['created_at']}] {f['message']}")
        lines.append("")

    lines.extend([
        "На основе этих данных дай ответ в формате:",
        "",
        "АНАЛИЗ СИТУАЦИИ:",
        "- [что происходит]",
        "",
        "ДЕЙСТВИЯ В РЕКЛАМЕ (выполняю я — агент):",
        "- [конкретное действие с обоснованием]",
        "",
        "РЕКОМЕНДАЦИИ ДЛЯ КЛИЕНТА (сайт / процесс):",
        "- [конкретный совет]",
        "",
        "ЕСЛИ ВСЁ ХОРОШО — план масштабирования:",
        "- [как безопасно увеличить объём]",
    ])

    return "\n".join(lines)
