import json
import os
import sys
import time

import pygame
import requests

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
OLLAMA_URL    = "http://localhost:11434/api/chat"
ALLTALK_URL   = "http://localhost:7851/api/tts-generate"
OLLAMA_MODEL  = "llama3.2"           # cambia al modelo que tengas en Ollama
VOICE_WAV     = "xyk_p02-p06.wav"          # nombre del .wav en la carpeta de voces de AllTalk
LANGUAGE      = "es"                 # idioma para AllTalk
SYSTEM_PROMPT = (
    "Eres un asistente útil y amigable. "
    "Responde siempre de forma concisa, en 1-3 oraciones."
)
# ---------------------------------------------------------------------------


def ask_ollama(messages: list) -> str:
    """Envía el historial a Ollama con streaming y devuelve el texto completo."""
    payload = {"model": OLLAMA_MODEL, "messages": messages, "stream": True}
    try:
        resp = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=120)
        resp.raise_for_status()
    except requests.exceptions.ConnectionError:
        print("[Error] No se puede conectar a Ollama en", OLLAMA_URL)
        return ""

    full_text = ""
    print("\nAsistente: ", end="", flush=True)

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


def speak(text: str) -> None:
    """Envía el texto a AllTalk TTS y reproduce el audio generado."""
    if not text:
        return

    form_data = {
        "text_input":            text,
        "text_filtering":        "standard",
        "character_voice_gen":   VOICE_WAV,
        "narrator_enabled":      "false",
        "narrator_voice_gen":    "none",
        "text_not_inside":       "character",
        "language":              LANGUAGE,
        "output_file_name":      "chatbot_out",
        "output_file_timestamp": "true",
        "autoplay":              "false",
        "autoplay_volume":       "0.8",
        "speed":                 "1.0",
        "pitch":                 "0",
        "temperature":           "0.75",
        "repetition_penalty":    "10.0",
    }

    try:
        resp = requests.post(ALLTALK_URL, data=form_data, timeout=60)
        resp.raise_for_status()
    except requests.exceptions.ConnectionError:
        print("[Error] No se puede conectar a AllTalk en", ALLTALK_URL)
        return
    except requests.exceptions.HTTPError as e:
        print(f"[Error TTS HTTP] {e}")
        return

    try:
        result = resp.json()
    except json.JSONDecodeError:
        print("[Error TTS] Respuesta no es JSON válido")
        return

    audio_path = result.get("output_file_path", "")
    if audio_path and os.path.isfile(audio_path):
        _play_local(audio_path)
        return

    # Fallback: descargar desde URL relativa si AllTalk no devuelve ruta local
    audio_url = result.get("output_file_url", "")
    if audio_url:
        _play_from_url(f"http://localhost:7851{audio_url}")
    else:
        print(f"[Error TTS] No se encontró archivo de audio. Respuesta: {result}")


def _play_local(path: str) -> None:
    """Carga y reproduce un archivo de audio local con pygame."""
    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.05)
    except pygame.error as e:
        print(f"[Error pygame] {e}")


def _play_from_url(url: str) -> None:
    """Descarga audio desde una URL y lo reproduce (fallback)."""
    import tempfile
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"[Error descargando audio] {e}")
        return

    suffix = ".wav" if "wav" in url else ".mp3"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(resp.content)
        tmp_path = tmp.name

    _play_local(tmp_path)
    os.unlink(tmp_path)


def main() -> None:
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
    print("=" * 50)
    print("  Chatbot con voz  |  escribe 'salir' para salir")
    print("=" * 50)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        try:
            user_input = input("\nTú: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nHasta luego.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("salir", "exit", "quit", "q"):
            print("Hasta luego.")
            break

        messages.append({"role": "user", "content": user_input})

        response_text = ask_ollama(messages)
        if response_text:
            messages.append({"role": "assistant", "content": response_text})
            speak(response_text)

    pygame.mixer.quit()


if __name__ == "__main__":
    main()
