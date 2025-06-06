from flask import Flask, render_template, request, jsonify, Response
import os
from google import genai
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
    voice_name_to_use = data.get('voice_name', 'Kore')

    if not text_to_synthesize:
        return jsonify({"error": "No text provided"}), 400

    try:
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

        gen_stream = client.models.generate_content_stream(
            model="gemini-2.5-flash-preview-tts",
            contents=text_to_synthesize,
            config=config,
        )

        def generate():
            for chunk in gen_stream:
                if (
                    chunk.candidates
                    and chunk.candidates[0].content
                    and chunk.candidates[0].content.parts
                ):
                    part = chunk.candidates[0].content.parts[0]
                    if part.inline_data and part.inline_data.data:
                        yield part.inline_data.data

    except Exception as e:
        print(f"Error during Gemini API call: {e}")
        if "API key not valid" in str(e) or "PERMISSION_DENIED" in str(e):
            return jsonify({"error": f"TTS generation failed: Invalid API Key or insufficient permissions. Details: {str(e)}"}), 401
        return jsonify({"error": f"TTS generation failed: {str(e)}"}), 500

    return Response(generate(), mimetype='application/octet-stream')


@app.route('/stream-audio', methods=['POST'])
def stream_audio():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return jsonify({"error": "GEMINI_API_KEY not set"}), 500

    data = request.get_json()
    text_to_synthesize = data.get('text') if data else None
    voice_name_to_use = data.get('voice_name', 'Kore') if data else 'Kore'

    if not text_to_synthesize:
        return jsonify({"error": "No text provided"}), 400

    client = genai.Client(api_key=api_key)

    try:
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

        gen_stream = client.models.generate_content_stream(
            model="gemini-2.5-flash-preview-tts",
            contents=text_to_synthesize,
            config=config,
        )

        def generate():
            for chunk in gen_stream:
                if (
                    chunk.candidates
                    and chunk.candidates[0].content
                    and chunk.candidates[0].content.parts
                ):
                    part = chunk.candidates[0].content.parts[0]
                    if part.inline_data and part.inline_data.data:
                        yield part.inline_data.data

    except Exception as e:
        print(f"Error during Gemini API stream: {e}")
        if "API key not valid" in str(e) or "PERMISSION_DENIED" in str(e):
            return jsonify({"error": f"TTS generation failed: Invalid API Key or insufficient permissions. Details: {str(e)}"}), 401
        return jsonify({"error": f"TTS generation failed: {str(e)}"}), 500

    return Response(generate(), mimetype='application/octet-stream')


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
