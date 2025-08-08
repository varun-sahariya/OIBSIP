document.addEventListener('DOMContentLoaded', () => {
    // ===================================================
    // Tab Switching Logic
    // ===================================================
    const tabs = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active class from all tabs and contents
            tabs.forEach(item => item.classList.remove('active'));
            tabContents.forEach(item => item.classList.remove('active'));
            
            // Add active class to clicked tab and corresponding content
            const target = document.querySelector(`#${tab.dataset.tab}`);
            tab.classList.add('active');
            target.classList.add('active');
        });
    });

    // ===================================================
    // AI Voice Generator Logic
    // ===================================================
    const generateBtn = document.getElementById('generate-btn');
    const textInput = document.getElementById('text-input');
    const audioContainer = document.getElementById('audio-container');

    generateBtn.addEventListener('click', async () => {
        const text = textInput.value.trim();
        
        if (text === '') {
            return alert('Please enter some text!');
        }

        // Update UI for processing state
        generateBtn.disabled = true;
        generateBtn.innerHTML = 'Generating... <span class="loading"></span>';
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
            
            // Create and configure audio player
            const audioPlayer = document.createElement('audio');
            audioPlayer.controls = true;
            audioPlayer.src = data.audioUrl;
            audioPlayer.preload = 'auto';
            
            // Add event listeners for better user experience
            audioPlayer.addEventListener('loadstart', () => {
                console.log('Audio loading started');
            });
            
            audioPlayer.addEventListener('canplay', () => {
                console.log('Audio ready to play');
                audioPlayer.play().catch(e => console.log('Autoplay prevented:', e));
            });
            
            audioPlayer.addEventListener('error', (e) => {
                console.error('Audio error:', e);
                alert('Error loading audio. Please try again.');
            });

            audioContainer.appendChild(audioPlayer);

        } catch (error) {
            console.error('Error:', error);
            alert(`An error occurred: ${error.message}`);
        } finally {
            generateBtn.disabled = false;
            generateBtn.textContent = 'Generate Audio';
        }
    });

    // ===================================================
    // Echo Bot Logic
    // ===================================================
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    const echoBotContainer = document.getElementById('echo-bot-container');
    const uploadStatus = document.getElementById('upload-status');
    
    let mediaRecorder;
    let audioChunks = [];
    let mediaStream;

    // Check if browser supports audio recording
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        
        startBtn.addEventListener('click', async () => {
            try {
                // Request microphone access
                mediaStream = await navigator.mediaDevices.getUserMedia({ 
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        sampleRate: 44100,
                    }
                });

                // Update UI for recording state
                startBtn.disabled = true;
                startBtn.classList.add('recording');
                stopBtn.disabled = false;
                echoBotContainer.innerHTML = '';
                uploadStatus.innerHTML = '';
                uploadStatus.className = '';
                audioChunks = [];

                // Initialize MediaRecorder
                mediaRecorder = new MediaRecorder(mediaStream, {
                    mimeType: 'audio/webm;codecs=opus'
                });

                // Start recording
                mediaRecorder.start();
                
                // Update status
                uploadStatus.textContent = '🎤 Recording... Click stop when finished';
                uploadStatus.className = 'processing';

                // Handle data collection
                mediaRecorder.addEventListener('dataavailable', event => {
                    if (event.data.size > 0) {
                        audioChunks.push(event.data);
                    }
                });

                // Handle recording stop
                mediaRecorder.addEventListener('stop', async () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    
                    // Update UI for processing
                    uploadStatus.textContent = '🔄 Processing your voice...';
                    uploadStatus.className = 'processing';
                    echoBotContainer.innerHTML = '';

                    // Prepare form data
                    const formData = new FormData();
                    formData.append('audio_file', audioBlob, 'user-recording.wav');

                    try {
                        // Send audio to server for processing
                        const response = await fetch('/tts/echo', {
                            method: 'POST',
                            body: formData,
                        });

                        if (!response.ok) {
                            const errorData = await response.json();
                            throw new Error(errorData.error || 'Echo processing failed');
                        }

                        const data = await response.json();
                        console.log('Echo Success:', data);
                        
                        // Update status
                        uploadStatus.textContent = '✅ Echo successful!';
                        uploadStatus.className = 'success';
                        
                        // Display transcription if available
                        if (data.transcription) {
                            const transcriptionDiv = document.createElement('div');
                            transcriptionDiv.style.marginBottom = '1rem';
                            transcriptionDiv.style.padding = '0.75rem';
                            transcriptionDiv.style.backgroundColor = 'var(--bg-color)';
                            transcriptionDiv.style.borderRadius = '8px';
                            transcriptionDiv.style.fontSize = '0.9rem';
                            transcriptionDiv.style.color = 'var(--text-muted-color)';
                            transcriptionDiv.innerHTML = `<strong>Transcription:</strong> "${data.transcription}"`;
                            echoBotContainer.appendChild(transcriptionDiv);
                        }
                        
                        // Create audio player for AI-generated response
                        const audioPlayer = document.createElement('audio');
                        audioPlayer.controls = true;
                        audioPlayer.src = data.audioUrl;
                        audioPlayer.preload = 'auto';
                        
                        // Add event listeners
                        audioPlayer.addEventListener('canplay', () => {
                            audioPlayer.play().catch(e => console.log('Autoplay prevented:', e));
                        });
                        
                        audioPlayer.addEventListener('error', (e) => {
                            console.error('Audio playback error:', e);
                            uploadStatus.textContent = '❌ Error playing generated audio';
                            uploadStatus.className = 'error';
                        });

                        echoBotContainer.appendChild(audioPlayer);

                    } catch (error) {
                        console.error('Echo Error:', error);
                        uploadStatus.textContent = `❌ Echo failed: ${error.message}`;
                        uploadStatus.className = 'error';
                    }
                    
                    // Clean up microphone stream
                    if (mediaStream) {
                        mediaStream.getTracks().forEach(track => track.stop());
                    }
                });

            } catch (err) {
                console.error('Error accessing microphone:', err);
                alert('Could not access your microphone. Please check permissions and try again.');
                
                // Reset button states
                startBtn.disabled = false;
                startBtn.classList.remove('recording');
                stopBtn.disabled = true;
            }
        });

        stopBtn.addEventListener('click', () => {
            if (mediaRecorder && mediaRecorder.state === 'recording') {
                mediaRecorder.stop();
                
                // Update UI
                startBtn.disabled = false;
                startBtn.classList.remove('recording');
                stopBtn.disabled = true;
                
                uploadStatus.textContent = '⏹️ Recording stopped. Processing...';
                uploadStatus.className = 'processing';
            }
        });

    } else {
        // Browser doesn't support audio recording
        alert('Sorry, your browser does not support audio recording.');
        startBtn.disabled = true;
        stopBtn.disabled = true;
        uploadStatus.textContent = '❌ Audio recording not supported in this browser';
        uploadStatus.className = 'error';
    }

    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
        if (mediaStream) {
            mediaStream.getTracks().forEach(track => track.stop());
        }
    });
});
