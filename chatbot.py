import pygame

from config import SYSTEM_PROMPT
from llm_client import ask_ollama
from recorder import grabar_voz
from tts_client import speak


def main() -> None:
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

    print("=" * 50)
    print("  Voces Híbrides  |  Ctrl+C para detener")
    print("=" * 50)

    voice_wav = grabar_voz()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        try:
            user_input = input("\nTú: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n")
            break

        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})

        response_text = ask_ollama(messages)
        if response_text:
            messages.append({"role": "assistant", "content": response_text})
            speak(response_text, voice_wav)

    pygame.mixer.quit()


if __name__ == "__main__":
    main()
