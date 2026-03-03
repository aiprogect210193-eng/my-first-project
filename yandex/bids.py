from .client import client


def set_keyword_bids(keyword_bids: list[dict]) -> list[dict]:
    """
    Установить ставки для ключевых слов.
    keyword_bids: список {"KeywordId": int, "Bid": float (в рублях)}
    """
    payload = [
        {"KeywordId": item["KeywordId"], "Bid": int(item["Bid"] * 1_000_000)}
        for item in keyword_bids
    ]
    result = client.call("bids", "set", {"Bids": payload})
    return result.get("SetResults", [])


def get_bids(keyword_ids: list[int]) -> list[dict]:
    result = client.call("bids", "get", {
        "SelectionCriteria": {"KeywordIds": keyword_ids},
        "FieldNames": ["KeywordId", "Bid", "ContextBid", "AuctionBids"],
    })
    return result.get("Bids", [])
