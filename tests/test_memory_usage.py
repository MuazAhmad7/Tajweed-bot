import sys
import os
import psutil
import time
import torch
import gc
from pathlib import Path
import numpy as np
import wave
import threading
from datetime import datetime

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import load_models, transcribe_audio, global_processor, global_model

def get_memory_usage():
    """Get current memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def log_memory(action, interval=False):
    """Log memory usage with a specific action"""
    # Force garbage collection before measuring
    gc.collect()
    torch.cuda.empty_cache() if torch.cuda.is_available() else None
    
    memory = get_memory_usage()
    torch_memory = torch.cuda.memory_allocated() / 1024 / 1024 if torch.cuda.is_available() else 0
    if not interval:
        print(f"[MEMORY] {action}: {memory:.2f} MB (RAM) | {torch_memory:.2f} MB (GPU)")
    return memory

def monitor_memory(stop_event, label=""):
    """Continuously monitor memory usage"""
    peak_memory = 0
    start_time = time.time()
    
    while not stop_event.is_set():
        current_memory = log_memory(f"{label} Continuous", interval=True)
        peak_memory = max(peak_memory, current_memory)
        elapsed = time.time() - start_time
        if not stop_event.is_set():  # Only print if we haven't been asked to stop
            print(f"[{elapsed:.1f}s] Current Memory: {current_memory:.2f} MB | Peak: {peak_memory:.2f} MB")
        time.sleep(1)  # Check every second
    
    return peak_memory

def test_model_loading():
    """Test memory usage during model loading"""
    print("\n=== Testing Model Loading Memory Usage ===")
    
    # Initial memory
    initial_memory = log_memory("Initial memory")
    
    # Load models
    load_models()
    after_load = log_memory("After loading models")
    
    # Force garbage collection
    gc.collect()
    torch.cuda.empty_cache() if torch.cuda.is_available() else None
    after_gc = log_memory("After garbage collection")
    
    print(f"\nModel loading increased memory by: {after_load - initial_memory:.2f} MB")
    print(f"Garbage collection freed: {after_load - after_gc:.2f} MB")

def test_audio_processing():
    """Test memory usage during audio processing"""
    print("\n=== Testing Audio Processing Memory Usage ===")
    
    # Get test audio files
    audio_dir = Path("tajweed dataset/audio")
    test_files = list(audio_dir.glob("*.mp3"))[:3]  # Test with first 3 audio files
    
    peak_memory = 0
    for audio_file in test_files:
        print(f"\nProcessing: {audio_file.name}")
        
        # Memory before processing
        before_process = log_memory("Before processing")
        
        # Process audio
        try:
            transcribed_text = transcribe_audio(str(audio_file))
            print(f"Transcription: {transcribed_text}")
            
            # Memory after processing
            after_process = log_memory("After processing")
            peak_memory = max(peak_memory, after_process)
            
            # Cleanup
            gc.collect()
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
            after_cleanup = log_memory("After cleanup")
            
            print(f"Processing used: {after_process - before_process:.2f} MB")
            print(f"Cleanup freed: {after_process - after_cleanup:.2f} MB")
            
        except Exception as e:
            print(f"Error processing {audio_file.name}: {e}")
    
    print(f"\nPeak memory usage during audio processing: {peak_memory:.2f} MB")

def test_memory_leak():
    """Test for memory leaks by processing the same file multiple times"""
    print("\n=== Testing for Memory Leaks ===")
    
    # Get a test file
    audio_file = next(Path("tajweed dataset/audio").glob("*.mp3"))
    
    initial_memory = log_memory("Initial memory")
    peak_memory = initial_memory
    
    # Process the same file multiple times
    for i in range(5):
        print(f"\nIteration {i+1}")
        transcribed_text = transcribe_audio(str(audio_file))
        print(f"Transcription: {transcribed_text}")
        
        current_memory = log_memory(f"After iteration {i+1}")
        peak_memory = max(peak_memory, current_memory)
        
        # Cleanup
        gc.collect()
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
        after_cleanup = log_memory("After cleanup")
        
        print(f"Memory change from start: {current_memory - initial_memory:.2f} MB")
    
    print(f"\nPeak memory during leak test: {peak_memory:.2f} MB")
    print(f"Final memory increase: {after_cleanup - initial_memory:.2f} MB")

def test_live_recording_simulation():
    """Simulate live recording and transcription process"""
    print("\n=== Testing Live Recording and Transcription ===")
    
    # Initialize models if not already loaded
    if global_processor is None or global_model is None:
        load_models()
    
    # Start memory monitoring in a separate thread
    stop_monitoring = threading.Event()
    monitor_thread = threading.Thread(
        target=monitor_memory,
        args=(stop_monitoring, "Recording"),
        daemon=True
    )
    
    try:
        print("\nSimulating recording process...")
        initial_memory = log_memory("Initial memory")
        
        # Start memory monitoring
        monitor_thread.start()
        
        # Simulate recording for 5 seconds
        print("Recording for 5 seconds...")
        time.sleep(5)
        
        # Process the recording
        print("\nProcessing recording...")
        # Use an existing audio file to simulate the recorded audio
        audio_file = next(Path("tajweed dataset/audio").glob("*.mp3"))
        transcribed_text = transcribe_audio(str(audio_file))
        
        # Get final memory usage
        final_memory = log_memory("Final memory")
        
        # Stop memory monitoring
        stop_monitoring.set()
        monitor_thread.join()
        
        print(f"\nTranscription result: {transcribed_text}")
        print(f"Memory change: {final_memory - initial_memory:.2f} MB")
        
    except Exception as e:
        print(f"Error during live recording simulation: {e}")
        stop_monitoring.set()
        if monitor_thread.is_alive():
            monitor_thread.join()
    
    finally:
        # Cleanup
        gc.collect()
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
        after_cleanup = log_memory("After cleanup")
        print(f"Memory freed by cleanup: {final_memory - after_cleanup:.2f} MB")

if __name__ == "__main__":
    print("Starting memory usage tests...")
    print(f"Python version: {sys.version}")
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA device: {torch.cuda.get_device_name(0)}")
    
    # Run tests
    test_model_loading()
    test_audio_processing()
    test_memory_leak()
    test_live_recording_simulation()
    
    print("\nTests completed!") 