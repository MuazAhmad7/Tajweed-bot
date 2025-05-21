import json
from pathlib import Path
import re

def load_rules():
    """Load Tajweed rules from the JSON file."""
    rules_path = Path(__file__).parent.parent / 'data' / 'fatihah_rules.json'
    with open(rules_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def check_tajweed_rules(transcription):
    """
    Check the transcription against known Tajweed rules.
    Returns a list of matches and misses.
    """
    rules_data = load_rules()
    feedback = []
    
    # Convert transcription to a normalized form
    normalized_text = normalize_arabic_text(transcription)
    
    # Check each ayah's rules
    for ayah_rules in rules_data['rules']:
        ayah_num = ayah_rules['ayah']
        
        for rule in ayah_rules['rules']:
            word = rule['word']
            if word in normalized_text:
                feedback.append({
                    'ayah': ayah_num,
                    'type': rule['type'],
                    'word': word,
                    'status': 'correct',
                    'description': rule['description']
                })
            else:
                feedback.append({
                    'ayah': ayah_num,
                    'type': rule['type'],
                    'word': word,
                    'status': 'incorrect',
                    'description': rule['description']
                })
    
    return feedback

def normalize_arabic_text(text):
    """
    Normalize Arabic text by removing diacritics and standardizing characters.
    """
    # Remove diacritics
    text = re.sub(r'[\u064B-\u065F\u0670]', '', text)
    
    # Normalize alef variations
    text = re.sub(r'[إأآا]', 'ا', text)
    
    # Normalize tah marbuta
    text = text.replace('ة', 'ه')
    
    # Normalize alef maksura
    text = text.replace('ى', 'ي')
    
    return text

def format_feedback(feedback_list):
    """
    Format the feedback into a human-readable string.
    """
    if not feedback_list:
        return "No Tajweed rules were checked in this recitation."
    
    formatted = []
    for item in feedback_list:
        status_symbol = "✅" if item['status'] == 'correct' else "❌"
        formatted.append(
            f"{status_symbol} Ayah {item['ayah']} - {item['type'].title()}: "
            f"{item['word']} - {item['description']}"
        )
    
    return "\n".join(formatted)

def analyze_recitation(transcription):
    """
    Main function to analyze a recitation and return formatted feedback.
    """
    feedback = check_tajweed_rules(transcription)
    return format_feedback(feedback) 