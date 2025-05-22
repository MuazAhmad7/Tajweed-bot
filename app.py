from flask import Flask, render_template, request, jsonify, send_file
import os
import whisper
from pathlib import Path
from utils.tajweed_checker import analyze_ayah, get_formatted_feedback
from flask_sock import Sock
import tempfile
import numpy as np
import torch
from utils.text_matcher import match_ayah_and_word
import wave
import json
import shutil

app = Flask(__name__)
sock = Sock(app)

# Configure upload folder
UPLOAD_FOLDER = Path('recordings')
UPLOAD_FOLDER.mkdir(exist_ok=True)

# Create a temporary directory for audio processing in our project folder
TEMP_DIR = Path('temp_audio')
TEMP_DIR.mkdir(exist_ok=True)

# Initialize Whisper model
model = whisper.load_model("base")

# Store the latest recording path
latest_recording = None

# Fatiha verses with their word-by-word text
FATIHA_VERSES = {
    0: ["بِسْمِ", "ٱللَّهِ", "ٱلرَّحْمَٰنِ", "ٱلرَّحِيمِ"],
    1: ["ٱلْحَمْدُ", "لِلَّهِ", "رَبِّ", "ٱلْعَٰلَمِينَ"],
    2: ["ٱلرَّحْمَٰنِ", "ٱلرَّحِيمِ"],
    3: ["مَٰلِكِ", "يَوْمِ", "ٱلدِّينِ"],
    4: ["إِيَّاكَ", "نَعْبُدُ", "وَإِيَّاكَ", "نَسْتَعِينُ"],
    5: ["ٱهْدِنَا", "ٱلصِّرَٰطَ", "ٱلْمُسْتَقِيمَ"],
    6: ["صِرَٰطَ", "ٱلَّذِينَ", "أَنْعَمْتَ", "عَلَيْهِمْ", "غَيْرِ", "ٱلْمَغْضُوبِ", "عَلَيْهِمْ", "وَلَا", "ٱلضَّآلِّينَ"]
}

@app.route('/')
def index():
    return render_template('landing.html')

@app.route('/demo')
def demo():
    return render_template('index.html')

@sock.route('/ws')
def handle_websocket(ws):
    print("WebSocket connection established")
    # Create a unique temporary directory for this session
    session_dir = TEMP_DIR / str(hash(ws))
    print(f"Creating temporary directory: {session_dir}")
    session_dir.mkdir(exist_ok=True, parents=True)
    chunk_counter = 0
    global latest_recording
    
    try:
        while True:
            try:
                # Receive audio chunk
                print(f"Waiting for audio chunk {chunk_counter}")
                audio_data = ws.receive()
                
                # Validate audio data
                if not isinstance(audio_data, bytes):
                    print(f"Invalid audio data type: {type(audio_data)}")
                    ws.send(json.dumps({
                        'type': 'error',
                        'message': 'Invalid audio data format'
                    }))
                    continue
                    
                if not audio_data or len(audio_data) == 0:
                    print("Empty audio data received")
                    continue
                
                print(f"Received audio chunk of size: {len(audio_data)} bytes")
                
                # Convert bytes to numpy array of int16
                try:
                    # Ensure the buffer size is even (required for int16)
                    if len(audio_data) % 2 != 0:
                        audio_data = audio_data[:-1]
                    
                    audio_np = np.frombuffer(audio_data, dtype=np.int16)
                    if len(audio_np) == 0:
                        print("Empty audio data after conversion")
                        continue
                        
                    print(f"Converted to numpy array of size: {len(audio_np)}")
                except Exception as e:
                    print(f"Error converting audio data: {e}")
                    continue
                
                # Save audio chunk to temporary WAV file
                temp_wav = session_dir / f'chunk_{chunk_counter}.wav'
                print(f"Saving audio to: {temp_wav}")
                latest_recording = temp_wav
                
                try:
                    with wave.open(str(temp_wav), 'wb') as wf:
                        wf.setnchannels(1)  # Mono
                        wf.setsampwidth(2)  # 16-bit
                        wf.setframerate(16000)  # 16kHz
                        wf.writeframes(audio_np.tobytes())
                        
                except Exception as wave_error:
                    print(f"Error writing WAV file: {wave_error}")
                    ws.send(json.dumps({
                        'type': 'error',
                        'message': f'Error saving audio: {str(wave_error)}'
                    }))
                    continue
                
                if not temp_wav.exists():
                    error_msg = f"Failed to create temporary file: {temp_wav}"
                    print(error_msg)
                    ws.send(json.dumps({
                        'type': 'error',
                        'message': error_msg
                    }))
                    continue
                
                print(f"Successfully saved audio chunk to: {temp_wav}")
                
                try:
                    # Load and check if the audio file is valid
                    with wave.open(str(temp_wav), 'rb') as wf:
                        if wf.getnframes() == 0:
                            print("Empty audio file")
                            continue
                        print(f"Audio file contains {wf.getnframes()} frames")
                except Exception as e:
                    print(f"Invalid audio file: {e}")
                    continue
                
                # Get absolute path for whisper
                abs_temp_wav = temp_wav.absolute()
                print(f"Using absolute path for transcription: {abs_temp_wav}")
                
                # Transcribe audio chunk
                print("Starting transcription...")
                try:
                    result = model.transcribe(str(abs_temp_wav), language='ar')
                    transcribed_text = result['text'].strip()
                    print(f"Transcription result: {transcribed_text}")
                except Exception as transcribe_error:
                    print(f"Transcription error: {transcribe_error}")
                    import traceback
                    print(f"Transcription error trace: {traceback.format_exc()}")
                    ws.send(json.dumps({
                        'type': 'error',
                        'message': f'Transcription failed: {str(transcribe_error)}'
                    }))
                    chunk_counter += 1
                    continue
                
                # Match transcribed text with Fatiha verses
                ayah_number, word_index = match_ayah_and_word(transcribed_text)
                print(f"Matched text to ayah {ayah_number}, word {word_index}")
                
                # Analyze using our new Tajweed checker
                if ayah_number is not None:
                    feedback = analyze_ayah(ayah_number, transcribed_text)
                else:
                    feedback = [{
                        'type': 'error',
                        'message': "Could not match recitation to any ayah of Surah Al-Fatiha"
                    }]
                
                # Send results back to client
                response = {
                    'type': 'transcription',
                    'text': transcribed_text,
                    'ayah_number': ayah_number,
                    'word_index': word_index,
                    'feedback': get_formatted_feedback(feedback)
                }
                ws.send(json.dumps(response))
                print("Sent response to client")
                
                # Clean up temporary file
                if temp_wav.exists():
                    temp_wav.unlink()
                    print(f"Cleaned up temporary file: {temp_wav}")
                chunk_counter += 1
                
            except Exception as e:
                print(f"Error processing audio chunk: {str(e)}")
                print(f"Error type: {type(e)}")
                import traceback
                print(f"Stack trace: {traceback.format_exc()}")
                try:
                    ws.send(json.dumps({
                        'type': 'error',
                        'message': f"Error processing audio: {str(e)}"
                    }))
                except:
                    print("Failed to send error message to client")
                break
    finally:
        # Clean up session directory
        try:
            if session_dir.exists():
                shutil.rmtree(session_dir, ignore_errors=True)
                print(f"Cleaned up session directory: {session_dir}")
        except Exception as e:
            print(f"Error cleaning up session directory: {str(e)}")
        print("WebSocket connection closed")

@app.route('/analyze', methods=['POST'])
def analyze_audio():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Save the audio file
    filename = Path(audio_file.filename)
    save_path = UPLOAD_FOLDER / filename
    audio_file.save(save_path)

    try:
        # Load model and transcribe
        model = whisper.load_model("base")
        result = model.transcribe(str(save_path), language="ar")
        
        # Get the transcription
        transcription = result['text']
        
        # Match transcribed text with Fatiha verses
        ayah_number, word_index = match_ayah_and_word(transcription)
        
        # Analyze using our new Tajweed checker
        if ayah_number is not None:
            feedback = analyze_ayah(ayah_number, transcription)
        else:
            feedback = [{
                'type': 'error',
                'message': "Could not match recitation to any ayah of Surah Al-Fatiha"
            }]
        
        return jsonify({
            'success': True,
            'transcription': transcription,
            'ayah_number': ayah_number,
            'feedback': get_formatted_feedback(feedback)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        # Clean up the audio file
        if save_path.exists():
            save_path.unlink()

@app.route('/latest-recording')
def get_latest_recording():
    global latest_recording
    if latest_recording and latest_recording.exists():
        return send_file(str(latest_recording), mimetype='audio/wav')
    return "No recording available", 404

if __name__ == '__main__':
    app.run(debug=True) 