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
from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq
import librosa

app = Flask(__name__)
sock = Sock(app)

# Configure upload folder
UPLOAD_FOLDER = Path('recordings')
UPLOAD_FOLDER.mkdir(exist_ok=True)

# Create a temporary directory for audio processing in our project folder
TEMP_DIR = Path('temp_audio')
TEMP_DIR.mkdir(exist_ok=True)

# Initialize Whisper model
whisper_processor = AutoProcessor.from_pretrained("fawzanaramam/Whisper-Small-Finetuned-on-Surah-Fatiha")
whisper_model = AutoModelForSpeechSeq2Seq.from_pretrained("fawzanaramam/Whisper-Small-Finetuned-on-Surah-Fatiha")

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

def transcribe_audio(audio_file):
    """Transcribe audio using Whisper model"""
    try:
        # Load and preprocess the audio
        speech, sr = librosa.load(audio_file, sr=16000)
        speech = speech.astype(np.float32)
        
        # Process with Whisper model
        inputs = whisper_processor(
            speech,
            sampling_rate=16000,
            return_tensors="pt"
        )
        
        with torch.no_grad():
            generated_ids = whisper_model.generate(inputs["input_features"])
            transcription = whisper_processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        return transcription.strip()
    except Exception as e:
        print(f"Detailed transcription error: {str(e)}")
        import traceback
        print(f"Stack trace: {traceback.format_exc()}")
        raise

@app.route('/')
def index():
    return render_template('landing.html')

@app.route('/demo')
def demo():
    return render_template('index.html')

@sock.route('/ws')
def handle_websocket(ws):
    print("WebSocket connection established")
    chunk_counter = 0
    temp_wav = None
    target_ayah = None  # Store the target ayah number
    
    try:
        while True:
            message = ws.receive()
            
            # Check if this is a configuration message
            if isinstance(message, str):
                try:
                    config = json.loads(message)
                    if 'target_ayah' in config:
                        target_ayah = config['target_ayah']
                        print(f"Received target ayah: {target_ayah}")
                    continue
                except json.JSONDecodeError:
                    print("Invalid JSON message received")
                    continue
            
            # Create a temporary WAV file for this chunk
            temp_wav = TEMP_DIR / f'chunk_{chunk_counter}.wav'
            abs_temp_wav = temp_wav.absolute()
            
            try:
                # Save the received audio data
                with open(temp_wav, 'wb') as f:
                    f.write(message)
                
                print(f"Using absolute path for transcription: {abs_temp_wav}")
                
                # For the last ayah (ayah 6), we'll use a more robust approach
                if target_ayah == "6":
                    try:
                        # Try direct audio processing first
                        import soundfile as sf
                        audio, sr = sf.read(str(abs_temp_wav))
                        if sr != 16000:
                            # Resample to 16kHz if needed
                            import librosa
                            audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
                    except Exception as sf_error:
                        print(f"Direct audio processing failed: {sf_error}")
                        # Fallback to basic audio reading
                        import wave
                        with wave.open(str(abs_temp_wav), 'rb') as wf:
                            audio = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
                            audio = audio.astype(np.float32) / 32768.0  # Convert to float32
                    
                    # Process with Whisper model
                    inputs = whisper_processor(
                        audio,
                        sampling_rate=16000,
                        return_tensors="pt"
                    )
                    
                    with torch.no_grad():
                        generated_ids = whisper_model.generate(inputs["input_features"])
                        transcribed_text = whisper_processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
                else:
                    # For other ayahs, use the standard transcription
                    transcribed_text = transcribe_audio(str(abs_temp_wav))
                
                print(f"Transcription result: {transcribed_text}")
                
                # If we have a target ayah, use it directly
                if target_ayah is not None:
                    ayah_number = int(target_ayah)
                    word_index = 0  # Reset word index for now
                else:
                    # Fallback to matching if no target ayah
                    ayah_number, word_index = match_ayah_and_word(transcribed_text)
                
                print(f"Using ayah {ayah_number}, word {word_index}")
                
                # Analyze using our Tajweed checker
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
                
            except Exception as e:
                print(f"Error processing chunk: {e}")
                import traceback
                print(f"Error trace: {traceback.format_exc()}")
                ws.send(json.dumps({
                    'type': 'error',
                    'message': f'Processing failed: {str(e)}'
                }))
            finally:
                # Clean up temporary file
                if temp_wav and temp_wav.exists():
                    temp_wav.unlink()
                chunk_counter += 1
                
    except Exception as e:
        print(f"WebSocket error: {e}")
        import traceback
        print(f"WebSocket error trace: {traceback.format_exc()}")
    finally:
        # Clean up any remaining temporary files
        if temp_wav and temp_wav.exists():
            temp_wav.unlink()

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
        # Transcribe using our new function
        transcription = transcribe_audio(str(save_path))
        
        # Match transcribed text with Fatiha verses
        ayah_number, word_index = match_ayah_and_word(transcription)
        
        # Analyze using our Tajweed checker
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

@app.route('/analyze-dataset', methods=['GET'])
def analyze_dataset():
    # Fix the path to use the exact folder name with space
    current_dir = Path(__file__).parent
    dataset_path = current_dir / 'tajweed dataset' / 'audio'
    print(f"Looking for dataset at: {dataset_path}")
    results = []
    
    try:
        metadata_file = dataset_path / 'fatiha_metadata_final.csv'
        print(f"Trying to open metadata file: {metadata_file}")
        if not metadata_file.exists():
            return jsonify({'error': f'Metadata file not found at {metadata_file}'}), 404
            
        # Read the metadata file
        with open(metadata_file, 'r', encoding='utf-8') as f:
            import csv
            reader = csv.DictReader(f)
            metadata = list(reader)
        
        for entry in metadata:
            audio_file = dataset_path / entry['file'].replace('.wav', '.mp3')
            print(f"Processing audio file: {audio_file}")
            if not audio_file.exists():
                print(f"Audio file not found: {audio_file}")
                continue
                
            try:
                # Transcribe the audio
                result = model.transcribe(str(audio_file), language="ar")
                transcription = result['text'].strip()
                
                # Get the ayah number from metadata
                ayah_number = int(entry['ayah']) - 1  # Convert to 0-based index
                
                # Analyze using our Tajweed checker
                feedback = analyze_ayah(ayah_number, transcription)
                
                results.append({
                    'reciter': entry['reciter'],
                    'ayah': entry['ayah'],
                    'original_text': entry['text'],
                    'transcribed_text': transcription,
                    'feedback': get_formatted_feedback(feedback)
                })
                
            except Exception as e:
                print(f"Error processing {audio_file}: {str(e)}")
                results.append({
                    'reciter': entry['reciter'],
                    'ayah': entry['ayah'],
                    'error': str(e)
                })
        
        return jsonify(results)
    except Exception as e:
        print(f"Error in analyze_dataset: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/reference-audio/<reciter>/<ayah>')
def get_reference_audio(reciter, ayah):
    # Construct the audio file path
    audio_file = Path(__file__).parent / 'tajweed dataset' / 'audio' / f'{reciter}_00100{ayah}.mp3'
    
    if not audio_file.exists():
        return "Audio file not found", 404
        
    return send_file(str(audio_file), mimetype='audio/mpeg')

@app.route('/switch_model/<model_name>')
def switch_model(model_name):
    """Switch between ASR models"""
    global CURRENT_MODEL
    if model_name in ["whisper", "wav2vec2"]:
        CURRENT_MODEL = model_name
        return jsonify({"status": "success", "message": f"Switched to {model_name} model"})
    return jsonify({"status": "error", "message": "Invalid model name"})

if __name__ == '__main__':
    app.run(debug=True) 