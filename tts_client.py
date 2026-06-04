import json
import os
import tempfile
import time
from typing import Optional

import pygame
import requests

from config import ALLTALK_URL, LANGUAGE


def _build_form(text: str, voice_wav: str, pitch: int = 0) -> dict:
    return {
        "text_input":            text,
        "text_filtering":        "standard",
        "character_voice_gen":   voice_wav,
        "narrator_enabled":      "false",
        "narrator_voice_gen":    "none",
        "text_not_inside":       "character",
        "language":              LANGUAGE,
        "output_file_name":      "chatbot_out",
        "output_file_timestamp": "true",
        "autoplay":              "false",
        "autoplay_volume":       "0.8",
        "speed":                 "1.0",
        "pitch":                 str(pitch),
        "temperature":           "0.1",
        "repetition_penalty":    "10.0",
    }


def _fetch_audio(text: str, voice_wav: str, pitch: int = 0) -> Optional[bytes]:
    """Llama a AllTalk y devuelve los bytes del audio generado, o None si falla."""
    if not os.path.isabs(voice_wav):
        voice_wav = os.path.abspath(voice_wav)
    print(f"[TTS] Usando voz: {voice_wav} (existe={os.path.isfile(voice_wav)})")

    try:
        resp = requests.post(ALLTALK_URL, data=_build_form(text, voice_wav, pitch), timeout=60)
        if not resp.ok:
            print(f"[Error TTS HTTP] {resp.status_code} — {resp.text[:500]}")
            return None
    except requests.exceptions.ConnectionError:
        print("[Error] No se puede conectar a AllTalk en", ALLTALK_URL)
        return None

    try:
        result = resp.json()
    except json.JSONDecodeError:
        print("[Error TTS] Respuesta no es JSON válido")
        return None

    print(f"[TTS] Respuesta AllTalk: {result}")

    audio_path = result.get("output_file_path", "")
    if audio_path and os.path.isfile(audio_path):
        with open(audio_path, "rb") as f:
            return f.read()

    audio_url = result.get("output_file_url", "")
    if audio_url:
        try:
            r = requests.get(f"http://localhost:7851{audio_url}", timeout=30)
            r.raise_for_status()
            return r.content
        except requests.exceptions.RequestException as e:
            print(f"[Error descargando audio] {e}")
            return None

    print(f"[Error TTS] No se encontró archivo de audio. Respuesta: {result}")
    return None


def synthesize(text: str, voice_wav: str, pitch: int = 0) -> Optional[bytes]:
    """Genera audio TTS y devuelve los bytes — para enviar por WebSocket."""
    if not text:
        return None
    return _fetch_audio(text, voice_wav, pitch)


def speak(text: str, voice_wav: str, pitch: int = 0) -> None:
    """Genera audio TTS y lo reproduce localmente — para uso en CLI."""
    if not text:
        return
    audio = _fetch_audio(text, voice_wav, pitch)
    if not audio:
        return
    suffix = ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(audio)
        tmp_path = tmp.name
    try:
        _play_local(tmp_path)
    finally:
        os.unlink(tmp_path)


def _play_local(path: str) -> None:
    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.05)
    except pygame.error as e:
        print(f"[Error pygame] {e}")
