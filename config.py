import os
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise RuntimeError(
            f"Переменная окружения '{key}' не задана. Проверьте файл .env"
        )
    return val


ANTHROPIC_API_KEY: str = _require("ANTHROPIC_API_KEY")
YANDEX_TOKEN: str = _require("YANDEX_OAUTH_TOKEN")
YANDEX_LOGIN: str = _require("YANDEX_CLIENT_LOGIN")

METRICA_COUNTER_ID: str = _require("YANDEX_METRICA_COUNTER_ID")
METRICA_GOAL_ID: str = _require("YANDEX_METRICA_GOAL_ID")

TARGET_CPL: float = float(os.getenv("TARGET_CPL", "500"))
CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-opus-4-6")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

YANDEX_DIRECT_BASE: str = "https://api.direct.yandex.com/json/v5/"
YANDEX_METRICA_BASE: str = "https://api-metrika.yandex.net/stat/v1/"
