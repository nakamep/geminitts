from google.cloud import texttospeech

def list_tts_voices():
    client = texttospeech.TextToSpeechClient()
    response = client.list_voices()
    
    print("Available Voices:")
    for voice in response.voices:
        lang_codes = ", ".join(voice.language_codes)
        gender = texttospeech.SsmlVoiceGender(voice.ssml_gender).name
        print(f"  Name: {voice.name}")
        print(f"    Language Codes: {lang_codes}")
        print(f"    SSML Gender: {gender}")
        # print(f"    Natural Sample Rate Hertz: {voice.natural_sample_rate_hertz}") # Optional
        print("-" * 20)

if __name__ == "__main__":
    list_tts_voices()
