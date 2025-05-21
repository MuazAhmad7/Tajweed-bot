from flask import Flask, render_template, request, jsonify
import os
import whisper
from pathlib import Path
from utils.tajweed_rules import analyze_recitation
from flask_sock import Sock
import tempfile
import numpy as np
import torch
from utils.text_matcher import match_ayah_and_word
import wave
import json

app = Flask(__name__)
sock = Sock(app)

# Configure upload folder
UPLOAD_FOLDER = Path('recordings')
UPLOAD_FOLDER.mkdir(exist_ok=True)

# Initialize Whisper model
model = whisper.load_model("base")

# Fatiha verses with their word-by-word text
FATIHA_VERSES = {
    1: ["بِسْمِ", "ٱللَّهِ", "ٱلرَّحْمَٰنِ", "ٱلرَّحِيمِ"],
    2: ["ٱلْحَمْدُ", "لِلَّهِ", "رَبِّ", "ٱلْعَٰلَمِينَ"],
    3: ["ٱلرَّحْمَٰنِ", "ٱلرَّحِيمِ"],
    4: ["مَٰلِكِ", "يَوْمِ", "ٱلدِّينِ"],
    5: ["إِيَّاكَ", "نَعْبُدُ", "وَإِيَّاكَ", "نَسْتَعِينُ"],
    6: ["ٱهْدِنَا", "ٱلصِّرَٰطَ", "ٱلْمُسْتَقِيمَ"],
    7: ["صِرَٰطَ", "ٱلَّذِينَ", "أَنْعَمْتَ", "عَلَيْهِمْ", "غَيْرِ", "ٱلْمَغْضُوبِ", "عَلَيْهِمْ", "وَلَا", "ٱلضَّآلِّينَ"]
}

@app.route('/')
def index():
    return render_template('index.html')

@sock.route('/ws')
def handle_websocket(ws):
    temp_dir = tempfile.mkdtemp()
    chunk_counter = 0
    
    while True:
        try:
            # Receive audio chunk
            audio_data = ws.receive()
            
            # Save audio chunk to temporary WAV file
            temp_wav = os.path.join(temp_dir, f'chunk_{chunk_counter}.wav')
            with wave.open(temp_wav, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(audio_data)
            
            # Transcribe audio chunk
            result = model.transcribe(temp_wav, language='ar')
            transcribed_text = result['text'].strip()
            
            # Match transcribed text with Fatiha verses
            ayah_number, word_index = match_ayah_and_word(transcribed_text)
            
            # Check for Tajweed errors if we found a match
            has_error = False
            if ayah_number and word_index is not None:
                current_word = FATIHA_VERSES[ayah_number][word_index]
                errors = analyze_recitation(transcribed_text, current_word)
                has_error = len(errors) > 0
            
            # Send results back to client
            response = {
                'type': 'transcription',
                'text': transcribed_text,
                'ayah_number': ayah_number,
                'word_index': word_index,
                'has_error': has_error
            }
            ws.send(json.dumps(response))
            
            # Clean up temporary file
            os.remove(temp_wav)
            chunk_counter += 1
            
        except Exception as e:
            print(f"Error processing audio: {str(e)}")
            break
    
    # Clean up temporary directory
    try:
        os.rmdir(temp_dir)
    except:
        pass

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
        
        # Analyze the transcription using our Tajweed rules
        transcription = result['text']
        feedback = analyze_recitation(transcription)
        
        return jsonify({
            'success': True,
            'transcription': transcription,
            'feedback': feedback
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        # Clean up the audio file
        if save_path.exists():
            save_path.unlink()

if __name__ == '__main__':
    app.run(debug=True) 