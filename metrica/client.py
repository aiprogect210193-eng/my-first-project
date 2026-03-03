import requests
from config import YANDEX_TOKEN

METRICA_BASE = "https://api-metrika.yandex.net/"


class MetricaClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"OAuth {YANDEX_TOKEN}",
            "Content-Type": "application/json",
        })

    def get(self, path: str, params: dict) -> dict:
        url = f"{METRICA_BASE}{path}"
        resp = self.session.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()


client = MetricaClient()
