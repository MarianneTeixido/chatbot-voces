import json
import os
import tempfile
import time

import pygame
import requests

from config import ALLTALK_URL, LANGUAGE


def speak(text: str, voice_wav: str) -> None:
    if not text:
        return

    voice_wav = os.path.abspath(voice_wav)

    form_data = {
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
        "pitch":                 "0",
        "temperature":           "0.75",
        "repetition_penalty":    "10.0",
    }

    try:
        resp = requests.post(ALLTALK_URL, data=form_data, timeout=60)
        if not resp.ok:
            print(f"[Error TTS HTTP] {resp.status_code} — {resp.text[:500]}")
            return
    except requests.exceptions.ConnectionError:
        print("[Error] No se puede conectar a AllTalk en", ALLTALK_URL)
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

    audio_url = result.get("output_file_url", "")
    if audio_url:
        _play_from_url(f"http://localhost:7851{audio_url}")
    else:
        print(f"[Error TTS] No se encontró archivo de audio. Respuesta: {result}")


def _play_local(path: str) -> None:
    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.05)
    except pygame.error as e:
        print(f"[Error pygame] {e}")


def _play_from_url(url: str) -> None:
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
