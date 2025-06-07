document.addEventListener('DOMContentLoaded', () => {
    const textInput = document.getElementById('text-input');
    const srtFileInput = document.getElementById('srt-file-input');
    const generateButton = document.getElementById('generate-button');
    const voiceSelect = document.getElementById('voice-select');
    const messageArea = document.getElementById('message-area');

    generateButton.addEventListener('click', (event) => {
        event.preventDefault();

        const textValue = textInput.value.trim();
        const srtFile = srtFileInput.files[0];
        const selectedVoice = voiceSelect.value;
        let textToSynthesize = null;

        generateButton.disabled = true;
        messageArea.textContent = "Generating audio, please wait...";

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
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)({sampleRate: 24000});
        const processor = audioCtx.createScriptProcessor(4096, 1, 1);
        let queue = [];
        let leftover = new Uint8Array(0);

        processor.onaudioprocess = (e) => {
            const out = e.outputBuffer.getChannelData(0);
            for (let i = 0; i < out.length; i++) {
                if (queue.length) {
                    out[i] = queue.shift() / 32768;
                } else {
                    out[i] = 0;
                }
            }
        };

        processor.connect(audioCtx.destination);

        fetch('/stream-audio', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ text: text, voice_name: voiceName })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.error || `Server error: ${response.status}`); });
            }
            const reader = response.body.getReader();
            function read() {
                reader.read().then(({ done, value }) => {
                    if (done) {
                        processor.disconnect();
                        audioCtx.close();
                        generateButton.disabled = false;
                        messageArea.textContent = "";
                        return;
                    }
                    if (leftover.length) {
                        const merged = new Uint8Array(leftover.length + value.length);
                        merged.set(leftover);
                        merged.set(value, leftover.length);
                        value = merged;
                        leftover = new Uint8Array(0);
                    }
                    if (value.length % 2 === 1) {
                        leftover = value.slice(value.length - 1);
                        value = value.slice(0, value.length - 1);
                    }
                    const view = new DataView(value.buffer, value.byteOffset, value.byteLength);
                    for (let i = 0; i < value.length; i += 2) {
                        queue.push(view.getInt16(i, true));
                    }
                    read();
                }).catch(err => {
                    console.error('Stream error', err);
                    processor.disconnect();
                    audioCtx.close();
                    generateButton.disabled = false;
                    messageArea.textContent = `Error: ${err.message}`;
                });
            }
            read();
        })
        .catch(error => {
            console.error('Error generating audio:', error);
            messageArea.textContent = `Error: ${error.message}`;
            processor.disconnect();
            audioCtx.close();
            generateButton.disabled = false;
        });
    }
});
