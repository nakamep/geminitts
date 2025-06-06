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

@patch('app.genai.Client')  # Patch where it's used in app.py
@patch.dict(os.environ, {"GEMINI_API_KEY": "test_api_key"})
def test_generate_audio_success(mock_client_class, client):
    '''Test successful audio generation.'''
    # Configure the mock
    mock_client_instance = MagicMock()
    mock_response = MagicMock()
    
    # Mocking the nested structure for response.candidates[0].content.parts[0].inline_data.data
    mock_part = MagicMock()
    mock_part.inline_data.data = b"dummy_pcm_audio_data" # Simulate PCM binary data
    mock_response.candidates = [MagicMock(content=MagicMock(parts=[mock_part]))]

    mock_client_instance.models.generate_content.return_value = mock_response
    mock_client_class.return_value = mock_client_instance

    response = client.post('/generate-audio', json={
        "text": "Hello world",
        "voice_name": "Kore"
    })

    assert response.status_code == 200
    assert response.mimetype == 'audio/wav'
    assert len(response.data) > 0 # Check that some data is returned (WAV header + dummy data)
    
    # Verify genai.Client was instantiated with the API key
    mock_client_class.assert_called_with(api_key="test_api_key")
    
    # Verify generate_content was called
    mock_client_instance.models.generate_content.assert_called_once()
    args, kwargs = mock_client_instance.models.generate_content.call_args
    assert kwargs['model'] == "gemini-2.5-flash-preview-tts"
    assert kwargs['contents'] == "Hello world"
    # Check the arguments passed to generate_content, aligning with app.py's current structure
    config_arg = kwargs['config']
    assert config_arg.response_modalities == ["AUDIO"]
    assert config_arg.speech_config.voice_config.prebuilt_voice_config.voice_name == "Kore"


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
    assert response.status_code == 500 # Response should be 500 when GEMINI_API_KEY is not set
    assert response.json == {"error": "GEMINI_API_KEY not set"}
    
@patch('app.genai.Client')
@patch.dict(os.environ, {"GEMINI_API_KEY": "test_api_key"})
def test_generate_audio_gemini_api_error(mock_client_class, client):
    '''Test audio generation when Gemini API call fails.'''
    mock_client_instance = MagicMock()
    mock_client_instance.models.generate_content.side_effect = Exception("Simulated Gemini API Error")
    mock_client_class.return_value = mock_client_instance

    response = client.post('/generate-audio', json={"text": "Hello world"})
    
    assert response.status_code == 500 # Or specific error code if you have one for this
    assert "TTS generation failed: Simulated Gemini API Error" in response.json["error"]
    
@patch('app.genai.Client')
@patch.dict(os.environ, {"GEMINI_API_KEY": "test_api_key"})
def test_generate_audio_specific_voice(mock_client_class, client):
    '''Test audio generation with a specific voice name.'''
    mock_client_instance = MagicMock()
    mock_response = MagicMock()
    mock_part = MagicMock()
    mock_part.inline_data.data = b"dummy_pcm_audio_data"
    mock_response.candidates = [MagicMock(content=MagicMock(parts=[mock_part]))]
    mock_client_instance.models.generate_content.return_value = mock_response
    mock_client_class.return_value = mock_client_instance

    client.post('/generate-audio', json={
        "text": "Hello from Puck",
        "voice_name": "Puck"
    })
    
    args, kwargs = mock_client_instance.models.generate_content.call_args
    # Check the arguments passed to generate_content for the specific voice
    config_arg = kwargs['config']
    assert config_arg.response_modalities == ["AUDIO"]  # Should request audio
    assert config_arg.speech_config.voice_config.prebuilt_voice_config.voice_name == "Puck"

@patch('app.genai.Client')
@patch.dict(os.environ, {"GEMINI_API_KEY": "test_api_key"})
def test_generate_audio_default_voice(mock_client_class, client):
    '''Test audio generation defaults to Kore when no voice provided.'''
    mock_client_instance = MagicMock()
    mock_response = MagicMock()
    mock_part = MagicMock()
    mock_part.inline_data.data = b"dummy_pcm_audio_data"
    mock_response.candidates = [MagicMock(content=MagicMock(parts=[mock_part]))]
    mock_client_instance.models.generate_content.return_value = mock_response
    mock_client_class.return_value = mock_client_instance

    client.post('/generate-audio', json={"text": "sample"})

    args, kwargs = mock_client_instance.models.generate_content.call_args
    config_arg = kwargs['config']
    assert config_arg.speech_config.voice_config.prebuilt_voice_config.voice_name == "Kore"


@patch('app.send_file', side_effect=Exception("Send file error"))
@patch('app.genai.Client')
@patch.dict(os.environ, {"GEMINI_API_KEY": "test_api_key"})
def test_generate_audio_unhandled_exception(mock_client_class, mock_send_file, client):
    '''Ensure unhandled exceptions return JSON error responses.'''
    mock_client_instance = MagicMock()
    mock_response = MagicMock()
    mock_part = MagicMock()
    mock_part.inline_data.data = b"dummy_pcm_audio_data"
    mock_response.candidates = [MagicMock(content=MagicMock(parts=[mock_part]))]
    mock_client_instance.models.generate_content.return_value = mock_response
    mock_client_class.return_value = mock_client_instance

    response = client.post('/generate-audio', json={"text": "Hello"})

    assert response.status_code == 500
    assert response.json["error"].startswith("Unexpected server error: Send file error")


@patch('app.genai.Client')
@patch.dict(os.environ, {"GEMINI_API_KEY": "test_api_key"})
def test_stream_audio_success(mock_client_class, client):
    """Test streaming audio chunks are concatenated and returned."""
    mock_client_instance = MagicMock()

    chunk1 = MagicMock()
    chunk1.data = b"foo"
    chunk2 = MagicMock()
    chunk2.data = b"bar"
    mock_client_instance.models.generate_content_stream.return_value = iter([chunk1, chunk2])

    mock_client_class.return_value = mock_client_instance

    response = client.post('/stream-audio', json={"text": "Hello"})

    assert response.status_code == 200
    assert response.mimetype == 'application/octet-stream'
    assert response.data == b"foobar"


@patch.dict(os.environ, {"GEMINI_API_KEY": "test_api_key"})
def test_stream_audio_no_text(client):
    """Streaming endpoint should return 400 when no text provided."""
    response = client.post('/stream-audio', json={})
    assert response.status_code == 400
    assert response.json == {"error": "No text provided"}


@patch.dict(os.environ, {}, clear=True)
def test_stream_audio_no_api_key(client):
    """Streaming endpoint should error when API key missing."""
    response = client.post('/stream-audio', json={"text": "Hello"})
    assert response.status_code == 500
    assert response.json == {"error": "GEMINI_API_KEY not set"}
