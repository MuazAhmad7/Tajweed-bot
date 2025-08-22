import os
import logging
from flask import Flask, render_template, request, jsonify
from pathlib import Path

# Set up simple logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Simple request logging
def log_request(req):
    logger.info(f"REQUEST: {req.method} {req.path}")

@app.route('/')
def index():
    log_request(request)
    return render_template('landing.html')

@app.route('/demo')
def demo():
    log_request(request)
    return render_template('index.html')

@app.route('/tajweed-rules')
def tajweed_rules():
    log_request(request)
    return render_template('tajweed_rules.html')

@app.route('/health')
def health_check():
    """Simple health check endpoint"""
    log_request(request)
    return jsonify({
        'status': 'healthy',
        'mode': 'static',
        'message': 'Static Tajweed learning website - no ML models loaded'
    })

# Mock endpoints for frontend compatibility
@app.route('/analyze', methods=['POST'])
def analyze_audio():
    log_request(request)
    return jsonify({
        'success': False,
        'message': 'Audio analysis is disabled in static mode. This is a demonstration of the Tajweed learning interface.',
        'mode': 'static'
    }), 200

@app.route('/madd-audio-analysis', methods=['POST'])
def madd_audio_analysis():
    log_request(request)
    return jsonify({
        'status': 'disabled',
        'message': 'Madd analysis is disabled in static mode. This is a demonstration of the Tajweed learning interface.',
        'mode': 'static'
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    logger.info(f"Starting STATIC Tajweed website on port {port}")
    logger.info("Note: All ML models and audio processing are disabled in this version")
    app.run(debug=True, host='0.0.0.0', port=port)
