from .client import client

# Москва=1, СПб=2, Россия=225 — стандартные ID регионов Яндекса
DEFAULT_REGIONS = [225]


def list_adgroups(campaign_id: int) -> list[dict]:
    result = client.call("adgroups", "get", {
        "SelectionCriteria": {"CampaignIds": [campaign_id]},
        "FieldNames": ["Id", "Name", "Status", "CampaignId", "RegionIds"],
    })
    return result.get("AdGroups", [])


def create_adgroup(
    campaign_id: int,
    name: str,
    region_ids: list[int] | None = None,
) -> int:
    """Создать группу объявлений. Возвращает Id."""
    result = client.call("adgroups", "add", {
        "AdGroups": [{
            "Name": name,
            "CampaignId": campaign_id,
            "RegionIds": region_ids or DEFAULT_REGIONS,
        }]
    })
    return result["AddResults"][0]["Id"]


def pause_adgroup(ad_group_id: int) -> None:
    client.call("adgroups", "suspend", {
        "SelectionCriteria": {"Ids": [ad_group_id]}
    })


def batch_pause_adgroups(group_ids: list[int]) -> list[dict]:
    """Остановить несколько групп за один вызов."""
    result = client.call("adgroups", "suspend", {
        "SelectionCriteria": {"Ids": group_ids}
    })
    return result.get("SuspendResults", [])


def resume_adgroup(ad_group_id: int) -> None:
    client.call("adgroups", "resume", {
        "SelectionCriteria": {"Ids": [ad_group_id]}
    })
