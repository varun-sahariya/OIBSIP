document.addEventListener('DOMContentLoaded', () => {
    const recordBtn = document.getElementById('record-btn');
    const endBtn = document.getElementById('end-btn');
    const statusEl = document.getElementById('status');
    const chatHistory = document.getElementById('chat-history');
    const audioPlayerContainer = document.getElementById('audio-player');

    const params = new URLSearchParams(window.location.search);
    let sessionId = params.get('session_id');
    if (!sessionId) {
        sessionId = crypto.randomUUID();
        const u = new URL(window.location);
        u.searchParams.set('session_id', sessionId);
        window.history.replaceState({}, '', u);
    }

    let mediaRecorder = null;
    let mediaStream = null;
    let audioChunks = [];
    let isRecording = false;

    function appendMessage(sender, text) {
        const d = document.createElement('div');
        d.className = `chat-message ${sender}`;
        d.innerHTML = `<strong>${sender === 'you' ? 'You' : 'AI'}:</strong> ${text}`;
        chatHistory.appendChild(d);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    function updateStatus(text, type = 'info') {
        statusEl.textContent = text;
        statusEl.className = type === 'listening' ? 'status-listening' : (type === 'error' ? 'status-error' : '');
    }

    function setUIState(state) {
        if (state === 'recording') {
            recordBtn.disabled = false;
            endBtn.disabled = false;
            recordBtn.classList.add('recording');
        } else if (state === 'processing') {
            recordBtn.disabled = true;
            endBtn.disabled = false;
            recordBtn.classList.remove('recording');
        } else {
            // idle
            recordBtn.disabled = false;
            endBtn.disabled = true;
            recordBtn.classList.remove('recording');
        }
    }

    function playAudio(url, onEnded) {
        audioPlayerContainer.innerHTML = '';
        const player = document.createElement('audio');
        player.src = url;
        player.autoplay = true;
        audioPlayerContainer.appendChild(player);
        if (onEnded) player.addEventListener('ended', onEnded);
    }

    function playFallbackAudio() {
        updateStatus('Playing error message...', 'error');
        setUIState('processing');
        fetch('/generate-fallback-audio', { method: 'POST' })
            .then(res => res.ok ? res.json() : Promise.reject('Failed to get fallback audio'))
            .then(data => playAudio(data.audioUrl, () => setUIState('idle')))
            .catch(err => {
                console.error("CRITICAL: Could not play fallback audio.", err);
                updateStatus('❌ A critical error occurred. Please refresh.', 'error');
                setUIState('idle');
            });
    }

    async function startRecording() {
        if (isRecording) return;
        try {
            mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
            isRecording = true;
            setUIState('recording');
            updateStatus('Listening...', 'listening');

            audioChunks = [];
            mediaRecorder = new MediaRecorder(mediaStream);
            mediaRecorder.ondataavailable = e => e.data && e.data.size && audioChunks.push(e.data);

            mediaRecorder.onstop = async () => {
                mediaStream && mediaStream.getTracks().forEach(t => t.stop());
                setUIState('processing');

                // Nothing captured?
                const blob = new Blob(audioChunks, { type: 'audio/wav' });
                if (!blob || blob.size === 0) {
                    updateStatus('No speech detected. Try again.', 'error');
                    setUIState('idle');
                    isRecording = false;
                    return;
                }

                updateStatus('Thinking...');
                const formData = new FormData();
                formData.append('audio_file', blob, 'user-recording.wav');

                try {
                    const resp = await fetch(`/agent/chat/${sessionId}`, { method: 'POST', body: formData });
                    const data = await resp.json();

                    if (!resp.ok) {
                        if (data.error_code) playFallbackAudio();
                        else throw new Error(data.error || 'Unknown server error');
                        return;
                    }

                    if (data.no_speech) {
                        updateStatus('No speech detected. Try again.', 'error');
                        setUIState('idle');
                        return;
                    }

                    appendMessage('you', data.user_transcript || '');
                    appendMessage('ai', data.llm_response || '');
                    if (data.audioUrl) {
                        playAudio(data.audioUrl, () => {
                            // auto-restart listening after the bot finishes
                            startRecording();
                        });
                    } else {
                        updateStatus('No audio returned from TTS.', 'error');
                        setUIState('idle');
                    }
                } catch (err) {
                    console.error('Chat pipeline error:', err);
                    updateStatus(`❌ Error: ${err.message}`, 'error');
                    setUIState('idle');
                } finally {
                    isRecording = false;
                }
            };

            mediaRecorder.start();
        } catch (err) {
            console.error('Microphone access error:', err);
            updateStatus('❌ Error: Could not access microphone.', 'error');
            setUIState('idle');
        }
    }

    function stopRecording() {
        if (mediaRecorder && isRecording) {
            isRecording = false;
            mediaRecorder.stop();
            updateStatus('Processing...', 'info');
        } else if (!isRecording) {
            // If user clicks when not recording, treat as no-op (prevents "no speech" error path)
            updateStatus('Click mic to start recording.', 'info');
        }
    }

    async function endConversation() {
        // Ensure recording is stopped
        if (mediaRecorder && isRecording) {
            isRecording = false;
            try { mediaRecorder.stop(); } catch {}
        }
        if (mediaStream) mediaStream.getTracks().forEach(t => t.stop());

        setUIState('processing');
        updateStatus('Ending conversation...', 'info');
        try {
            const resp = await fetch(`/agent/chat/${sessionId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ end_convo: true })
            });
            const data = await resp.json();
            if (data.error) throw new Error(data.error);
            appendMessage('ai', data.llm_response || 'Goodbye.');
            if (data.audioUrl) {
                playAudio(data.audioUrl, () => {
                    updateStatus('Conversation ended. Click mic to start again.');
                    setUIState('idle');
                });
            } else {
                updateStatus('Conversation ended. Click mic to start again.');
                setUIState('idle');
            }
        } catch (err) {
            console.error('End convo error:', err);
            updateStatus('❌ Failed to end conversation gracefully.', 'error');
            setUIState('idle');
        }
    }

    // Single toggle button behavior
    recordBtn.addEventListener('click', () => {
        if (isRecording) {
            stopRecording();
        } else {
            startRecording();
        }
    });

    endBtn.addEventListener('click', endConversation);

    setUIState('idle');
});
