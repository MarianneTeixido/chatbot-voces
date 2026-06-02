import os
import time

import numpy as np
import scipy.io.wavfile as wav
import sounddevice as sd

from config import AUDIO_INPUT_DEVICE, RECORD_DURATION, VOICE_TEMP_WAV, VOICES_DIR

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
        device=AUDIO_INPUT_DEVICE,
    )

    for seg in range(duracion, 0, -1):
        print(f"  {seg} seg restantes...   ", end="\r", flush=True)
        time.sleep(1)

    sd.stop()
    print("\n  [Grabación completada]")

    wav.write(path_salida, SAMPLE_RATE, audio)

    # Diagnóstico: verificar que el audio tiene señal real
    max_amp = int(np.max(np.abs(audio)))
    size_kb = os.path.getsize(path_salida) // 1024
    print(f"  [Diagnóstico] Amplitud máxima: {max_amp} (>500 = hay voz)")
    print(f"  [Diagnóstico] Archivo: {os.path.abspath(path_salida)} ({size_kb} KB)")
    if max_amp < 500:
        print("  [ADVERTENCIA] La grabación parece silencio. Verifica el micrófono.")
        print("  Dispositivos de entrada disponibles:")
        for d in sd.query_devices():
            if d["max_input_channels"] > 0:
                print(f"    [{d['index']}] {d['name']}")
    else:
        print("  [OK] Audio grabado correctamente.")

    return path_salida
