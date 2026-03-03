from .client import client


def list_campaigns(states: list[str] | None = None) -> list[dict]:
    """Список кампаний с основными метриками."""
    criteria = {}
    if states:
        criteria["States"] = states
    result = client.call("campaigns", "get", {
        "SelectionCriteria": criteria,
        "FieldNames": ["Id", "Name", "State", "Status", "DailyBudget", "StartDate", "Type"],
    })
    return result.get("Campaigns", [])


def create_campaign(name: str, daily_budget: float, start_date: str) -> int:
    """Создать текстовую кампанию. Возвращает Id."""
    result = client.call("campaigns", "add", {
        "Campaigns": [{
            "Name": name,
            "StartDate": start_date,
            "DailyBudget": {
                "Amount": int(daily_budget * 1_000_000),
                "Mode": "STANDARD",
            },
            "TextCampaign": {
                "BiddingStrategy": {
                    "Search": {"BiddingStrategyType": "HIGHEST_POSITION"},
                    "Network": {"BiddingStrategyType": "SERVING_OFF"},
                }
            },
        }]
    })
    return result["AddResults"][0]["Id"]


def create_master_campaign(
    name: str,
    daily_budget: float,
    start_date: str,
    region_ids: list[int] | None = None,
) -> int:
    """Создать мастер-кампанию (SmartCampaign). Яндекс сам управляет таргетингом."""
    campaign = {
        "Name": name,
        "StartDate": start_date,
        "DailyBudget": {
            "Amount": int(daily_budget * 1_000_000),
            "Mode": "STANDARD",
        },
        "SmartCampaign": {
            "BiddingStrategy": {
                "Search": {
                    "BiddingStrategyType": "AVERAGE_CPA",
                    "AverageCpa": {
                        "Bid": int(500 * 1_000_000),
                        "WeeklySpendLimit": int(daily_budget * 7 * 1_000_000),
                    },
                },
                "Network": {"BiddingStrategyType": "SERVING_OFF"},
            }
        },
    }
    result = client.call("campaigns", "add", {"Campaigns": [campaign]})
    return result["AddResults"][0]["Id"]


def update_campaign_budget(campaign_id: int, daily_budget: float) -> None:
    """Обновить дневной бюджет кампании."""
    client.call("campaigns", "update", {
        "Campaigns": [{
            "Id": campaign_id,
            "DailyBudget": {
                "Amount": int(daily_budget * 1_000_000),
                "Mode": "STANDARD",
            },
        }]
    })


def pause_campaign(campaign_id: int) -> None:
    client.call("campaigns", "suspend", {
        "SelectionCriteria": {"Ids": [campaign_id]}
    })


def resume_campaign(campaign_id: int) -> None:
    client.call("campaigns", "resume", {
        "SelectionCriteria": {"Ids": [campaign_id]}
    })
