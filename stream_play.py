import os
import sys
import pyaudio
from google import genai
from google.genai import types

RECEIVE_SAMPLE_RATE = 24000
FORMAT = pyaudio.paInt16
CHANNELS = 1

def stream_tts(text: str, voice_name: str = "Kore"):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")
    client = genai.Client(api_key=api_key)
    config = types.GenerateContentConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
            )
        ),
    )

    stream = client.models.generate_content_stream(
        model="gemini-2.5-flash-preview-tts",
        contents=text,
        config=config,
    )

    pya = pyaudio.PyAudio()
    audio_stream = pya.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RECEIVE_SAMPLE_RATE,
        output=True,
    )

    try:
        for chunk in stream:
            if (
                chunk.candidates
                and chunk.candidates[0].content
                and chunk.candidates[0].content.parts
            ):
                part = chunk.candidates[0].content.parts[0]
                if part.inline_data and part.inline_data.data:
                    audio_stream.write(part.inline_data.data)
    finally:
        audio_stream.stop_stream()
        audio_stream.close()
        pya.terminate()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python stream_play.py 'text to synthesize'")
        sys.exit(1)
    stream_tts(sys.argv[1])
