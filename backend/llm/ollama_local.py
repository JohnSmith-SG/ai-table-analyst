"""Локальные модели через Ollama (REST API на этом же компьютере, без интернета и ключей)."""
import os

import requests
from .common import MAX_TOKENS

HOST = os.environ.get("OLLAMA_HOST_URL", "http://127.0.0.1:11434")
# на CPU без видеокарты ответ может идти долго — по умолчанию ждём до 3 часов
TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", "10800"))


class OllamaModel:
    def __init__(self, model: str, think: bool | None = None, num_predict: int = MAX_TOKENS):
        self.model = model
        # think=True: «размышления» модели приходят отдельным полем и в ответ не попадают
        self.think = think
        # лимит считает и размышления, поэтому думающей модели нужен запас
        self.num_predict = num_predict
        self.MODEL_NAME = f"{model} (локально, Ollama)"

    def ask(self, system: str, user: str) -> str:
        payload = {"model": self.model, "stream": False,
                   "options": {"temperature": 0.3, "num_predict": self.num_predict},
                   "messages": [{"role": "system", "content": system},
                                {"role": "user", "content": user}]}
        if self.think is not None:
            payload["think"] = self.think
        try:
            r = requests.post(f"{HOST}/api/chat", json=payload, timeout=TIMEOUT)
        except requests.ConnectionError:
            raise RuntimeError(f"Ollama не отвечает на {HOST} — запустите Ollama (ollama serve)")
        body = r.json()
        if r.status_code != 200:
            raise RuntimeError(f"Ollama {r.status_code}: {body.get('error') or body}")
        msg = body["message"]
        print(f"[ollama] {self.model}: размышления {len(msg.get('thinking') or '')} зн., "
              f"ответ {len(msg['content'])} зн., токенов {body.get('eval_count')}", flush=True)
        return msg["content"].strip()


GEMMA = OllamaModel(os.environ.get("OLLAMA_MODEL", "gemma3:4b-analyst"))
# qwen3 с think=False всё равно рассуждает — но прямо в тексте ответа и упирается в лимит
# (проверено 20.10.2026: 900 токенов «размышлений вслух» без выводов), поэтому think=True
QWEN = OllamaModel(os.environ.get("OLLAMA_MODEL_QWEN", "qwen3:4b-analyst"), think=True, num_predict=4096)
