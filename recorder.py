import os
import time

import numpy as np
import scipy.io.wavfile as wav
import sounddevice as sd

from config import RECORD_DURATION, VOICE_TEMP_WAV, VOICES_DIR

SAMPLE_RATE = 44100


def grabar_voz(duracion: int = RECORD_DURATION, path_salida: str = VOICE_TEMP_WAV) -> str:
    os.makedirs(VOICES_DIR, exist_ok=True)

    print("\n[Grabación] Preparate. Comenzando en...")
    for i in range(3, 0, -1):
        print(f"  {i}...", flush=True)
        time.sleep(1)
    print("  ¡GRABANDO!", flush=True)

    audio = sd.rec(
        int(duracion * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16",
    )

    for seg in range(duracion, 0, -1):
        print(f"  {seg} seg restantes...   ", end="\r", flush=True)
        time.sleep(1)

    sd.wait()
    print("\n  [Grabación completada]")

    wav.write(path_salida, SAMPLE_RATE, audio)
    return path_salida
