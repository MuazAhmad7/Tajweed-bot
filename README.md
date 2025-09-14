# AI Tajweed Teacher

# Frontend Site https://tajweed-bot-production.up.railway.app/

An interactive web application that helps users learn and practice Tajweed rules while reciting Surah Al-Fatiha. The application uses speech recognition to provide real-time feedback on recitation and highlights Tajweed rules.

## Features

- Real-time speech recognition for Arabic recitation
- Interactive word-by-word highlighting
- Tajweed rules visualization
- Dark/Light mode support
- Instant feedback on recitation
- English translations and transliterations

## Prerequisites

- Python 3.8+
- FFmpeg
- Web browser with microphone support

## Setup

1. Clone the repository:
```bash
git clone [your-repo-url]
cd tajweed-bot
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install FFmpeg:
- macOS: `brew install ffmpeg`
- Windows: Download from FFmpeg website
- Linux: `sudo apt-get install ffmpeg`

## Running the Application

1. Activate the virtual environment if not already activated:
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Start the Flask server:
```bash
python app.py
```

3. Open your web browser and navigate to `http://localhost:5000`

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
