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
from multiprocessing import shared_memory
import pickle
import atexit

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

# Global variables for model and processor
global_processor = None
global_model = None

def load_models():
    """Load models once and share between workers"""
    global global_processor, global_model
    if global_processor is None or global_model is None:
        print("[MEM] Loading models...")
        try:
            # Try to access existing shared memory
            shm = shared_memory.SharedMemory(name='whisper_model')
            print("[MEM] Using existing model from shared memory")
        except FileNotFoundError:
            # First worker loads the model
            print("[MEM] First worker loading model")
            processor = AutoProcessor.from_pretrained(
                "fawzanaramam/Whisper-Small-Finetuned-on-Surah-Fatiha",
                low_memory=True
            )
            model = AutoModelForSpeechSeq2Seq.from_pretrained(
                "fawzanaramam/Whisper-Small-Finetuned-on-Surah-Fatiha",
                low_cpu_mem_usage=True,
                torch_dtype=torch.float16  # Use half precision
            )
            # Move model to CPU and optimize memory
            model = model.to('cpu').eval()
            
            # Create shared memory and store model
            model_bytes = pickle.dumps((processor, model))
            shm = shared_memory.SharedMemory(create=True, size=len(model_bytes), name='whisper_model')
            shm.buf[:len(model_bytes)] = model_bytes
            
        # Load model from shared memory
        model_bytes = bytes(shm.buf)
        global_processor, global_model = pickle.loads(model_bytes)
        print("[MEM] Models loaded successfully")

def cleanup_shared_memory():
    """Cleanup shared memory on shutdown"""
    try:
        shm = shared_memory.SharedMemory(name='whisper_model')
        shm.close()
        shm.unlink()
    except FileNotFoundError:
        pass

# Register cleanup function
atexit.register(cleanup_shared_memory)

def transcribe_audio(audio_file):
    """Transcribe audio using global model instance"""
    global global_processor, global_model
    try:
        if global_processor is None or global_model is None:
            load_models()
            
        # Load and preprocess the audio
        speech, sr = librosa.load(audio_file, sr=16000)
        speech = speech.astype(np.float32)
        
        # Clear any unused memory
        gc.collect()
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
        
        # Process with Whisper model
        inputs = global_processor(
            speech,
            sampling_rate=16000,
            return_tensors="pt"
        )
        
        with torch.no_grad():
            generated_ids = global_model.generate(
                inputs["input_features"],
                max_length=225,
                num_beams=1
            )
            transcription = global_processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        # Clear temporary tensors
        del inputs, generated_ids
        gc.collect()
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
        
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

def get_memory_usage():
    """Get current memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def log_memory(action):
    """Log memory usage with a specific action"""
    memory = get_memory_usage()
    print(f"[MEMORY] {action}: {memory:.2f} MB")
    return memory

@sock.route('/ws')
def handle_websocket(ws):
    print("WebSocket connection established")
    request_logger.info("WEBSOCKET: /ws connection established")
    
    # Log initial memory
    initial_memory = log_memory("Initial memory before recording")
    peak_memory = initial_memory
    
    chunk_counter = 0
    temp_wav = None
    target_ayah = None
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
                    data = json.loads(message)
                    if data.get('done'):
                        done = True
                        # Log memory before processing
                        pre_process_memory = log_memory("Memory before processing recording")
                        
                        # Process the recording
                        result = process_recording(temp_wav, target_ayah)
                        
                        # Log memory after processing
                        post_process_memory = log_memory("Memory after processing recording")
                        peak_memory = max(peak_memory, post_process_memory)
                        
                        print(f"Memory used for processing: {post_process_memory - pre_process_memory:.2f} MB")
                        print(f"Peak memory: {peak_memory:.2f} MB")
                        
                        # Cleanup
                        gc.collect()
                        torch.cuda.empty_cache() if torch.cuda.is_available() else None
                        after_cleanup = log_memory("After cleanup")
                        
                        print(f"Memory freed by cleanup: {post_process_memory - after_cleanup:.2f} MB")
                        
                        ws.send(json.dumps(result))
                    else:
                        target_ayah = data.get('target_ayah')
                        temp_wav = data.get('temp_wav')
                except json.JSONDecodeError:
                    print("Error decoding JSON message")
                    request_logger.error("WEBSOCKET: Error decoding JSON message")
            else:
                # Handle binary audio data
                audio_chunks.append(message)
                chunk_counter += 1
                current_memory = log_memory(f"Memory after chunk {chunk_counter}")
                peak_memory = max(peak_memory, current_memory)
                
    except Exception as e:
        print(f"WebSocket error: {e}")
        request_logger.error(f"WEBSOCKET: Error - {e}")
    finally:
        # Final memory cleanup
        gc.collect()
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
        final_memory = log_memory("Final memory")
        print(f"Total memory change: {final_memory - initial_memory:.2f} MB")
        print(f"Peak memory reached: {peak_memory:.2f} MB")

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

        # Only check Madd Laazim for الضَّالِّينَ in the last ayah (ayah_number == 6)
        madd_results = []
        if ayah_number == 6:
            # Find the index of الضَّالِّينَ (normalize for robustness)
            target_word = None
            for w in words:
                if normalize_arabic_text(w) == normalize_arabic_text('الضَّالِّينَ'):
                    target_word = w
                    break
            if target_word:
                word_idx = words.index(target_word)
                # Get audio duration and word durations
                audio_duration = get_audio_duration_librosa(str(save_path))
                debug_log.append(f'Audio duration: {audio_duration:.2f}s')
                word_lengths = [len(normalize_arabic_text(w)) for w in words]
                total_length = sum(word_lengths)
                word_durations = [(l / total_length) * audio_duration if total_length > 0 else 0 for l in word_lengths]
                debug_log.append(f'Word durations: {word_durations}')
                this_word_duration = word_durations[word_idx] if word_idx < len(word_durations) else 0
                # Madd Laazim feedback logic
                mandatory_msg = 'Madd Laazim is a mandatory 6 count for the ending ayah.'
                if this_word_duration < 2.0:
                    feedback = f"❌ Madd Laazim too short on الضَّالِّينَ. {mandatory_msg}"
                    madd_detected = False
                elif this_word_duration > 3.0:
                    feedback = f"❌ Madd Laazim too long on الضَّالِّينَ. {mandatory_msg}"
                    madd_detected = False
                else:
                    feedback = f"✅ Madd Laazim correct on الضَّالِّينَ. {mandatory_msg}"
                    madd_detected = True
                madd_results.append({
                    'ayah': ayah_number + 1,
                    'word': target_word,
                    'letter': '',
                    'type': 'Madd Laazim',
                    'madd_detected': madd_detected,
                    'text_expected': True,
                    'feedback': feedback,
                })
                debug_log.append(f"DEBUG: Madd Laazim analysis result: {madd_results}")
            else:
                debug_log.append('الضَّالِّينَ not found in last ayah words.')
        else:
            debug_log.append('Not last ayah, skipping Madd feedback.')

        # Clean up audio file only after all processing
        if save_path.exists():
            save_path.unlink()
            debug_log.append(f'Deleted audio file {save_path}')

        return jsonify({
            'status': 'done',
            'results': madd_results,
            'debug': debug_log
        })

    except Exception as e:
        error = f'Internal error: {str(e)}'
        debug_log.append(error)
        return jsonify({'status': 'error', 'error': error, 'debug': debug_log}), 500

# Load models when app starts
load_models()

if __name__ == '__main__':
    # Development server
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port) 