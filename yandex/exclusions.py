from .client import client


def add_site_exclusions(campaign_id: int, sites: list[str]) -> None:
    """Добавить запрещённые площадки (сайты) для кампании."""
    client.call("campaigns", "update", {
        "Campaigns": [{
            "Id": campaign_id,
            "ExcludedSites": {"Items": sites},
        }]
    })


def add_app_exclusions(campaign_id: int, app_ids: list[str]) -> None:
    """Добавить запрещённые мобильные приложения."""
    # Приложения задаются как площадки с префиксом app_
    formatted = [f"app_{a}" if not a.startswith("app_") else a for a in app_ids]
    client.call("campaigns", "update", {
        "Campaigns": [{
            "Id": campaign_id,
            "ExcludedSites": {"Items": formatted},
        }]
    })
