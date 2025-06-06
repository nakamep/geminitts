from flask import Flask, render_template, request, jsonify, send_file
import os
from google import genai
import wave
import io
from werkzeug.exceptions import HTTPException

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate-audio', methods=['POST'])
def generate_audio():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return jsonify({"error": "GEMINI_API_KEY not set"}), 500

    client = genai.Client(api_key=api_key)

    data = request.get_json()
    text_to_synthesize = data.get('text')
    voice_name_to_use = data.get('voice_name', 'Kore') # Default to 'Kore'

    if not text_to_synthesize:
        return jsonify({"error": "No text provided"}), 400

    try:
        # Configure the speech settings and response modality using the new SDK types
        config = genai.types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=genai.types.SpeechConfig(
                voice_config=genai.types.VoiceConfig(
                    prebuilt_voice_config=genai.types.PrebuiltVoiceConfig(
                        voice_name=voice_name_to_use
                    )
                )
            ),
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=text_to_synthesize,
            config=config,
        )
        
        # Ensure the response has the expected structure
        if not response.candidates or not response.candidates[0].content or not response.candidates[0].content.parts:
            raise ValueError("Unexpected response structure from Gemini API")

        audio_part = response.candidates[0].content.parts[0]
        if not audio_part.inline_data or not audio_part.inline_data.data:
             raise ValueError("Audio data not found in Gemini API response")

        audio_data_pcm = audio_part.inline_data.data

    except Exception as e:
        print(f"Error during Gemini API call: {e}")
        # Check for specific authentication errors if possible, though genai SDK might abstract this
        if "API key not valid" in str(e) or "PERMISSION_DENIED" in str(e): # Heuristic check
            return jsonify({"error": f"TTS generation failed: Invalid API Key or insufficient permissions. Details: {str(e)}"}), 401
        return jsonify({"error": f"TTS generation failed: {str(e)}"}), 500

    # Save PCM data to a WAV file in memory
    wav_buffer = io.BytesIO()
    try:
        with wave.open(wav_buffer, "wb") as wf:
            wf.setnchannels(1)  # Mono
            wf.setsampwidth(2)  # 16-bit PCM (2 bytes)
            wf.setframerate(24000)  # Gemini TTS sample rate
            wf.writeframes(audio_data_pcm)
        wav_buffer.seek(0)
    except Exception as e:
        print(f"Error during WAV processing: {e}")
        return jsonify({"error": f"Failed to process audio data: {str(e)}"}), 500

    return send_file(wav_buffer, mimetype='audio/wav')


@app.errorhandler(Exception)
def handle_unexpected_error(e):
    """Return JSON for any unhandled server errors."""
    if isinstance(e, HTTPException):
        code = e.code
        description = e.description
    else:
        code = 500
        description = str(e)
    return jsonify({"error": f"Unexpected server error: {description}"}), code

if __name__ == '__main__':
    # Note: For production, use a proper WSGI server.
    # The GEMINI_API_KEY should be set in the environment where this app runs.
    # Example: export GEMINI_API_KEY="YOUR_ACTUAL_API_KEY"
    if not os.environ.get("GEMINI_API_KEY"):
        print("Warning: GEMINI_API_KEY environment variable is not set.")
        print("The /generate-audio endpoint will fail without it.")
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
