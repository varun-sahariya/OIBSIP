document.addEventListener('DOMContentLoaded', () => {

    // ===================================================
    // Part 0: Tab Switching Logic
    // ===================================================
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

    // ===================================================
    // Part 1: Text-to-Speech Code
    // ===================================================
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

    // ===================================================
    // Part 2: Echo Bot Code (UPDATED FOR DAY 6)
    // ===================================================
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    const echoBotContainer = document.getElementById('echo-bot-container');
    const uploadStatus = document.getElementById('upload-status');
    const transcriptionDisplay = document.getElementById('transcription-display'); // Get the new display div
    
    let mediaRecorder;
    let audioChunks = [];
    let mediaStream; // To keep track of the microphone stream

    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        startBtn.addEventListener('click', async () => {
            try {
                mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
                startBtn.disabled = true;
                startBtn.classList.add('recording');
                stopBtn.disabled = false;
                echoBotContainer.innerHTML = '';
                uploadStatus.innerHTML = '';
                transcriptionDisplay.innerHTML = ''; // Clear old transcript
                audioChunks = [];
                mediaRecorder = new MediaRecorder(mediaStream);
                mediaRecorder.start();
                
                mediaRecorder.addEventListener('dataavailable', event => {
                    audioChunks.push(event.data);
                });

                // --- THIS IS THE UPDATED PART FOR DAY 6 ---
                // --- THIS IS THE UPDATED PART FOR DAY 7 ---
mediaRecorder.addEventListener('stop', () => {
    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
    
    // UI feedback
    uploadStatus.textContent = 'Echoing your voice...';
    uploadStatus.className = '';
    echoBotContainer.innerHTML = ''; // Clear previous audio player

    const formData = new FormData();
    formData.append('audio_file', audioBlob, 'user-recording.wav');

    // Send the audio to the NEW /tts/echo endpoint
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
        
        // Create an audio player for the NEW AI-generated audio
        const audioPlayer = document.createElement('audio');
        audioPlayer.controls = true;
        audioPlayer.src = data.audioUrl; // Use the URL from the response
        audioPlayer.autoplay = true; // Play it automatically
        echoBotContainer.appendChild(audioPlayer);
    })
    .catch(error => {
        console.error('Echo Error:', error);
        uploadStatus.textContent = `❌ Echo failed: ${error.message}`;
        uploadStatus.className = 'error';
    });
    
    // Stop the microphone stream
    if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop());
    }
});
            } catch (err) {
                console.error('Error accessing microphone:', err);
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