"""GigaChat 2 Pro через REST. Ключ авторизации -> токен доступа на 30 минут (кэшируется)."""
import threading
import time
import uuid
from pathlib import Path

import requests
from .common import MAX_TOKENS, TIMEOUT, secret

OAUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
CHAT_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
SCOPE = "GIGACHAT_API_PERS"
MODEL_NAME = "GigaChat 2 Pro"
CA = str(Path(__file__).with_name("russian_trusted_root_ca.pem"))  # сертификат Минцифры

_token = None
_expires = 0.0
_lock = threading.Lock()


def _access_token() -> str:
    global _token, _expires
    with _lock:
        if _token and time.time() < _expires - 60:
            return _token
        r = requests.post(
            OAUTH_URL, data={"scope": SCOPE}, verify=CA, timeout=TIMEOUT,
            headers={"Authorization": "Basic " + secret("GIGACHAT_AUTH_KEY"),
                     "RqUID": str(uuid.uuid4()), "Accept": "application/json"})
        body = r.json()
        if r.status_code != 200:
            raise RuntimeError(f"GigaChat OAuth {r.status_code}: {body.get('message', body)}")
        _token = body["access_token"]
        _expires = body["expires_at"] / 1000
        return _token


def ask(system: str, user: str) -> str:
    r = requests.post(
        CHAT_URL, verify=CA, timeout=TIMEOUT,
        headers={"Authorization": f"Bearer {_access_token()}"},
        json={"model": "GigaChat-2-Pro", "max_tokens": MAX_TOKENS, "temperature": 0.3,
              "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]})
    body = r.json()
    if r.status_code != 200:
        raise RuntimeError(f"GigaChat {r.status_code}: {body.get('message', body)}")
    return body["choices"][0]["message"]["content"].strip()
