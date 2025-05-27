// Global variables for audio processing
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let ws = null;
let currentRecordingAyah = null;
let tooltipTimeout = null;
let currentReciter = 'mishary'; // Default reciter

const processingMessages = [
    "Whispering your ayah to the neural net",
    "Decoding divine frequencies",
    "Hold on... we're ironing your ghunna",
    "Just making sure your qalqala didn't jump off the page",
    "Fixing your ikhfaa with duct tape"
];

// Theme handling function
function handleThemeChange(isDark) {
    // Update body attribute
    document.body.setAttribute('data-theme', isDark ? 'dark' : 'light');
    
    // Update theme in localStorage
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
    
    // Update toggle buttons
    const themeToggle = document.getElementById('themeToggle');
    const mobileThemeToggle = document.getElementById('mobileThemeToggle');
    
    if (themeToggle) {
        themeToggle.textContent = isDark ? '☀️' : '🌙';
    }
    if (mobileThemeToggle) {
        mobileThemeToggle.textContent = isDark ? '☀️' : '🌙';
    }
    
    // Update renderer background if it exists (for landing page)
    if (typeof updateRendererBackground === 'function') {
        updateRendererBackground();
    }
    
    // Update colors if they exist (for landing page)
    if (typeof targetColor !== 'undefined' && typeof THREE !== 'undefined') {
        targetColor = new THREE.Color(isDark ? 0x1e88e5 : 0x42a5f5);
        if (typeof pointLight1 !== 'undefined' && typeof pointLight2 !== 'undefined') {
            pointLight1.color.setHex(isDark ? 0x1e88e5 : 0x42a5f5);
            pointLight2.color.setHex(isDark ? 0x42a5f5 : 0x90caf9);
        }
    }
}

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing recording functionality');
    
    // Add click listeners to all ayahs
    const ayahs = document.querySelectorAll('.ayah');
    console.log('Found ayahs:', ayahs.length);

    ayahs.forEach(ayah => {
        console.log('Adding click listener to ayah:', ayah);
        ayah.addEventListener('click', handleAyahClick);
    });

    // Root word tooltip functionality
    const tooltip = document.getElementById('root-tooltip');
    let activeWord = null;

    function hideTooltip() {
        if (tooltipTimeout) {
            clearTimeout(tooltipTimeout);
        }
        tooltip.classList.add('fade-out');
        setTimeout(() => {
            tooltip.classList.remove('show', 'fade-out');
            if (activeWord) {
                activeWord.classList.remove('word-highlight');
                activeWord = null;
            }
        }, 300); // Wait for fade animation to complete
    }

    document.querySelectorAll('.word').forEach(word => {
        word.addEventListener('click', (e) => {
            const root = e.currentTarget.getAttribute('data-root');
            const trans = e.currentTarget.getAttribute('data-trans');
            const translit = e.currentTarget.getAttribute('data-translit');
            
            if (root) {
                // Clear any existing timeout
                if (tooltipTimeout) {
                    clearTimeout(tooltipTimeout);
                }
                
                // Get word's position
                const rect = e.currentTarget.getBoundingClientRect();
                
                // Position tooltip above the word
                tooltip.style.left = `${rect.left + (rect.width / 2)}px`;
                tooltip.style.top = `${rect.top - 40}px`;
                tooltip.style.transform = 'translate(-50%, -100%)';
                
                // Show root word, translation and transliteration
                tooltip.innerHTML = `
                    <div class="tooltip-content">
                        <div class="root">Root: ${root}</div>
                        <div class="trans">${trans}</div>
                        <div class="translit">${translit}</div>
                    </div>
                `;
                tooltip.classList.remove('fade-out');
                tooltip.classList.add('show');
                
                // Highlight clicked word
                if (activeWord) {
                    activeWord.classList.remove('word-highlight');
                }
                e.currentTarget.classList.add('word-highlight');
                activeWord = e.currentTarget;

                // Set timeout to hide tooltip after 2 seconds
                tooltipTimeout = setTimeout(hideTooltip, 2000);
            }
        });
    });

    // Hide tooltip when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.word')) {
            hideTooltip();
        }
    });

    // Theme Toggle
    const themeToggle = document.getElementById('themeToggle');
    const mobileThemeToggle = document.getElementById('mobileThemeToggle');
    const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');
    
    // Set initial theme based on localStorage or system preference
    const savedTheme = localStorage.getItem('theme');
    const isDark = savedTheme === 'dark' || (!savedTheme && prefersDarkScheme.matches);
    handleThemeChange(isDark);

    // Theme toggle click handlers
    const toggleTheme = () => {
        const isDark = document.body.getAttribute('data-theme') === 'dark';
        handleThemeChange(!isDark);
    };

    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
    if (mobileThemeToggle) {
        mobileThemeToggle.addEventListener('click', toggleTheme);
    }

    // Listen for system theme changes
    prefersDarkScheme.addEventListener('change', (e) => {
        if (!localStorage.getItem('theme')) {
            handleThemeChange(e.matches);
        }
    });

    // Initialize ayah controls
    document.querySelectorAll('.ayah').forEach(ayah => {
        const playBtn = ayah.querySelector('.play-btn');
        const optionsBtn = ayah.querySelector('.options-btn');
        const optionsMenu = ayah.querySelector('.options-menu');
        const optionsContent = ayah.querySelector('.options-content');
        const audio = ayah.querySelector('.ayah-audio');
        const reciterSelect = ayah.querySelector('.reciter-select select');
        const ayahNumber = ayah.dataset.ayah;
        
        // Set initial reciter value
        reciterSelect.value = currentReciter;
        
        // Add mouseleave event to close options menu
        ayah.addEventListener('mouseleave', () => {
            optionsMenu.classList.remove('active');
        });
        
        // Play button functionality
        playBtn.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent ayah click handler
            
            const isPlaying = playBtn.classList.contains('playing');
            
            // Stop all other playing audio
            document.querySelectorAll('.ayah-audio').forEach(otherAudio => {
                if (otherAudio !== audio) {
                    otherAudio.pause();
                    otherAudio.currentTime = 0;
                }
            });
            document.querySelectorAll('.play-btn').forEach(btn => {
                if (btn !== playBtn) {
                    btn.classList.remove('playing');
                }
            });
            
            if (isPlaying) {
                audio.pause();
                playBtn.classList.remove('playing');
            } else {
                audio.src = `/reference-audio/${currentReciter}/${parseInt(ayahNumber) + 1}`;
                audio.play()
                    .then(() => {
                        playBtn.classList.add('playing');
                    })
                    .catch(error => {
                        console.error('Error playing audio:', error);
                        alert('Error playing audio. Please try again.');
                    });
            }
        });
        
        // Options menu functionality
        optionsBtn.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent ayah click handler
            
            // Close all other open menus
            document.querySelectorAll('.options-menu').forEach(menu => {
                if (menu !== optionsMenu) {
                    menu.classList.remove('active');
                }
            });
            
            optionsMenu.classList.toggle('active');
        });

        // Prevent clicks inside options content from closing the menu
        optionsContent.addEventListener('click', (e) => {
            e.stopPropagation();
        });

        // Handle reciter select clicks and changes
        reciterSelect.addEventListener('click', (e) => {
            e.stopPropagation();
        });
        
        // Handle reciter change
        reciterSelect.addEventListener('change', (e) => {
            e.stopPropagation();
            
            // Update global reciter
            currentReciter = e.target.value;
            
            // Update all other reciter selects
            document.querySelectorAll('.reciter-select select').forEach(select => {
                select.value = currentReciter;
            });
            
            // If this ayah is currently playing, update its source
            if (!audio.paused) {
                const currentTime = audio.currentTime;
                audio.src = `/reference-audio/${currentReciter}/${parseInt(ayahNumber) + 1}`;
                audio.currentTime = currentTime;
                audio.play()
                    .catch(error => {
                        console.error('Error playing audio:', error);
                        alert('Error playing audio. Please try again.');
                    });
            }
        });
        
        // Handle audio end
        audio.addEventListener('ended', () => {
            playBtn.classList.remove('playing');
        });
    });
    
    // Close options menu when clicking outside, but not when clicking inside options
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.options-content') && !e.target.closest('.options-btn')) {
            document.querySelectorAll('.options-menu').forEach(menu => {
                menu.classList.remove('active');
            });
        }
    });
});

// Handle ayah click
async function handleAyahClick(e) {
    console.log('handleAyahClick called');
    
    // Only prevent recording for specific interactive elements
    if (e.target.classList.contains('word') || 
        e.target.closest('.word') ||
        e.target.closest('.play-btn') ||
        e.target.closest('.options-btn') ||
        e.target.closest('.options-content')) {
        console.log('Clicked on word or control button, not starting recording');
        return;
    }
    
    e.preventDefault();
    e.stopPropagation();
    
    const ayah = e.currentTarget;
    console.log('Ayah clicked:', ayah.dataset.ayah, 'Current recording state:', isRecording);
    
    try {
        if (isRecording && currentRecordingAyah === ayah) {
            console.log('Stopping recording for current ayah');
            await stopRecording();
        } else {
            console.log('Starting recording');
            if (isRecording) {
                console.log('Stopping previous recording first');
                await stopRecording();
            }
            await startRecording(ayah);
        }
    } catch (err) {
        console.error('Error handling ayah click:', err);
        alert('Error with recording. Please ensure microphone permissions are granted.');
        await stopRecording();
    }
}

// Initialize WebSocket connection
function initializeWebSocket() {
    console.log('Setting up WebSocket connection...');
    ws = new WebSocket(`ws://${window.location.host}/ws`);
    
    ws.onopen = () => {
        console.log('WebSocket connection established');
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
    
    ws.onclose = () => {
        console.log('WebSocket connection closed');
    };
    
    ws.onmessage = function(event) {
        const response = JSON.parse(event.data);
        console.log('WebSocket message received:', response);
        if (response.type === 'transcription') {
            handleTranscription(response.text, response.ayah_number, response.word_index, response.has_error);
        } else if (response.type === 'error') {
            console.error('Server error:', response.message);
            alert('Error: ' + response.message);
        }
    };
}

// Handle transcription results
function handleTranscription(text, ayahNumber, wordIndex, hasError) {
    console.log('Handling transcription:', { text, ayahNumber, wordIndex, hasError });
    
    if (ayahNumber !== null && wordIndex !== null) {
        // Remove previous highlights
        document.querySelectorAll('.word.active').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.ayah.active').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.word.error').forEach(el => el.classList.remove('error'));
        
        // Highlight current ayah and word
        const ayah = document.querySelector(`.ayah[data-ayah="${ayahNumber}"]`);
        if (ayah) {
            ayah.classList.add('active');
            const words = ayah.querySelectorAll('.word');
            if (words[wordIndex]) {
                words[wordIndex].classList.add('active');
                if (hasError) {
                    words[wordIndex].classList.add('error');
                }
            }
        }
    }
}

// Start recording function
async function startRecording(ayah) {
    try {
        console.log('Starting recording for ayah:', ayah.dataset.ayah);
        
        // Initialize WebSocket first
        initializeWebSocket();
        
        // Wait for WebSocket connection to be established
        while (ws.readyState !== WebSocket.OPEN) {
            await new Promise(resolve => setTimeout(resolve, 100));
        }
        
        // Send target ayah number
        ws.send(JSON.stringify({
            target_ayah: ayah.dataset.ayah
        }));
        
        // Request microphone permission with specific constraints
        console.log('Requesting microphone access...');
        const stream = await navigator.mediaDevices.getUserMedia({
            audio: {
                channelCount: 1,
                sampleRate: 16000,
                echoCancellation: true,
                noiseSuppression: true
            }
        });
        console.log('Microphone access granted, creating MediaRecorder...');
        
        // Create MediaRecorder instance with specific MIME type
        const options = {
            mimeType: 'audio/webm;codecs=opus',
            audioBitsPerSecond: 16000
        };
        
        try {
            mediaRecorder = new MediaRecorder(stream, options);
            console.log('MediaRecorder created successfully');
        } catch (e) {
            console.warn('Failed to create MediaRecorder with preferred options, trying fallback...', e);
            // Fallback to default options
            mediaRecorder = new MediaRecorder(stream);
        }
        
        audioChunks = [];
        
        // Add recording class immediately for visual feedback
        ayah.classList.add('recording');
        currentRecordingAyah = ayah;
        
        // Handle data available event
        mediaRecorder.ondataavailable = async (event) => {
            console.log('Data available from MediaRecorder, size:', event.data.size);
            if (event.data.size > 0) {
                audioChunks.push(event.data);
                
                // Convert WebM chunk to WAV before sending
                const audioContext = new AudioContext();
                const arrayBuffer = await event.data.arrayBuffer();
                const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
                
                // Create WAV file
                const wavData = audioBufferToWav(audioBuffer);
                const wavBlob = new Blob([wavData], { type: 'audio/wav' });
                
                // Send WAV data through WebSocket
                if (ws && ws.readyState === WebSocket.OPEN) {
                    const buffer = await wavBlob.arrayBuffer();
                    console.log('Sending WAV audio chunk, size:', buffer.byteLength);
                    ws.send(buffer);
                } else {
                    console.warn('WebSocket not ready, chunk not sent');
                }
            }
        };

        // Function to convert AudioBuffer to WAV format
        function audioBufferToWav(buffer) {
            const numOfChan = buffer.numberOfChannels;
            const length = buffer.length * numOfChan * 2;
            const sampleRate = buffer.sampleRate;
            const data = new DataView(new ArrayBuffer(44 + length));
            
            // WAV Header
            writeString(data, 0, 'RIFF');
            data.setUint32(4, 36 + length, true);
            writeString(data, 8, 'WAVE');
            writeString(data, 12, 'fmt ');
            data.setUint32(16, 16, true);
            data.setUint16(20, 1, true);
            data.setUint16(22, numOfChan, true);
            data.setUint32(24, sampleRate, true);
            data.setUint32(28, sampleRate * numOfChan * 2, true);
            data.setUint16(32, numOfChan * 2, true);
            data.setUint16(34, 16, true);
            writeString(data, 36, 'data');
            data.setUint32(40, length, true);
            
            // Write audio data
            const offset = 44;
            const channelData = [];
            for (let i = 0; i < numOfChan; i++) {
                channelData.push(buffer.getChannelData(i));
            }
            
            let pos = 0;
            while (pos < buffer.length) {
                for (let i = 0; i < numOfChan; i++) {
                    const sample = Math.max(-1, Math.min(1, channelData[i][pos]));
                    data.setInt16(offset + (pos * numOfChan + i) * 2, sample < 0 ? sample * 0x8000 : sample * 0x7FFF, true);
                }
                pos++;
            }
            
            return data.buffer;
        }

        // Helper function to write strings to DataView
        function writeString(view, offset, string) {
            for (let i = 0; i < string.length; i++) {
                view.setUint8(offset + i, string.charCodeAt(i));
            }
        }

        // Handle recording stop
        mediaRecorder.onstop = async () => {
            console.log('MediaRecorder stopped');
            if (ws) {
                ws.close();
            }
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            console.log('Sending complete audio, size:', audioBlob.size);
            await sendAudioToServer(audioBlob);
        };

        // Handle recording errors
        mediaRecorder.onerror = (event) => {
            console.error('MediaRecorder error:', event.error);
            alert('Error during recording: ' + event.error.message);
            stopRecording().catch(console.error);
        };

        // Start recording with smaller time slices for more frequent updates
        mediaRecorder.start(100);
        isRecording = true;
        console.log('Recording started successfully');
        
    } catch (err) {
        console.error('Error starting recording:', err);
        alert('Error accessing microphone. Please ensure microphone permissions are granted and try again.');
        // Clean up UI if there's an error
        if (currentRecordingAyah) {
            currentRecordingAyah.classList.remove('recording');
        }
        currentRecordingAyah = null;
        isRecording = false;
        throw err; // Re-throw to be handled by caller
    }
}

// Stop recording function
async function stopRecording() {
    console.log('Stopping recording');
    
    try {
        if (isRecording && mediaRecorder) {
            // Stop MediaRecorder
            if (mediaRecorder.state !== 'inactive') {
                console.log('Stopping MediaRecorder');
                mediaRecorder.stop();
                mediaRecorder.stream.getTracks().forEach(track => {
                    track.stop();
                    console.log('Stopped audio track:', track.label);
                });
            }
            
            // Show processing message
            const randomMessage = processingMessages[Math.floor(Math.random() * processingMessages.length)];
            document.querySelector('.feedback-card:first-child').innerHTML = `
                <h3>Recorded Recitation</h3>
                <p class="processing-message">${randomMessage}<span class="dots"></span></p>
            `;
            document.querySelector('.feedback-card:last-child').innerHTML = `
                <h3>Tajweed Feedback</h3>
                <p class="processing-message">Analyzing your recitation<span class="dots"></span></p>
            `;
            
            // Close WebSocket connection
            if (ws) {
                console.log('Closing WebSocket connection');
                ws.close();
                ws = null;
            }
            
            // Remove recording UI feedback
            if (currentRecordingAyah) {
                console.log('Removing recording UI from ayah:', currentRecordingAyah.dataset.ayah);
                currentRecordingAyah.classList.remove('recording');
                currentRecordingAyah = null;
            }
            
            isRecording = false;
            mediaRecorder = null;
            console.log('Recording stopped successfully');
        }
    } catch (err) {
        console.error('Error stopping recording:', err);
        // Clean up state even if there's an error
        isRecording = false;
        mediaRecorder = null;
        ws = null;
        if (currentRecordingAyah) {
            currentRecordingAyah.classList.remove('recording');
            currentRecordingAyah = null;
        }
        throw err; // Re-throw to be handled by caller
    }
}

// Function to highlight active ayah and word
function highlightAyah(ayahNumber, word = null) {
    // Remove previous highlights
    document.querySelectorAll('.ayah.active').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.word.active').forEach(el => el.classList.remove('active'));
    
    // Highlight new ayah
    const ayah = document.querySelector(`.ayah[data-ayah="${ayahNumber}"]`);
    if (ayah) {
        ayah.classList.add('active');
        
        // Scroll to ayah smoothly
        ayah.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        // Highlight specific word if provided
        if (word) {
            const wordEl = ayah.querySelector(`.word[data-word="${word}"]`);
            if (wordEl) {
                wordEl.classList.add('active');
            }
        }
    }
}

// Send audio to server for analysis
async function sendAudioToServer(audioBlob) {
    console.log('Sending audio to server');
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.wav');

    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();
        console.log('Server response:', result);
        
        if (result.success) {
            const feedbackHtml = result.feedback.map(message => {
                let messageClass = 'feedback-message ';
                let icon = '';
                
                if (message.startsWith('✅')) {
                    messageClass += 'feedback-success';
                    icon = '✅';
                } else if (message.startsWith('⚠️')) {
                    messageClass += 'feedback-warning';
                    icon = '⚠️';
                } else if (message.startsWith('ℹ️')) {
                    messageClass += 'feedback-info';
                    icon = 'ℹ️';
                } else {
                    messageClass += 'feedback-error';
                    icon = '❌';
                }
                
                return `
                    <div class="${messageClass}">
                        <span class="feedback-icon">${icon}</span>
                        <span>${message.replace(/[✅⚠️ℹ️❌]/g, '').trim()}</span>
                    </div>
                `;
            }).join('');
            
            document.getElementById('feedback').innerHTML = `
                <div class="feedback-section">
                    <div class="feedback-card">
                        <h3>Recorded Recitation</h3>
                        <p dir="rtl" class="arabic">${result.transcription}</p>
                    </div>
                    <div class="feedback-card">
                        <h3>Tajweed Feedback</h3>
                        <div class="feedback-messages">
                            ${feedbackHtml}
                        </div>
                    </div>
                </div>
            `;
        } else {
            document.getElementById('feedback').innerHTML = `
                <div class="feedback-section">
                    <div class="feedback-card">
                        <div class="feedback-message feedback-error">
                            <span class="feedback-icon">❌</span>
                            <span>Error: ${result.error}</span>
                        </div>
                    </div>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error sending audio:', error);
        document.getElementById('feedback').innerHTML = `
            <div class="feedback-section">
                <div class="feedback-card">
                    <div class="feedback-message feedback-error">
                        <span class="feedback-icon">❌</span>
                        <span>Error sending recording to server</span>
                    </div>
                </div>
            </div>
        `;
    }
}

// Show toast message function
function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.remove();
    }, 3000);
} 