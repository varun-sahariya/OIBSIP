document.addEventListener('DOMContentLoaded', () => {
    const recordBtn = document.getElementById('record-btn');
    const endBtn = document.getElementById('end-btn');
    const statusEl = document.getElementById('status');
    const chatHistory = document.getElementById('chat-history');
    const audioPlayerContainer = document.getElementById('audio-player');

    const sessionId = new URLSearchParams(window.location.search).get('session_id') || crypto.randomUUID();
    if (!new URLSearchParams(window.location.search).get('session_id')) {
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
        statusEl.className = `status-${type}`;
    }

    function setUIState(state) {
        recordBtn.disabled = state === 'processing';
        endBtn.disabled = state === 'idle';
        if (state === 'recording') {
            recordBtn.classList.add('recording');
        } else {
            recordBtn.classList.remove('recording');
        }
    }

    function playAudio(url, onEndedCallback) {
        audioPlayerContainer.innerHTML = '';
        const player = document.createElement('audio');
        player.src = url;
        player.autoplay = true;
        audioPlayerContainer.appendChild(player);
        player.onended = onEndedCallback;
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
            mediaRecorder.ondataavailable = e => audioChunks.push(e.data);

            mediaRecorder.onstop = async () => {
                if (mediaStream) mediaStream.getTracks().forEach(track => track.stop());

                setUIState('processing');
                updateStatus('Thinking...');
                const formData = new FormData();
                formData.append('audio_file', new Blob(audioChunks, { type: 'audio/wav' }));

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

                    appendMessage('you', data.user_transcript);
                    appendMessage('ai', data.llm_response);
                    playAudio(data.audioUrl, startRecording);

                } catch (err) {
                    console.error('Chat pipeline error:', err);
                    updateStatus(`❌ Error: ${err.message}`, 'error');
                    setUIState('idle');
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
        }
    }

    async function endConversation() {
        isRecording = false;
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
        }
        if (mediaStream) {
            mediaStream.getTracks().forEach(track => track.stop());
        }

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
            appendMessage('ai', data.llm_response);
            playAudio(data.audioUrl, () => {
                updateStatus('Conversation ended. Click mic to start again.');
                setUIState('idle');
            });
        } catch (err) {
            console.error('End convo error:', err);
            updateStatus('❌ Failed to end conversation gracefully.', 'error');
            setUIState('idle');
        }
    }

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