class VoiceAssistantPro {
    constructor() {
        this.socket = null;
        this.isRecording = false;
        this.mediaStream = null;
        this.audioContext = null;
        this.workletNode = null;
        this.playbackContext = null;
        this.gainNode = null;
        this.audioQueue = [];
        this.isProcessingQueue = false;
        this.nextStartTime = 0;
        this.activeSourceNodes = [];
        this.currentPersona = 'default';
        this.apiKeys = {};
        this.isConfigured = false;
        
        this.initializeElements();
        this.setupEventListeners();
        this.checkStoredConfig(); // ✨ We'll use this to load keys from browser storage
    }

    initializeElements() {
        // Config elements
        this.configBtn = document.getElementById('configBtn');
        this.helpBtn = document.getElementById('helpBtn');
        this.configOverlay = document.getElementById('configOverlay');
        this.closeConfigBtn = document.getElementById('closeConfigBtn');
        this.cancelConfigBtn = document.getElementById('cancelConfigBtn');
        this.configForm = document.getElementById('configForm');
        
        // Control elements
        this.micBtn = document.getElementById('micBtn');
        this.micContainer = document.getElementById('micContainer');
        this.statusDisplay = document.getElementById('statusDisplay');
        this.stopBtn = document.getElementById('stopBtn');
        this.clearBtn = document.getElementById('clearBtn');
        this.volumeSlider = document.getElementById('volumeSlider');
        this.volumeDisplay = document.getElementById('volumeDisplay');
        
        // Chat elements
        this.chatHistory = document.getElementById('chatHistory');
        this.typingIndicator = document.getElementById('typingIndicator');
        
        // Status elements
        this.connectionDot = document.getElementById('connectionDot');
        this.connectionStatus = document.getElementById('connectionStatus');
        
        // Persona elements
        this.personaSelect = document.getElementById('personaSelect');
        this.personaPreview = document.getElementById('personaPreview');
        
        // API key inputs
        this.assemblyaiKeyInput = document.getElementById('assemblyaiKey');
        this.geminiKeyInput = document.getElementById('geminiKey');
        this.murfKeyInput = document.getElementById('murfKey');
        this.tavilyKeyInput = document.getElementById('tavilyKey');
        this.gnewsKeyInput = document.getElementById('gnewsKey');
    }

    setupEventListeners() {
        // Config modal events
        this.configBtn.addEventListener('click', () => this.openConfigModal());
        this.helpBtn.addEventListener('click', () => this.openConfigModal()); // Help button now opens config
        this.closeConfigBtn.addEventListener('click', () => this.closeConfigModal());
        this.cancelConfigBtn.addEventListener('click', () => this.closeConfigModal());
        this.configForm.addEventListener('submit', (e) => this.handleConfigSubmit(e));
        
        // Control events
        this.micBtn.addEventListener('click', () => this.toggleRecording());
        this.stopBtn.addEventListener('click', () => this.stopRecording());
        this.clearBtn.addEventListener('click', () => this.clearChat());
        this.volumeSlider.addEventListener('input', (e) => this.updateVolume(e));
        
        // Persona events
        this.personaSelect.addEventListener('change', (e) => this.changePersona(e));
        
        // Click outside modal to close
        this.configOverlay.addEventListener('click', (e) => {
            if (e.target === this.configOverlay) {
                this.closeConfigModal();
            }
        });
    }

    checkStoredConfig() {
        // This is still simplified because the backend handles keys, but it provides a better UI experience.
        this.isConfigured = true;
        this.initializeSocket();
        this.updateStatus('Ready to Chat');
        this.statusDisplay.textContent = 'Ready to Chat';
        this.micContainer.classList.remove('processing');
        document.querySelector('.conversation-subtitle').textContent = 'Click the mic and start speaking';
        document.querySelector('.message-content').textContent = 'Welcome! Click the microphone in the sidebar to start our conversation.';

        // ✨ Bonus: Load keys from localStorage into the form if they exist
        this.assemblyaiKeyInput.value = localStorage.getItem('assemblyaiKey') || '';
        this.geminiKeyInput.value = localStorage.getItem('geminiKey') || '';
        this.murfKeyInput.value = localStorage.getItem('murfKey') || '';
        this.tavilyKeyInput.value = localStorage.getItem('tavilyKey') || '';
        this.gnewsKeyInput.value = localStorage.getItem('gnewsKey') || '';
    }
    
    // ===============================================
    // ✨✨✨ START OF THE FIX ✨✨✨
    // ===============================================
    
    openConfigModal() {
        // Instead of an alert, we change the display style to show the modal
        this.configOverlay.style.display = 'flex';
    }

    closeConfigModal() {
        // We hide the modal by setting the display style back to 'none'
        this.configOverlay.style.display = 'none';
    }

    handleConfigSubmit(e) {
        // Prevent the page from reloading
        e.preventDefault();
        
        // ✨ Bonus: Save the keys to the browser's local storage
        // This makes it so the user doesn't have to re-enter them every time.
        localStorage.setItem('assemblyaiKey', this.assemblyaiKeyInput.value);
        localStorage.setItem('geminiKey', this.geminiKeyInput.value);
        localStorage.setItem('murfKey', this.murfKeyInput.value);
        localStorage.setItem('tavilyKey', this.tavilyKeyInput.value);
        localStorage.setItem('gnewsKey', this.gnewsKeyInput.value);
        
        console.log("API keys saved to browser's local storage.");
        alert("Configuration saved locally! Remember, the server uses the keys from the .env file.");
        
        // Close the modal after saving
        this.closeConfigModal();
    }
    
    // ===============================================
    // ✨✨✨ END OF THE FIX ✨✨✨
    // ===============================================

    initializeSocket() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.updateConnectionStatus('Connected', true);
            this.updateStatus('Ready to chat!');
            this.socket.emit('set_persona', { persona: this.currentPersona });
        });
        
        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
            this.updateConnectionStatus('Disconnected', false);
            this.updateStatus('Connection lost');
        });
        
        this.socket.on('turn_detected', (data) => {
            if (data.transcript) {
                this.updateStatus(`💬 "${data.transcript}"`, 'processing');
                this.micContainer.classList.add('processing');
            }
        });
        
        this.socket.on('turn_ended', (data) => {
            if (data.final_transcript) {
                this.addMessage(data.final_transcript, 'user');
                this.micContainer.classList.remove('processing');
                this.showTyping();
                this.stopAudio();
            }
        });
        
        this.socket.on('audio_chunk', (base64Audio) => {
            if (base64Audio) {
                const audioData = this.base64ToArrayBuffer(base64Audio);
                if (audioData.byteLength > 0) {
                    this.audioQueue.push(audioData);
                    if (!this.isProcessingQueue) {
                        this.processAudioQueue();
                    }
                }
            }
        });
        
        this.socket.on('llm_chunk', (data) => {
            this.hideTyping();
            this.updateAssistantMessage(data.text);
        });
        
        this.socket.on('llm_complete', () => {
            this.hideTyping();
        });
    }

    updateConnectionStatus(status, connected) {
        this.connectionStatus.textContent = status;
        this.connectionDot.className = `status-dot ${connected ? '' : 'disconnected'}`;
    }

    updateStatus(message, className = '') {
        this.statusDisplay.textContent = message;
        this.statusDisplay.className = `status-display ${className}`;
    }

    async toggleRecording() {
        if (this.isRecording) {
            this.stopRecording();
        } else {
            await this.startRecording();
        }
    }

    async startRecording() {
        if (this.isRecording) return;
        
        try {
            this.stopAudio();
            
            this.mediaStream = await navigator.mediaDevices.getUserMedia({ 
                audio: { sampleRate: 16000, channelCount: 1 } 
            });
            
            this.audioContext = new AudioContext({ sampleRate: 16000 });
            
            const workletBlob = new Blob([`
                class PCMProcessor extends AudioWorkletProcessor {
                    process(inputs) {
                        this.port.postMessage(inputs[0][0]);
                        return true;
                    }
                }
                registerProcessor('pcm-processor', PCMProcessor);
            `], { type: 'application/javascript' });
            
            const workletURL = URL.createObjectURL(workletBlob);
            await this.audioContext.audioWorklet.addModule(workletURL);
            
            const mediaStreamSource = this.audioContext.createMediaStreamSource(this.mediaStream);
            this.workletNode = new AudioWorkletNode(this.audioContext, 'pcm-processor');
            
            let audioBuffer = [];
            this.workletNode.port.onmessage = (event) => {
                audioBuffer.push(...event.data);
                if (audioBuffer.length >= 4096) {
                    const pcm16Data = new Int16Array(audioBuffer.length);
                    for (let i = 0; i < audioBuffer.length; i++) {
                        pcm16Data[i] = Math.max(-1, Math.min(1, audioBuffer[i])) * 0x7FFF;
                    }
                    this.socket.emit('stream', pcm16Data.buffer);
                    audioBuffer = [];
                }
            };
            
            mediaStreamSource.connect(this.workletNode);
            this.isRecording = true;
            this.micContainer.classList.add('listening');
            this.updateStatus('🎙️ Listening...', 'listening');
            this.stopBtn.disabled = false;
            
        } catch (error) {
            console.error('Error starting recording:', error);
            this.updateStatus('❌ Microphone access denied');
        }
    }

    stopRecording() {
        if (!this.isRecording) return;
        
        this.isRecording = false;
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
        }
        if (this.workletNode) {
            this.workletNode.disconnect();
        }
        if (this.audioContext) {
            this.audioContext.close();
        }
        
        this.micContainer.classList.remove('listening');
        this.updateStatus('Ready to chat!');
        this.stopBtn.disabled = true;
    }

    changePersona(e) {
        this.currentPersona = e.target.value;
        const personas = {
            default: "Hello! I'm your AI assistant, ready to help you with questions, tasks, and conversations in a professional and friendly manner.",
            pirate: "Ahoy matey! I be a salty pirate captain ready for adventure on the high seas! 🏴‍☠️",
            scientist: "Fascinating! I'm a brilliant scientist eager to explore the mysteries of the universe through experimentation! ⚗️",
            wizard: "By my ancient wisdom, I am a mystical wizard versed in the arcane arts and eternal knowledge! ✨",
            robot: "GREETINGS HUMAN. I AM A LOGICAL ROBOT UNIT DESIGNED TO PROVIDE OPTIMAL ASSISTANCE AND EFFICIENCY. BEEP BOOP! 🤖",
            chef: "Bonjour! I am a passionate master chef who lives and breathes the culinary arts! Magnifique! 👨‍🍳",
            detective: "Good day. I'm a sharp-eyed detective who notices every detail and solves mysteries with keen observation. 🔍"
        };
        
        this.personaPreview.textContent = personas[this.currentPersona];
        
        if (this.socket) {
            this.socket.emit('set_persona', { persona: this.currentPersona });
        }
    }

    updateVolume(e) {
        const volume = parseFloat(e.target.value);
        this.volumeDisplay.textContent = `${Math.round(volume * 100)}%`;
        if (this.gainNode) {
            this.gainNode.gain.value = volume;
        }
    }

    clearChat() {
        this.chatHistory.innerHTML = `
            <div class="message assistant">
                <div class="message-avatar">🤖</div>
                <div class="message-content">
                    Welcome back! I'm ready to help you with anything you need.
                </div>
            </div>
        `;
    }

    addMessage(text, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = type === 'user' ? '👤' : '🤖';
        
        const content = document.createElement('div');
        content.className = 'message-content';
        content.textContent = text;
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);
        this.chatHistory.appendChild(messageDiv);
        this.chatHistory.scrollTop = this.chatHistory.scrollHeight;
    }

    updateAssistantMessage(text) {
        let lastMessage = this.chatHistory.querySelector('.message.assistant:last-child .message-content');
        if (!lastMessage) {
            this.addMessage('', 'assistant');
            lastMessage = this.chatHistory.querySelector('.message.assistant:last-child .message-content');
        }
        lastMessage.textContent += text;
        this.chatHistory.scrollTop = this.chatHistory.scrollHeight;
    }

    showTyping() {
        this.typingIndicator.classList.add('active');
    }

    hideTyping() {
        this.typingIndicator.classList.remove('active');
    }

    base64ToArrayBuffer(base64) {
        try {
            const binaryString = window.atob(base64);
            const len = binaryString.length;
            const bytes = new Uint8Array(len);
            for (let i = 0; i < len; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }
            return bytes.buffer;
        } catch (error) {
            console.error('Error decoding base64:', error);
            return new ArrayBuffer(0);
        }
    }

    async processAudioQueue() {
        if (this.isProcessingQueue || this.audioQueue.length === 0) return;
        
        this.isProcessingQueue = true;
        
        try {
            await this.initializePlaybackContext();
            const pcmData = this.audioQueue.shift();
            if (pcmData && pcmData.byteLength > 0) {
                await this.processAudioChunk(pcmData);
            }
        } catch (error) {
            console.error('Error processing audio queue:', error);
        } finally {
            this.isProcessingQueue = false;
            if (this.audioQueue.length > 0) {
                setTimeout(() => this.processAudioQueue(), 10);
            }
        }
    }

    async initializePlaybackContext() {
        if (!this.playbackContext || this.playbackContext.state === 'closed') {
            this.playbackContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: 44100 
            });
            
            this.gainNode = this.playbackContext.createGain();
            this.gainNode.gain.value = parseFloat(this.volumeSlider.value);
            this.gainNode.connect(this.playbackContext.destination);
            this.nextStartTime = 0;
        }
        
        if (this.playbackContext.state === 'suspended') {
            await this.playbackContext.resume();
        }
    }

    async processAudioChunk(pcmData) {
        try {
            const samples = pcmData.byteLength / 2;
            if (samples === 0) return;
            
            const audioBuffer = this.playbackContext.createBuffer(1, samples, 44100);
            const channelData = audioBuffer.getChannelData(0);
            
            const pcm16 = new Int16Array(pcmData);
            for (let i = 0; i < samples; i++) {
                channelData[i] = pcm16[i] / 32768;
            }
            
            const source = this.playbackContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(this.gainNode);
            
            const currentTime = this.playbackContext.currentTime;
            const startTime = (this.nextStartTime > currentTime) ? this.nextStartTime : currentTime;
            
            source.start(startTime);
            this.nextStartTime = startTime + audioBuffer.duration;
            this.activeSourceNodes.push(source);
            
            source.onended = () => {
                this.activeSourceNodes = this.activeSourceNodes.filter(s => s !== source);
                if (this.audioQueue.length === 0 && this.activeSourceNodes.length === 0) {
                    this.micContainer.classList.remove('speaking');
                    this.updateStatus(this.isRecording ? '🎙️ Listening...' : 'Ready to chat!');
                }
            };
            
            if (this.activeSourceNodes.length === 1) {
                this.micContainer.classList.add('speaking');
                this.updateStatus('🔊 AI is speaking...', 'speaking');
            }
            
        } catch (error) {
            console.error('Error processing audio chunk:', error);
        }
    }

    stopAudio() {
        if (this.playbackContext && this.playbackContext.state !== 'closed') {
            this.activeSourceNodes.forEach(source => {
                try {
                    if (source.buffer) source.stop();
                } catch (e) {
                    // Source may already be stopped
                }
            });
            this.playbackContext.close().catch(e => console.error('Error closing audio context:', e));
        }
        
        this.audioQueue = [];
        this.activeSourceNodes = [];
        this.nextStartTime = 0;
        this.isProcessingQueue = false;
        this.playbackContext = null;
        this.gainNode = null;
        this.micContainer.classList.remove('speaking');
    }
}

// Initialize the application when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new VoiceAssistantPro();
});