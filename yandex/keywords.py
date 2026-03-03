from .client import client


def add_keywords(
    ad_group_id: int,
    keywords: list[str],
    bid: float | None = None,
) -> list[dict]:
    """
    Добавить ключевые слова в группу.
    Поддерживает синтаксис Яндекса: +слово, -минус, "фраза", [порядок].
    """
    kw_objects = [{"Keyword": kw, "AdGroupId": ad_group_id} for kw in keywords]
    if bid:
        for kw in kw_objects:
            kw["Bid"] = int(bid * 1_000_000)
    result = client.call("keywords", "add", {"Keywords": kw_objects})
    return result.get("AddResults", [])


def get_keywords(campaign_id: int) -> list[dict]:
    """Получить ключевые слова кампании со ставками и статусом."""
    result = client.call("keywords", "get", {
        "SelectionCriteria": {"CampaignIds": [campaign_id]},
        "FieldNames": [
            "Id", "Keyword", "Status", "State", "ServingStatus",
            "Bid", "ContextBid", "AdGroupId", "CampaignId",
        ],
    })
    return result.get("Keywords", [])


def add_negative_keywords(campaign_id: int, negatives: list[str]) -> None:
    """Добавить минус-слова на уровне кампании."""
    client.call("campaigns", "update", {
        "Campaigns": [{
            "Id": campaign_id,
            "NegativeKeywords": {"Items": negatives},
        }]
    })


def pause_keyword(keyword_id: int) -> None:
    client.call("keywords", "suspend", {
        "SelectionCriteria": {"Ids": [keyword_id]}
    })
