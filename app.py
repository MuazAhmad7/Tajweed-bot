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
import gc
import psutil
import logging
from datetime import datetime
from utils.tajweed_checker import normalize_arabic_text, ARABIC_MADD_LETTERS, SURAH_FATIHA

app = Flask(__name__)
sock = Sock(app)

# Configure upload folder
UPLOAD_FOLDER = Path('recordings')
UPLOAD_FOLDER.mkdir(exist_ok=True)

# Create a temporary directory for audio processing in our project folder
TEMP_DIR = Path('temp_audio')
TEMP_DIR.mkdir(exist_ok=True)

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

# Set up request logging to a file
REQUEST_LOG_FILE = 'request_log.txt'
request_logger = logging.getLogger('request_logger')
request_logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(REQUEST_LOG_FILE)
file_handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
if not request_logger.hasHandlers():
    request_logger.addHandler(file_handler)

def log_request(req):
    try:
        request_logger.info(f"REQUEST: {req.method} {req.path}\n  args: {dict(req.args)}\n  form: {dict(req.form)}\n  json: {req.get_json(silent=True)}\n  headers: {dict(req.headers)}")
    except Exception as e:
        request_logger.error(f"Failed to log request: {e}")

def transcribe_audio(audio_file):
    """Transcribe audio using Whisper model, loading model only when needed to save memory."""
    try:
        print("[MEM] Before model load:", psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2, "MB")
        processor = AutoProcessor.from_pretrained("fawzanaramam/Whisper-Small-Finetuned-on-Surah-Fatiha")
        model = AutoModelForSpeechSeq2Seq.from_pretrained("fawzanaramam/Whisper-Small-Finetuned-on-Surah-Fatiha")
        print("[MEM] After model load:", psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2, "MB")
        # Load and preprocess the audio
        speech, sr = librosa.load(audio_file, sr=16000)
        speech = speech.astype(np.float32)
        # Process with Whisper model
        inputs = processor(
            speech,
            sampling_rate=16000,
            return_tensors="pt"
        )
        with torch.no_grad():
            generated_ids = model.generate(inputs["input_features"])
            transcription = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        print("[MEM] After transcription:", psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2, "MB")
        del processor
        del model
        gc.collect()
        print("[MEM] After gc.collect():", psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2, "MB")
        return transcription.strip()
    except Exception as e:
        print(f"Detailed transcription error: {str(e)}")
        import traceback
        print(f"Stack trace: {traceback.format_exc()}")
        raise

@app.route('/')
def index():
    log_request(request)
    print('DEBUG: Handling / route')
    return render_template('landing.html')

@app.route('/demo')
def demo():
    log_request(request)
    print('DEBUG: Handling /demo route')
    return render_template('index.html')

@app.route('/tajweed-rules')
def tajweed_rules():
    log_request(request)
    print('DEBUG: Handling /tajweed-rules route')
    return render_template('tajweed_rules.html')

@sock.route('/ws')
def handle_websocket(ws):
    print("WebSocket connection established")
    request_logger.info("WEBSOCKET: /ws connection established")
    chunk_counter = 0
    temp_wav = None
    target_ayah = None  # Store the target ayah number
    audio_chunks = []
    done = False
    try:
        while not done:
            message = ws.receive()
            if message is None:
                print("WebSocket closed by client.")
                request_logger.info("WEBSOCKET: closed by client")
                break
            # Check if this is a configuration or done message
            if isinstance(message, str):
                try:
                    config = json.loads(message)
                    if 'target_ayah' in config:
                        target_ayah = config['target_ayah']
                        print(f"Received target ayah: {target_ayah}")
                        request_logger.info(f"WEBSOCKET: Received target ayah: {target_ayah}")
                        continue
                    if config.get('type') == 'done':
                        print("Received done message from client.")
                        request_logger.info("WEBSOCKET: Received done message from client.")
                        done = True
                        continue
                except json.JSONDecodeError:
                    print("Invalid JSON message received")
                    request_logger.info("WEBSOCKET: Invalid JSON message received")
                    continue
            # Save audio chunk in memory
            audio_chunks.append(message)
            chunk_counter += 1
        # After receiving all chunks, process the audio
        if audio_chunks:
            temp_wav = TEMP_DIR / f'ws_recording_{os.getpid()}.wav'
            abs_temp_wav = temp_wav.absolute()
            try:
                with open(temp_wav, 'wb') as f:
                    for chunk in audio_chunks:
                        f.write(chunk)
                print(f"Saved full audio to {abs_temp_wav}")
                request_logger.info(f"WEBSOCKET: Saved full audio to {abs_temp_wav}")
                # Transcription logic (same as before)
                if target_ayah == "6":
                    try:
                        import soundfile as sf
                        audio, sr = sf.read(str(abs_temp_wav))
                        if sr != 16000:
                            import librosa
                            audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
                    except Exception as sf_error:
                        print(f"Direct audio processing failed: {sf_error}")
                        request_logger.info(f"WEBSOCKET: Direct audio processing failed: {sf_error}")
                        import wave
                        with wave.open(str(abs_temp_wav), 'rb') as wf:
                            audio = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
                            audio = audio.astype(np.float32) / 32768.0
                    inputs = AutoProcessor.from_pretrained("fawzanaramam/Whisper-Small-Finetuned-on-Surah-Fatiha")(
                        audio,
                        sampling_rate=16000,
                        return_tensors="pt"
                    )
                    with torch.no_grad():
                        generated_ids = AutoModelForSpeechSeq2Seq.from_pretrained("fawzanaramam/Whisper-Small-Finetuned-on-Surah-Fatiha").generate(inputs["input_features"])
                        transcribed_text = inputs.batch_decode(generated_ids, skip_special_tokens=True)[0]
                else:
                    transcribed_text = transcribe_audio(str(abs_temp_wav))
                print(f"Transcription result: {transcribed_text}")
                request_logger.info(f"WEBSOCKET: Transcription result: {transcribed_text}")
                if target_ayah is not None:
                    ayah_number = int(target_ayah)
                    word_index = 0
                else:
                    ayah_number, word_index = match_ayah_and_word(transcribed_text)
                print(f"Using ayah {ayah_number}, word {word_index}")
                request_logger.info(f"WEBSOCKET: Using ayah {ayah_number}, word {word_index}")
                if ayah_number is not None:
                    feedback = analyze_ayah(ayah_number, transcribed_text)
                else:
                    feedback = [{
                        'type': 'error',
                        'message': "Could not match recitation to any ayah of Surah Al-Fatiha"
                    }]
                response = {
                    'type': 'transcription',
                    'text': transcribed_text,
                    'ayah_number': ayah_number,
                    'word_index': word_index,
                    'feedback': get_formatted_feedback(feedback)
                }
                ws.send(json.dumps(response))
                print("Sent response to client")
                request_logger.info("WEBSOCKET: Sent response to client")
            except Exception as e:
                print(f"Error processing audio: {e}")
                import traceback
                print(f"Error trace: {traceback.format_exc()}")
                request_logger.error(f"WEBSOCKET: Error processing audio: {e}\n{traceback.format_exc()}")
                ws.send(json.dumps({
                    'type': 'error',
                    'message': f'Processing failed: {str(e)}'
                }))
            finally:
                if temp_wav and temp_wav.exists():
                    temp_wav.unlink()
    except Exception as e:
        print(f"WebSocket error: {e}")
        import traceback
        print(f"WebSocket error trace: {traceback.format_exc()}")
        request_logger.error(f"WEBSOCKET: error: {e}\n{traceback.format_exc()}")
    finally:
        if temp_wav and temp_wav.exists():
            temp_wav.unlink()

@app.route('/analyze', methods=['POST'])
def analyze_audio():
    log_request(request)
    print('DEBUG: Handling /analyze route')
    if 'audio' not in request.files:
        print('DEBUG: No audio file provided')
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    if audio_file.filename == '':
        print('DEBUG: No selected file')
        return jsonify({'error': 'No selected file'}), 400

    # Save the audio file
    filename = Path(audio_file.filename)
    save_path = UPLOAD_FOLDER / filename
    audio_file.save(save_path)
    print(f'DEBUG: Saved audio file to {save_path}')

    try:
        # Transcribe using our new function
        transcription = transcribe_audio(str(save_path))
        print(f'DEBUG: Transcription: {transcription}')
        
        # Match transcribed text with Fatiha verses
        ayah_number, word_index = match_ayah_and_word(transcription)
        print(f'DEBUG: Matched ayah_number: {ayah_number}, word_index: {word_index}')
        
        # Analyze using our Tajweed checker
        if ayah_number is not None:
            feedback = analyze_ayah(ayah_number, transcription)
        else:
            feedback = [{
                'type': 'error',
                'message': "Could not match recitation to any ayah of Surah Al-Fatiha"
            }]
        print(f'DEBUG: Feedback: {feedback}')
        
        return jsonify({
            'success': True,
            'transcription': transcription,
            'ayah_number': ayah_number,
            'feedback': get_formatted_feedback(feedback)
        })

    except Exception as e:
        print(f'DEBUG: Exception: {e}')
        return jsonify({'error': str(e)}), 500

    finally:
        # Clean up the audio file
        if save_path.exists():
            save_path.unlink()
            print(f'DEBUG: Deleted audio file {save_path}')

@app.route('/latest-recording')
def get_latest_recording():
    log_request(request)
    print('DEBUG: Handling /latest-recording route')
    global latest_recording
    if latest_recording and latest_recording.exists():
        print(f'DEBUG: Returning latest recording {latest_recording}')
        return send_file(str(latest_recording), mimetype='audio/wav')
    print('DEBUG: No recording available')
    return "No recording available", 404

@app.route('/analyze-dataset', methods=['GET'])
def analyze_dataset():
    log_request(request)
    print('DEBUG: Handling /analyze-dataset route')
    # Fix the path to use the exact folder name with space
    current_dir = Path(__file__).parent
    dataset_path = current_dir / 'tajweed dataset' / 'audio'
    print(f"Looking for dataset at: {dataset_path}")
    results = []
    
    try:
        metadata_file = dataset_path / 'fatiha_metadata_final.csv'
        print(f"Trying to open metadata file: {metadata_file}")
        if not metadata_file.exists():
            print(f"DEBUG: Metadata file not found at {metadata_file}")
            return jsonify({'error': f'Metadata file not found at {metadata_file}'}), 404
            
        # Read the metadata file
        with open(metadata_file, 'r', encoding='utf-8') as f:
            import csv
            reader = csv.DictReader(f)
            metadata = list(reader)
        print(f"DEBUG: Loaded metadata with {len(metadata)} entries")
        
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
                print(f"DEBUG: Transcription for {audio_file}: {transcription}")
                
                # Get the ayah number from metadata
                ayah_number = int(entry['ayah']) - 1  # Convert to 0-based index
                print(f"DEBUG: Ayah number for {audio_file}: {ayah_number}")
                
                # Analyze using our Tajweed checker
                feedback = analyze_ayah(ayah_number, transcription)
                print(f"DEBUG: Feedback for {audio_file}: {feedback}")
                
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
        print(f"DEBUG: Finished processing dataset")
        return jsonify(results)
    except Exception as e:
        print(f"Error in analyze_dataset: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/reference-audio/<reciter>/<ayah>')
def get_reference_audio(reciter, ayah):
    log_request(request)
    print(f'DEBUG: Handling /reference-audio/{reciter}/{ayah} route')
    # Construct the audio file path
    audio_file = Path(__file__).parent / 'tajweed dataset' / 'audio' / f'{reciter}_00100{ayah}.mp3'
    
    if not audio_file.exists():
        print(f'DEBUG: Audio file not found: {audio_file}')
        return "Audio file not found", 404
        
    print(f'DEBUG: Returning audio file: {audio_file}')
    return send_file(str(audio_file), mimetype='audio/mpeg')

@app.route('/switch_model/<model_name>')
def switch_model(model_name):
    log_request(request)
    print(f'DEBUG: Handling /switch_model/{model_name} route')
    """Switch between ASR models"""
    global CURRENT_MODEL
    if model_name in ["whisper", "wav2vec2"]:
        CURRENT_MODEL = model_name
        print(f'DEBUG: Switched to model {model_name}')
        return jsonify({"status": "success", "message": f"Switched to {model_name} model"})
    print(f'DEBUG: Invalid model name: {model_name}')
    return jsonify({"status": "error", "message": "Invalid model name"})

def get_audio_duration_librosa(audio_path):
    """Get duration of audio file in seconds using librosa, with robust fallbacks."""
    try:
        import librosa
        duration = librosa.get_duration(path=audio_path)
        if duration > 0:
            return duration
    except Exception as e:
        print(f"Librosa failed: {e}")
    # Fallback to soundfile
    try:
        import soundfile as sf
        f = sf.SoundFile(audio_path)
        duration = len(f) / f.samplerate
        return duration
    except Exception as e:
        print(f"SoundFile failed: {e}")
    # Fallback to wave
    try:
        import wave
        with wave.open(audio_path, 'rb') as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            duration = frames / float(rate)
            return duration
    except Exception as e:
        print(f"Wave failed: {e}")
    return 0.0

@app.route('/madd-audio-analysis', methods=['POST'])
def madd_audio_analysis():
    debug_log = []
    try:
        # 1. Get latest audio file from upload (like /analyze)
        if 'audio' not in request.files:
            error = 'No audio file provided'
            debug_log.append(error)
            return jsonify({'status': 'error', 'error': error, 'debug': debug_log}), 400
        audio_file = request.files['audio']
        if audio_file.filename == '':
            error = 'No selected file'
            debug_log.append(error)
            return jsonify({'status': 'error', 'error': error, 'debug': debug_log}), 400
        filename = Path(audio_file.filename)
        save_path = UPLOAD_FOLDER / filename
        audio_file.save(save_path)
        debug_log.append(f'Saved audio file to {save_path}')

        # 2. Transcribe
        transcription = transcribe_audio(str(save_path))
        debug_log.append(f'Transcription: {transcription}')
        if not transcription:
            error = 'Transcription failed.'
            debug_log.append(error)
            if save_path.exists():
                save_path.unlink()
            return jsonify({'status': 'error', 'error': error, 'debug': debug_log}), 400

        # 3. Match ayah
        ayah_number, _ = match_ayah_and_word(transcription)
        debug_log.append(f'Matched ayah_number: {ayah_number}')
        if ayah_number is None:
            error = 'Could not match recitation to any ayah of Surah Al-Fatiha.'
            debug_log.append(error)
            if save_path.exists():
                save_path.unlink()
            return jsonify({'status': 'error', 'error': error, 'debug': debug_log}), 400

        # 4. Get ayah text and words
        ayah_data = SURAH_FATIHA.get(ayah_number)
        if not ayah_data:
            error = f'Ayah {ayah_number} not found in SURAH_FATIHA.'
            debug_log.append(error)
            if save_path.exists():
                save_path.unlink()
            return jsonify({'status': 'error', 'error': error, 'debug': debug_log}), 400
        ayah_text = ayah_data['text']
        words = ayah_text.split()
        debug_log.append(f'Ayah text: {ayah_text}')
        debug_log.append(f'Words: {words}')

        # 5. Detect Madd letters in each word
        madd_results = []
        for word in words:
            norm_word = normalize_arabic_text(word)
            for letter in ARABIC_MADD_LETTERS:
                if letter in norm_word:
                    madd_results.append({
                        'ayah': ayah_number + 1,  # 1-based
                        'word': word,
                        'letter': letter,
                        'type': 'Madd Asli',
                        'text_expected': True
                    })
        debug_log.append(f'Madd instances: {madd_results}')

        # 6. Estimate durations (improved: proportional to word length)
        audio_duration = get_audio_duration_librosa(str(save_path))
        debug_log.append(f'Audio duration: {audio_duration:.2f}s')
        # Split ayah text into words and get their lengths
        word_lengths = [len(normalize_arabic_text(w)) for w in words]
        total_length = sum(word_lengths)
        # Assign each word a proportional duration
        word_durations = [(l / total_length) * audio_duration if total_length > 0 else 0 for l in word_lengths]
        debug_log.append(f'Word durations: {word_durations}')

        # 7. Madd detection and feedback (use per-word duration)
        for madd in madd_results:
            # Find the index of the word in the ayah
            try:
                word_idx = words.index(madd['word'])
            except ValueError:
                word_idx = 0
            this_word_duration = word_durations[word_idx] if word_idx < len(word_durations) else 0
            if this_word_duration < 0.4:
                madd['madd_detected'] = False
                madd['feedback'] = f"Madd too short on {madd['letter']} in {madd['word']} (duration: {this_word_duration:.2f}s, should be at least 0.4s)"
            elif this_word_duration > 0.7:
                madd['madd_detected'] = False
                madd['feedback'] = f"Madd too long on {madd['letter']} in {madd['word']} (duration: {this_word_duration:.2f}s, should not exceed 0.7s)"
            else:
                madd['madd_detected'] = True
                madd['feedback'] = f"Madd correct on {madd['letter']} in {madd['word']} (duration: {this_word_duration:.2f}s)"
        debug_log.append(f"DEBUG: Madd analysis results: {madd_results}")
        debug_log.append('Final Madd analysis complete.')

        # 8. Prepare user-friendly results for frontend
        user_friendly_results = []
        for madd in madd_results:
            user_friendly_results.append({
                'ayah': madd['ayah'],
                'word': madd['word'],
                'letter': madd['letter'],
                'type': madd['type'],
                'madd_detected': madd['madd_detected'],
                'text_expected': madd['text_expected'],
                'feedback': madd['feedback'],
            })

        # 9. Clean up audio file only after all processing
        if save_path.exists():
            save_path.unlink()
            debug_log.append(f'Deleted audio file {save_path}')

        return jsonify({
            'status': 'done',
            'results': user_friendly_results,
            'debug': debug_log
        })

    except Exception as e:
        error = f'Internal error: {str(e)}'
        debug_log.append(error)
        return jsonify({'status': 'error', 'error': error, 'debug': debug_log}), 500

if __name__ == '__main__':
    app.run(debug=True) 