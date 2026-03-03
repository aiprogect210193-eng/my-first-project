import requests
from config import YANDEX_TOKEN, YANDEX_LOGIN, YANDEX_DIRECT_BASE


class YandexAPIError(Exception):
    def __init__(self, error_dict: dict):
        code = error_dict.get("error_code", "")
        detail = error_dict.get("error_detail", "")
        msg = error_dict.get("error_string", "Неизвестная ошибка")
        super().__init__(f"[{code}] {msg}: {detail}")


class YandexDirectClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {YANDEX_TOKEN}",
            "Client-Login": YANDEX_LOGIN,
            "Accept-Language": "ru",
            "Content-Type": "application/json; charset=utf-8",
        })

    def call(self, service: str, method: str, params: dict) -> dict:
        url = f"{YANDEX_DIRECT_BASE}{service}"
        payload = {"method": method, "params": params}
        resp = self.session.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        body = resp.json()
        if "error" in body:
            raise YandexAPIError(body["error"])
        return body.get("result", body)


# Синглтон — все модули импортируют его
client = YandexDirectClient()
