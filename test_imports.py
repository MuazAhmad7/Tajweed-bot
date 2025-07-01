#!/usr/bin/env python3
"""
Test script to verify imports and basic functionality
"""
import sys
import traceback

def test_imports():
    """Test all required imports"""
    try:
        print("Testing imports...")
        
        # Flask and web
        import flask
        print(f"✓ Flask version: {flask.__version__}")
        import werkzeug
        print(f"✓ Werkzeug version: {werkzeug.__version__}")
        from flask import Flask, render_template, request, jsonify
        print("✓ Flask components")
        from flask_sock import Sock
        print("✓ Flask-Sock")
        
        # Scientific libraries
        import numpy as np
        print(f"✓ NumPy version: {np.__version__}")
        import torch
        print(f"✓ PyTorch version: {torch.__version__}")
        import librosa
        print(f"✓ Librosa imported")
        
        # ML libraries
        import whisper
        print("✓ Whisper imported")
        from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq
        print("✓ Transformers imported")
        
        # System utilities
        import psutil
        print("✓ psutil imported")
        from multiprocessing import shared_memory
        print("✓ shared_memory imported")
        
        print("\nAll imports successful!")
        return True
    except Exception as e:
        print(f"\n❌ Import error: {str(e)}")
        traceback.print_exc()
        return False

def test_flask_app():
    """Test basic Flask app creation"""
    try:
        print("\nTesting Flask app creation...")
        from flask import Flask
        app = Flask(__name__)
        
        @app.route('/test')
        def test_route():
            return "Test successful"
        
        print("✓ Flask app created successfully")
        return True
    except Exception as e:
        print(f"\n❌ Flask app error: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    imports_ok = test_imports()
    flask_ok = test_flask_app()
    
    if imports_ok and flask_ok:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Tests failed!")
        sys.exit(1) 