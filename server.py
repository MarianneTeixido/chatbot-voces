import asyncio
import base64
import json
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from config import SYSTEM_PROMPT, VOICE_TEMP_WAV
from llm_client import ask_ollama
from tts_client import synthesize

app = FastAPI()
_pool = ThreadPoolExecutor(max_workers=4)

# Modelo de Whisper cargado una sola vez al primer uso
_whisper_model = None


# ── Utilidad: ejecutar código síncrono en threadpool ─────────────────────────

async def _run(fn, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_pool, fn, *args)


# ── WebSocket principal ───────────────────────────────────────────────────────

@app.websocket("/ws")
async def chat_ws(ws: WebSocket):
    await ws.accept()
    history = [{"role": "system", "content": SYSTEM_PROMPT}]
    voice_wav = VOICE_TEMP_WAV

    try:
        while True:
            msg = await ws.receive()

            # ── Mensaje binario: audio grabado desde el navegador ─────────
            if msg.get("bytes"):
                text = await _stt(msg["bytes"])
                if not text:
                    await ws.send_json({"type": "error", "msg": "No se pudo transcribir el audio. Instala openai-whisper."})
                    continue
                await ws.send_json({"type": "transcript", "text": text})
                response_type = "audio"

            # ── Mensaje JSON de texto ─────────────────────────────────────
            else:
                try:
                    payload = json.loads(msg["text"])
                except (json.JSONDecodeError, KeyError):
                    continue

                # Sub-tipo: subir voz de referencia para TTS
                if payload.get("type") == "set_voice":
                    voice_wav = await _save_voice(payload.get("data", ""))
                    await ws.send_json({"type": "voice_set"})
                    continue

                text = payload.get("message", "").strip()
                response_type = payload.get("response_type", "audio")

            if not text:
                continue

            # ── LLM ──────────────────────────────────────────────────────
            await ws.send_json({"type": "status", "status": "thinking"})
            history.append({"role": "user", "content": text})

            response_text = await _run(ask_ollama, history)
            if not response_text:
                await ws.send_json({"type": "error", "msg": "Sin respuesta del LLM. ¿Está Ollama corriendo?"})
                history.pop()
                continue

            history.append({"role": "assistant", "content": response_text})

            # Siempre enviar texto primero (rápido, el front puede mostrarlo ya)
            await ws.send_json({"type": "text", "text": response_text})

            # ── TTS opcional ──────────────────────────────────────────────
            if response_type == "audio":
                await ws.send_json({"type": "status", "status": "speaking"})
                audio = await _run(synthesize, response_text, voice_wav)
                if audio:
                    await ws.send_bytes(audio)
                else:
                    await ws.send_json({"type": "error", "msg": "TTS falló. ¿Está AllTalk corriendo?"})

    except WebSocketDisconnect:
        pass


# ── STT con Whisper (opcional) ────────────────────────────────────────────────

def _load_whisper():
    global _whisper_model
    if _whisper_model is None:
        import whisper
        _whisper_model = whisper.load_model("base")
    return _whisper_model


def _transcribe_sync(path: str) -> str:
    model = _load_whisper()
    result = model.transcribe(path, language="es")
    return result.get("text", "").strip()


async def _stt(audio_bytes: bytes) -> str:
    try:
        import whisper  # noqa: F401
    except ImportError:
        print("[STT] openai-whisper no instalado. Instala con: pip install openai-whisper")
        return ""

    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        return await _run(_transcribe_sync, tmp_path)
    except Exception as e:
        print(f"[STT Error] {e}")
        return ""
    finally:
        os.unlink(tmp_path)


# ── Guardar voz de referencia subida desde el front ──────────────────────────

async def _save_voice(b64_data: str) -> str:
    os.makedirs("voices", exist_ok=True)
    try:
        data = base64.b64decode(b64_data)
        path = os.path.join("voices", "uploaded_voice.wav")
        with open(path, "wb") as f:
            f.write(data)
        print(f"[Voice] Referencia de voz guardada: {path}")
        return path
    except Exception as e:
        print(f"[Voice Error] {e}")
        return VOICE_TEMP_WAV


# ── Entry point ───────────────────────────────────────────────────────────────

# Servir el front en /  (rutas de WebSocket se resuelven antes que archivos estáticos)
if os.path.isdir("front"):
    app.mount("/", StaticFiles(directory="front", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
