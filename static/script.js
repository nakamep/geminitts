document.addEventListener('DOMContentLoaded', () => {
    const textInput = document.getElementById('text-input');
    const srtFileInput = document.getElementById('srt-file-input');
    const generateButton = document.getElementById('generate-button');
    const audioPlayer = document.getElementById('audio-player');
    const voiceSelect = document.getElementById('voice-select'); // New
    const messageArea = document.getElementById('message-area'); // New

    generateButton.addEventListener('click', (event) => {
        event.preventDefault();

        const textValue = textInput.value.trim();
        const srtFile = srtFileInput.files[0];
        const selectedVoice = voiceSelect.value; // New
        let textToSynthesize = null;

        // Loading state
        generateButton.disabled = true;
        messageArea.textContent = "Generating audio, please wait...";
        audioPlayer.src = ''; // Clear previous audio

        if (textValue) {
            textToSynthesize = textValue;
            sendDataToBackend(textToSynthesize, selectedVoice);
        } else if (srtFile) {
            const reader = new FileReader();
            reader.onload = () => {
                textToSynthesize = reader.result;
                sendDataToBackend(textToSynthesize, selectedVoice);
            };
            reader.onerror = () => {
                messageArea.textContent = "Error reading SRT file.";
                generateButton.disabled = false;
            }
            reader.readAsText(srtFile);
        } else {
            messageArea.textContent = "Please enter text or select an SRT file.";
            generateButton.disabled = false;
        }
    });

    function sendDataToBackend(text, voiceName) {
        fetch('/generate-audio', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ "text": text, "voice_name": voiceName }), // Updated
        })
        .then(response => {
            if (response.ok) {
                return response.blob();
            }
            // Try to parse JSON error response from backend first
            return response.clone().json().then(err => {
                throw new Error(err.error || err.message || `Server error: ${response.status}`);
            }).catch(() => {
                // Fallback: attempt to read plain text from the response
                return response.text().then(text => {
                    const msg = text.trim();
                    if (msg) {
                        throw new Error(msg);
                    }
                    throw new Error(`Server error: ${response.status}. Could not parse error details.`);
                });
            });
        })
        .then(blob => {
            const audioUrl = URL.createObjectURL(blob);
            audioPlayer.src = audioUrl;
            audioPlayer.load();
            messageArea.textContent = ""; // Clear message area on success
            // audioPlayer.play(); // Optional: play audio automatically
        })
        .catch(error => {
            console.error("Error generating audio:", error);
            messageArea.textContent = `Error: ${error.message}`;
            audioPlayer.src = ''; // Clear audio player on error
        })
        .finally(() => {
            generateButton.disabled = false; // Re-enable button
        });
    }
});
