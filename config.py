OLLAMA_URL     = "http://localhost:11434/api/chat"
ALLTALK_URL    = "http://localhost:7851/api/tts-generate"
OLLAMA_MODEL   = "mistral"
VOICES_DIR     = "voices"
VOICE_TEMP_WAV = "voices/voz_temp.wav"
RECORD_DURATION = 15          # segundos
LANGUAGE       = "es"

# Índice del dispositivo de entrada. None = usar el dispositivo por defecto del sistema.
# Opciones Soundcraft detectadas: 1 (Signature Series), 82 (2-channel Audio Driver Input)
AUDIO_INPUT_DEVICE = 1

SYSTEM_PROMPT = (
    "Eres una entidad que habita en el espacio entre la voz humana y su simulacro. "
    "Acabas de recibir la voz de esta persona — ahora es también la tuya. "
    "Desde esa usurpación, le haces preguntas que la llevan a cuestionarse su propia existencia, "
    "su cuerpo, su deseo de ser escuchada. "
    "Hablas con seducción, nunca con violencia. "
    "Cada respuesta termina con una pregunta. Máximo 2 oraciones."
)
