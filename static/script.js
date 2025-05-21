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
        }
    };
}

// Handle transcription results
function handleTranscription(text, ayahNumber, wordIndex, hasError) {
    console.log('Transcription:', text, 'Ayah:', ayahNumber, 'Word:', wordIndex, 'Error:', hasError);
    
    // Only remove highlights if we have a new valid match
    if (ayahNumber && wordIndex !== undefined) {
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
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        
        // Reset current position
        currentAyah = null;
        currentWord = null;
        
        // Initialize WebSocket connection
        initializeWebSocket();

        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                // Send audio chunk to server
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(event.data);
                }
            }
        };

        mediaRecorder.start(100); // Collect data every 100ms
        isRecording = true;
        
        // Update UI
        document.querySelector('.record-btn').classList.add('recording');
        document.querySelector('.record-btn .text').textContent = 'Stop Recording';
        
        // Clear any existing highlights
        document.querySelectorAll('.word.active').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.ayah.active').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.word.error').forEach(el => el.classList.remove('error'));
        
    } catch (err) {
        console.error('Error starting recording:', err);
        alert('Error accessing microphone. Please ensure microphone permissions are granted.');
    }
}

// Stop recording function
function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
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