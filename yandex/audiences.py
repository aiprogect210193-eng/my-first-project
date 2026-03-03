from .client import client


def create_retargeting_campaign(
    name: str,
    daily_budget: float,
    start_date: str,
    goal_id: int,
    days: int = 30,
) -> int:
    """
    Создать ретаргетинговую кампанию на аудиторию, которая
    посещала сайт за последние N дней но не выполнила цель.
    Возвращает Id созданной кампании.

    Примечание: аудитория для ретаргетинга настраивается через условия
    ретаргетинга в группе объявлений (RetargetingList) — здесь создаётся
    кампания-оболочка, группы добавляются отдельно.
    """
    result = client.call("campaigns", "add", {
        "Campaigns": [{
            "Name": f"{name} (ретаргетинг {days}д)",
            "StartDate": start_date,
            "DailyBudget": {
                "Amount": int(daily_budget * 1_000_000),
                "Mode": "STANDARD",
            },
            "TextCampaign": {
                "BiddingStrategy": {
                    "Search": {"BiddingStrategyType": "SERVING_OFF"},
                    "Network": {
                        "BiddingStrategyType": "MAXIMUM_CLICKS",
                        "MaximumClicks": {
                            "WeeklySpendLimit": int(daily_budget * 7 * 1_000_000),
                        },
                    },
                }
            },
        }]
    })
    campaign_id = result["AddResults"][0]["Id"]
    return campaign_id


def create_retargeting_condition(
    name: str,
    goal_id: int,
    days: int,
) -> int:
    """
    Создать условие ретаргетинга: посещали сайт N дней, не выполнили цель.
    Возвращает Id условия.
    """
    result = client.call("retargetinglists", "add", {
        "RetargetingLists": [{
            "Name": name,
            "Rules": [
                {
                    "Goals": [{"Id": goal_id, "Goal": "NOT_ACHIEVED"}],
                    "InclusionType": "ALL",
                    "MaxDays": days,
                }
            ],
        }]
    })
    return result["AddResults"][0]["Id"]
