"""YandexGPT Pro 5.1 через REST (Yandex Cloud, API-ключ сервисного аккаунта)."""
import requests
from .common import MAX_TOKENS, TIMEOUT, secret

URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
MODEL_NAME = "YandexGPT Pro 5.1"


def ask(system: str, user: str) -> str:
    folder = secret("YANDEX_FOLDER_ID")
    r = requests.post(
        URL,
        headers={"Authorization": "Api-Key " + secret("YANDEX_API_KEY"), "x-folder-id": folder},
        json={"modelUri": f"gpt://{folder}/yandexgpt/rc",
              "completionOptions": {"stream": False, "temperature": 0.3, "maxTokens": str(MAX_TOKENS)},
              "messages": [{"role": "system", "text": system}, {"role": "user", "text": user}]},
        timeout=TIMEOUT)
    body = r.json()
    if r.status_code != 200:
        raise RuntimeError(f"YandexGPT {r.status_code}: {body.get('message') or body}")
    return body["result"]["alternatives"][0]["message"]["text"].strip()
