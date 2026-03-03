from .client import client


def create_ad(
    ad_group_id: int,
    title: str,
    text: str,
    href: str,
    title2: str = "",
    display_url: str = "",
) -> int:
    """
    Создать текстовое объявление.
    title — до 35 символов
    title2 — до 30 символов (необязательно)
    text — до 81 символа
    """
    ad: dict = {
        "AdGroupId": ad_group_id,
        "TextAd": {
            "Title": title,
            "Text": text,
            "Href": href,
        },
    }
    if title2:
        ad["TextAd"]["Title2"] = title2
    if display_url:
        ad["TextAd"]["DisplayUrlPath"] = display_url

    result = client.call("ads", "add", {"Ads": [ad]})
    return result["AddResults"][0]["Id"]


def list_ads(ad_group_id: int) -> list[dict]:
    result = client.call("ads", "get", {
        "SelectionCriteria": {"AdGroupIds": [ad_group_id]},
        "FieldNames": ["Id", "State", "Status"],
        "TextAdFieldNames": ["Title", "Title2", "Text", "Href"],
    })
    return result.get("Ads", [])
