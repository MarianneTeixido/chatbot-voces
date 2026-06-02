import json

import requests

from config import OLLAMA_MODEL, OLLAMA_URL


def ask_ollama(messages: list) -> str:
    payload = {"model": OLLAMA_MODEL, "messages": messages, "stream": True}
    try:
        resp = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=120)
        resp.raise_for_status()
    except requests.exceptions.ConnectionError:
        print("[Error] No se puede conectar a Ollama en", OLLAMA_URL)
        return ""

    full_text = ""
    print("\nAgencia: ", end="", flush=True)

    for line in resp.iter_lines():
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue

        chunk = data.get("message", {}).get("content", "")
        print(chunk, end="", flush=True)
        full_text += chunk

        if data.get("done"):
            break

    print()
    return full_text.strip()
