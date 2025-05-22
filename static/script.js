// Global variables for audio processing
let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let ws = null;
let currentAyah = null;
let currentWord = null;

// Initialize WebSocket connection
function initializeWebSocket() {
    ws = new WebSocket('ws://' + window.location.host + '/ws');
    ws.onmessage = function(event) {
        const response = JSON.parse(event.data);
        if (response.type === 'transcription') {
            handleTranscription(response.text, response.ayah_number, response.word_index, response.has_error);
        } else if (response.type === 'error') {
            console.error('Server error:', response.message);
        }
    };
    ws.onerror = function(error) {
        console.error('WebSocket error:', error);
    };
}

// Handle transcription results
function handleTranscription(text, ayahNumber, wordIndex, hasError) {
    console.log('Transcription:', text, 'Ayah:', ayahNumber, 'Word:', wordIndex, 'Error:', hasError);
    
    // Only remove highlights if we have a new valid match
    if (ayahNumber !== null && wordIndex !== null) {
        // Remove previous highlights
        if (currentAyah !== ayahNumber || currentWord !== wordIndex) {
            document.querySelectorAll('.word.active').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.ayah.active').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.word.error').forEach(el => el.classList.remove('error'));
        }
        
        // Highlight current ayah
        const ayah = document.querySelector(`.ayah[data-ayah="${ayahNumber}"]`);
        if (ayah) {
            ayah.classList.add('active');
            
            // Highlight current word
            const words = ayah.querySelectorAll('.word');
            if (words[wordIndex]) {
                words[wordIndex].classList.add('active');
                if (hasError) {
                    words[wordIndex].classList.add('error');
                }
                
                // Scroll the word into view if needed
                words[wordIndex].scrollIntoView({
                    behavior: 'smooth',
                    block: 'center'
                });
            }
        }
        
        // Update current position
        currentAyah = ayahNumber;
        currentWord = wordIndex;
    }
}

// Start recording function
async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                channelCount: 1,
                sampleRate: 16000
            } 
        });
        
        // Create audio context for processing
        const audioContext = new AudioContext({
            sampleRate: 16000
        });
        const source = audioContext.createMediaStreamSource(stream);
        
        // Create a buffer of reasonable size
        const bufferSize = 2048;  // Must be a power of 2
        const processor = audioContext.createScriptProcessor(bufferSize, 1, 1);
        
        source.connect(processor);
        processor.connect(audioContext.destination);
        
        // Reset current position
        currentAyah = null;
        currentWord = null;
        
        // Initialize WebSocket connection
        initializeWebSocket();
        
        // Process audio data
        processor.onaudioprocess = (e) => {
            if (ws && ws.readyState === WebSocket.OPEN && isRecording) {
                // Get raw audio data
                const inputData = e.inputBuffer.getChannelData(0);
                
                // Convert float32 to int16
                const int16Data = new Int16Array(inputData.length);
                for (let i = 0; i < inputData.length; i++) {
                    // Convert float32 to int16
                    const s = Math.max(-1, Math.min(1, inputData[i]));
                    int16Data[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
                }
                
                // Send the audio data
                try {
                    ws.send(int16Data.buffer);
                } catch (error) {
                    console.error('Error sending audio data:', error);
                }
            }
        };
        
        isRecording = true;
        
        // Update UI
        document.querySelector('.record-btn').classList.add('recording');
        document.querySelector('.record-btn .text').textContent = 'Stop Recording';
        
        // Clear any existing highlights
        document.querySelectorAll('.word.active').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.ayah.active').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.word.error').forEach(el => el.classList.remove('error'));
        
        // Store cleanup function
        window.audioCleanup = () => {
            if (processor && audioContext) {
                processor.disconnect();
                source.disconnect();
                stream.getTracks().forEach(track => track.stop());
                audioContext.close();
            }
        };
        
    } catch (err) {
        console.error('Error starting recording:', err);
        alert('Error accessing microphone. Please ensure microphone permissions are granted.');
    }
}

// Stop recording function
function stopRecording() {
    if (isRecording) {
        // Clean up audio processing
        if (window.audioCleanup) {
            window.audioCleanup();
        }
        
        isRecording = false;
        
        // Close WebSocket connection
        if (ws) {
            ws.close();
            ws = null;
        }
        
        // Update UI
        document.querySelector('.record-btn').classList.remove('recording');
        document.querySelector('.record-btn .text').textContent = 'Start Recording';
        
        // Reset current position
        currentAyah = null;
        currentWord = null;
    }
}

// Toggle recording
document.querySelector('.record-btn').addEventListener('click', () => {
    if (!isRecording) {
        startRecording();
    } else {
        stopRecording();
    }
}); 