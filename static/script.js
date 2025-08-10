document.addEventListener('DOMContentLoaded', () => {
    const tabs = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(item => item.classList.remove('active'));
            tabContents.forEach(item => item.classList.remove('active'));
            const target = document.querySelector(`#${tab.dataset.tab}`);
            tab.classList.add('active');
            target.classList.add('active');
        });
    });

    const generateBtn = document.getElementById('generate-btn');
    const textInput = document.getElementById('text-input');
    const audioContainer = document.getElementById('audio-container');
    generateBtn.addEventListener('click', async () => {
        const text = textInput.value.trim();
        if (text === '') { return alert('Please enter some text!'); }
        generateBtn.disabled = true;
        generateBtn.textContent = 'Generating...';
        audioContainer.innerHTML = '';
        try {
            const response = await fetch('/generate-audio', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: text }),
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Something went wrong.');
            }
            const data = await response.json();
            const audioPlayer = document.createElement('audio');
            audioPlayer.controls = true;
            audioPlayer.src = data.audioUrl;
            audioContainer.appendChild(audioPlayer);
            audioPlayer.play();
        } catch (error) {
            console.error('Error:', error);
            alert(`An error occurred: ${error.message}`);
        } finally {
            generateBtn.disabled = false;
            generateBtn.textContent = 'Generate Audio';
        }
    });

    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    const echoBotContainer = document.getElementById('echo-bot-container');
    const uploadStatus = document.getElementById('upload-status');
    const transcriptionDisplay = document.getElementById('transcription-display');
    let mediaRecorder;
    let audioChunks = [];
    let mediaStream;

    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        startBtn.addEventListener('click', async () => {
            try {
                mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
                startBtn.disabled = true;
                startBtn.classList.add('recording');
                stopBtn.disabled = false;
                echoBotContainer.innerHTML = '';
                uploadStatus.innerHTML = '';
                transcriptionDisplay.innerHTML = '';
                audioChunks = [];
                mediaRecorder = new MediaRecorder(mediaStream);
                mediaRecorder.start();
                mediaRecorder.addEventListener('dataavailable', event => {
                    audioChunks.push(event.data);
                });
                mediaRecorder.addEventListener('stop', () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    uploadStatus.textContent = 'Echoing your voice...';
                    uploadStatus.className = '';
                    const formData = new FormData();
                    formData.append('audio_file', audioBlob, 'user-recording.wav');
                    fetch('/tts/echo', {
                        method: 'POST',
                        body: formData,
                    })
                    .then(response => {
                        if (!response.ok) {
                            return response.json().then(err => { throw new Error(err.error || 'Echo failed') });
                        }
                        return response.json();
                    })
                    .then(data => {
                        console.log('Echo Success:', data);
                        uploadStatus.textContent = '✅ Echo successful!';
                        uploadStatus.className = 'success';

                        // NEW: Display the transcription from the response
                        transcriptionDisplay.textContent = `You said: "${data.transcription}"`;

                        // Play the new AI audio
                        const audioPlayer = document.createElement('audio');
                        audioPlayer.controls = true;
                        audioPlayer.src = data.audioUrl;
                        audioPlayer.autoplay = true;
                        echoBotContainer.appendChild(audioPlayer);
                    })
                    .catch(error => {
                        console.error('Echo Error:', error);
                        uploadStatus.textContent = `❌ Echo failed: ${error.message}`;
                        uploadStatus.className = 'error';
                    });
                    if (mediaStream) {
                        mediaStream.getTracks().forEach(track => track.stop());
                    }
                });
            } catch (err) {
                console.error('Error getting media stream:', err);
                alert('Could not access your microphone.');
            }
        });
        stopBtn.addEventListener('click', () => {
            if (mediaRecorder && mediaRecorder.state === 'recording') {
                mediaRecorder.stop();
                startBtn.disabled = false;
                startBtn.classList.remove('recording');
                stopBtn.disabled = true;
            }
        });
    } else {
        alert('Sorry, your browser does not support audio recording.');
        startBtn.disabled = true;
    }
});