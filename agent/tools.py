"""
Схемы инструментов для Claude API.
Это чистый список данных — логика в dispatcher.py.
"""

TOOL_DEFINITIONS = [
    # ── Кампании ──────────────────────────────────────────────────────────────
    {
        "name": "list_campaigns",
        "description": "Получить список рекламных кампаний из Яндекс Директ с их статусами и бюджетами.",
        "input_schema": {
            "type": "object",
            "properties": {
                "states": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["ON", "OFF", "SUSPENDED", "ENDED", "ARCHIVED"]},
                    "description": "Фильтр по состоянию. Пропустить — получить все кампании.",
                }
            },
        },
    },
    {
        "name": "create_campaign",
        "description": "Создать новую текстовую рекламную кампанию в Яндекс Директ.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name":         {"type": "string", "description": "Название кампании"},
                "daily_budget": {"type": "number", "description": "Дневной бюджет в рублях"},
                "start_date":   {"type": "string", "description": "Дата старта в формате YYYY-MM-DD"},
            },
            "required": ["name", "daily_budget", "start_date"],
        },
    },
    {
        "name": "create_master_campaign",
        "description": "Создать мастер-кампанию (SmartCampaign) — Яндекс сам управляет таргетингом.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name":         {"type": "string"},
                "daily_budget": {"type": "number", "description": "Дневной бюджет в рублях"},
                "start_date":   {"type": "string", "description": "YYYY-MM-DD"},
                "region_ids":   {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "ID регионов Яндекса. Москва=1, СПб=2, Россия=225.",
                },
            },
            "required": ["name", "daily_budget", "start_date"],
        },
    },
    {
        "name": "update_campaign_budget",
        "description": "Изменить дневной бюджет кампании.",
        "input_schema": {
            "type": "object",
            "properties": {
                "campaign_id":  {"type": "integer"},
                "daily_budget": {"type": "number", "description": "Новый бюджет в рублях"},
            },
            "required": ["campaign_id", "daily_budget"],
        },
    },
    # ── Группы объявлений ─────────────────────────────────────────────────────
    {
        "name": "create_adgroup",
        "description": "Создать группу объявлений внутри кампании.",
        "input_schema": {
            "type": "object",
            "properties": {
                "campaign_id": {"type": "integer"},
                "name":        {"type": "string"},
                "region_ids":  {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "ID регионов. По умолчанию вся Россия (225).",
                },
            },
            "required": ["campaign_id", "name"],
        },
    },
    {
        "name": "batch_pause_adgroups",
        "description": "Остановить несколько групп объявлений за один вызов.",
        "input_schema": {
            "type": "object",
            "properties": {
                "group_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Список Id групп для остановки.",
                }
            },
            "required": ["group_ids"],
        },
    },
    # ── Объявления ────────────────────────────────────────────────────────────
    {
        "name": "create_ad",
        "description": "Создать текстовое объявление в группе.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ad_group_id": {"type": "integer"},
                "title":       {"type": "string", "description": "Заголовок 1, до 35 символов"},
                "title2":      {"type": "string", "description": "Заголовок 2, до 30 символов (необязательно)"},
                "text":        {"type": "string", "description": "Текст объявления, до 81 символа"},
                "href":        {"type": "string", "description": "URL посадочной страницы"},
                "display_url": {"type": "string", "description": "Отображаемый домен (необязательно)"},
            },
            "required": ["ad_group_id", "title", "text", "href"],
        },
    },
    # ── Ключевые слова ────────────────────────────────────────────────────────
    {
        "name": "add_keywords",
        "description": "Добавить ключевые слова в группу. Поддерживает синтаксис Яндекса (+слово, \"фраза\", [порядок]).",
        "input_schema": {
            "type": "object",
            "properties": {
                "ad_group_id": {"type": "integer"},
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Список ключевых фраз",
                },
                "bid": {"type": "number", "description": "Начальная ставка в рублях (необязательно)"},
            },
            "required": ["ad_group_id", "keywords"],
        },
    },
    {
        "name": "add_negative_keywords",
        "description": "Добавить минус-слова на уровне кампании.",
        "input_schema": {
            "type": "object",
            "properties": {
                "campaign_id": {"type": "integer"},
                "negatives": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Список минус-слов",
                },
            },
            "required": ["campaign_id", "negatives"],
        },
    },
    {
        "name": "get_keywords",
        "description": "Получить ключевые слова кампании с текущими ставками и статусами.",
        "input_schema": {
            "type": "object",
            "properties": {
                "campaign_id": {"type": "integer"}
            },
            "required": ["campaign_id"],
        },
    },
    # ── Ставки ────────────────────────────────────────────────────────────────
    {
        "name": "set_keyword_bids",
        "description": "Установить или изменить ставки для ключевых слов.",
        "input_schema": {
            "type": "object",
            "properties": {
                "keyword_bids": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "KeywordId": {"type": "integer"},
                            "Bid":       {"type": "number", "description": "Ставка в рублях"},
                        },
                        "required": ["KeywordId", "Bid"],
                    },
                }
            },
            "required": ["keyword_bids"],
        },
    },
    # ── Исключения ────────────────────────────────────────────────────────────
    {
        "name": "add_site_exclusions",
        "description": "Добавить запрещённые площадки для показа в РСЯ.",
        "input_schema": {
            "type": "object",
            "properties": {
                "campaign_id": {"type": "integer"},
                "sites": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Список доменов для исключения",
                },
            },
            "required": ["campaign_id", "sites"],
        },
    },
    # ── Ретаргетинг ───────────────────────────────────────────────────────────
    {
        "name": "create_retargeting_campaign",
        "description": "Создать ретаргетинговую кампанию на аудиторию, которая посещала сайт но не оставила заявку.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name":         {"type": "string"},
                "daily_budget": {"type": "number", "description": "Дневной бюджет в рублях"},
                "start_date":   {"type": "string", "description": "YYYY-MM-DD"},
                "goal_id":      {"type": "integer", "description": "ID цели в Яндекс Метрике"},
                "days":         {"type": "integer", "description": "Окно аудитории: 7, 14 или 30 дней", "enum": [7, 14, 30]},
            },
            "required": ["name", "daily_budget", "start_date", "goal_id"],
        },
    },
    # ── Статистика Директ ─────────────────────────────────────────────────────
    {
        "name": "get_campaign_stats",
        "description": "Получить статистику по кампаниям: клики, показы, CTR, расход.",
        "input_schema": {
            "type": "object",
            "properties": {
                "campaign_ids": {"type": "array", "items": {"type": "integer"}},
                "date_from":    {"type": "string", "description": "YYYY-MM-DD"},
                "date_to":      {"type": "string", "description": "YYYY-MM-DD"},
            },
            "required": ["campaign_ids", "date_from", "date_to"],
        },
    },
    {
        "name": "get_keyword_stats",
        "description": "Получить статистику по ключевым словам кампании.",
        "input_schema": {
            "type": "object",
            "properties": {
                "campaign_id": {"type": "integer"},
                "date_from":   {"type": "string", "description": "YYYY-MM-DD"},
                "date_to":     {"type": "string", "description": "YYYY-MM-DD"},
            },
            "required": ["campaign_id", "date_from", "date_to"],
        },
    },
    # ── Аналитика ─────────────────────────────────────────────────────────────
    {
        "name": "get_webvisor_insights",
        "description": "Получить аналитику поведения пользователей на сайте: устройства, отказы, источники трафика.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date_from": {"type": "string", "description": "YYYY-MM-DD"},
                "date_to":   {"type": "string", "description": "YYYY-MM-DD"},
            },
            "required": ["date_from", "date_to"],
        },
    },
    {
        "name": "analyze_full_funnel",
        "description": "Полный анализ маркетинговой воронки: реклама → сайт → лиды → качество.",
        "input_schema": {
            "type": "object",
            "properties": {
                "campaign_ids": {"type": "array", "items": {"type": "integer"}},
                "date_from":    {"type": "string", "description": "YYYY-MM-DD"},
                "date_to":      {"type": "string", "description": "YYYY-MM-DD"},
            },
            "required": ["campaign_ids", "date_from", "date_to"],
        },
    },
    {
        "name": "get_site_recommendations",
        "description": "Получить ИИ рекомендации по улучшению сайта на основе данных Вебвизора и лидов.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date_from":     {"type": "string", "description": "YYYY-MM-DD"},
                "date_to":       {"type": "string", "description": "YYYY-MM-DD"},
                "extra_context": {"type": "string", "description": "Дополнительный контекст (наблюдения, заметки)"},
            },
            "required": ["date_from", "date_to"],
        },
    },
    # ── Лиды и обратная связь ─────────────────────────────────────────────────
    {
        "name": "get_lead_stats",
        "description": "Получить статистику лидов: % целевых, по источникам, причины отказов.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "process_client_feedback",
        "description": "Проанализировать обратную связь клиента о лидах и сформировать план действий.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_last_report",
        "description": "Получить текст последнего сформированного отчёта.",
        "input_schema": {"type": "object", "properties": {}},
    },
]
