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
        fetch('/stream-audio', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ "text": text, "voice_name": voiceName }), // Updated
        })
        .then(async response => {
            if (!response.ok) {
                try {
                    const err = await response.clone().json();
                    throw new Error(err.error || err.message || `Server error: ${response.status}`);
                } catch {
                    const msg = await response.text();
                    throw new Error(msg.trim() || `Server error: ${response.status}`);
                }
            }

            const reader = response.body.getReader();
            const chunks = [];
            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                if (value) chunks.push(value);
            }
            const wavBlob = pcmChunksToWav(chunks, 24000);
            const audioUrl = URL.createObjectURL(wavBlob);
            audioPlayer.src = audioUrl;
            audioPlayer.load();
            messageArea.textContent = "";
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

    function pcmChunksToWav(chunks, sampleRate) {
        let totalLength = 0;
        for (const c of chunks) {
            totalLength += c.length;
        }
        const buffer = new ArrayBuffer(44 + totalLength);
        const view = new DataView(buffer);
        let offset = 0;

        function writeString(s) {
            for (let i = 0; i < s.length; i++) {
                view.setUint8(offset++, s.charCodeAt(i));
            }
        }
        function writeUint32(v) { view.setUint32(offset, v, true); offset += 4; }
        function writeUint16(v) { view.setUint16(offset, v, true); offset += 2; }

        writeString('RIFF');
        writeUint32(36 + totalLength);
        writeString('WAVE');
        writeString('fmt ');
        writeUint32(16);
        writeUint16(1); // PCM
        writeUint16(1); // Mono
        writeUint32(sampleRate);
        writeUint32(sampleRate * 2);
        writeUint16(2);
        writeUint16(16);
        writeString('data');
        writeUint32(totalLength);

        for (const chunk of chunks) {
            new Uint8Array(buffer, offset).set(chunk);
            offset += chunk.length;
        }

        return new Blob([buffer], { type: 'audio/wav' });
    }
});
