"""Локальная модель через Ollama (REST API на этом же компьютере, без интернета и ключей)."""
import os

import requests
from .common import MAX_TOKENS

HOST = os.environ.get("OLLAMA_HOST_URL", "http://127.0.0.1:11434")
MODEL = os.environ.get("OLLAMA_MODEL", "gemma3:4b-analyst")
MODEL_NAME = f"{MODEL} (локально, Ollama)"
# на CPU без видеокарты ответ может идти долго — по умолчанию ждём до 3 часов
TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", "10800"))


def ask(system: str, user: str) -> str:
    try:
        r = requests.post(
            f"{HOST}/api/chat",
            json={"model": MODEL, "stream": False,
                  "options": {"temperature": 0.3, "num_predict": MAX_TOKENS},
                  "messages": [{"role": "system", "content": system},
                               {"role": "user", "content": user}]},
            timeout=TIMEOUT)
    except requests.ConnectionError:
        raise RuntimeError(f"Ollama не отвечает на {HOST} — запустите Ollama (ollama serve)")
    body = r.json()
    if r.status_code != 200:
        raise RuntimeError(f"Ollama {r.status_code}: {body.get('error') or body}")
    return body["message"]["content"].strip()
