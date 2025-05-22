import pytest
import os
from unittest.mock import patch, MagicMock
import io

# Add the project root to the Python path for imports if necessary,
# or ensure app can be imported. For simplicity, we assume app.py is in root.
# This might require adjustment depending on how the app is structured for testing.
# For now, let's assume 'app' can be imported if tests are run from root.
from app import app as flask_app # Assuming your Flask app instance is named 'app' in app.py

@pytest.fixture
def app():
    # Flask app configuration for testing
    flask_app.config.update({
        "TESTING": True,
    })
    # You can also set up mock environment variables here if needed globally for tests
    # For example: os.environ['GEMINI_API_KEY'] = 'fake_test_key'
    yield flask_app
    # Clean up (if any) after tests
    # if 'GEMINI_API_KEY' in os.environ and os.environ['GEMINI_API_KEY'] == 'fake_test_key':
    #     del os.environ['GEMINI_API_KEY']


@pytest.fixture
def client(app):
    return app.test_client()

def test_index_route(client):
    '''Test the index route.'''
    response = client.get('/')
    assert response.status_code == 200
    assert b"<title>Text-to-Speech with Gemini</title>" in response.data # Check for some HTML content

@patch('app.genai.GenerativeModel') # Patch where it's used in app.py
@patch.dict(os.environ, {"GEMINI_API_KEY": "test_api_key"})
def test_generate_audio_success(mock_generative_model, client):
    '''Test successful audio generation.'''
    # Configure the mock
    mock_model_instance = MagicMock()
    mock_response = MagicMock()
    
    # Mocking the nested structure for response.candidates[0].content.parts[0].inline_data.data
    mock_part = MagicMock()
    mock_part.inline_data.data = b"dummy_pcm_audio_data" # Simulate PCM binary data
    mock_response.candidates = [MagicMock(content=MagicMock(parts=[mock_part]))]
    
    mock_model_instance.generate_content.return_value = mock_response
    mock_generative_model.return_value = mock_model_instance

    response = client.post('/generate-audio', json={
        "text": "Hello world",
        "voice_name": "Kore"
    })

    assert response.status_code == 200
    assert response.mimetype == 'audio/wav'
    assert len(response.data) > 0 # Check that some data is returned (WAV header + dummy data)
    
    # Verify genai.GenerativeModel was called with the correct model name
    mock_generative_model.assert_called_with(model_name="gemini-2.5-flash-preview-tts")
    
    # Verify generate_content was called
    mock_model_instance.generate_content.assert_called_once()
    args, kwargs = mock_model_instance.generate_content.call_args
    assert kwargs['contents'] == ["Hello world"]
    # Check if voice_name 'Kore' was used in the speech_config object passed directly to generate_content
    # This reflects the change in app.py where speech_config is no longer part of generation_config
    speech_config_arg = kwargs['speech_config'] 
    assert speech_config_arg.voice_config.prebuilt_voice_config.voice_name == "Kore"


def test_generate_audio_no_text(client):
    '''Test audio generation with no text provided.'''
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test_api_key"}): # Ensure API key for this path
        response = client.post('/generate-audio', json={"voice_name": "Kore"})
    assert response.status_code == 400
    assert response.json == {"error": "No text provided"}

@patch.dict(os.environ, {}, clear=True) # Ensure GEMINI_API_KEY is not set
def test_generate_audio_no_api_key(client):
    '''Test audio generation with no API key set.'''
    response = client.post('/generate-audio', json={"text": "Hello"})
    assert response.status_code == 500 # Or 401 if you made that change
    assert response.json == {"error": "GEMINI_API_KEY not set"}
    
@patch('app.genai.GenerativeModel')
@patch.dict(os.environ, {"GEMINI_API_KEY": "test_api_key"})
def test_generate_audio_gemini_api_error(mock_generative_model, client):
    '''Test audio generation when Gemini API call fails.'''
    mock_model_instance = MagicMock()
    mock_model_instance.generate_content.side_effect = Exception("Simulated Gemini API Error")
    mock_generative_model.return_value = mock_model_instance

    response = client.post('/generate-audio', json={"text": "Hello world"})
    
    assert response.status_code == 500 # Or specific error code if you have one for this
    assert "TTS generation failed: Simulated Gemini API Error" in response.json["error"]
    
@patch('app.genai.GenerativeModel')
@patch.dict(os.environ, {"GEMINI_API_KEY": "test_api_key"})
def test_generate_audio_specific_voice(mock_generative_model, client):
    '''Test audio generation with a specific voice name.'''
    mock_model_instance = MagicMock()
    mock_response = MagicMock()
    mock_part = MagicMock()
    mock_part.inline_data.data = b"dummy_pcm_audio_data"
    mock_response.candidates = [MagicMock(content=MagicMock(parts=[mock_part]))]
    mock_model_instance.generate_content.return_value = mock_response
    mock_generative_model.return_value = mock_model_instance

    client.post('/generate-audio', json={
        "text": "Hello from Puck",
        "voice_name": "Puck"
    })
    
    args, kwargs = mock_model_instance.generate_content.call_args
    # Check if voice_name 'Puck' was used in the speech_config object passed directly to generate_content
    speech_config_arg = kwargs['speech_config']
    assert speech_config_arg.voice_config.prebuilt_voice_config.voice_name == "Puck"
