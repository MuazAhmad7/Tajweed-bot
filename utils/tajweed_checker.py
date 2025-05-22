# tajweed_checker.py
from .text_matcher import similar, normalize_arabic_text as text_matcher_normalize

ARABIC_MADD_LETTERS = ['ا', 'و', 'ي']

# Ayahs of Surah Fatiha with their word-by-word breakdown
SURAH_FATIHA = {
    0: {
        'text': "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ",
        'key_words': ['بسم', 'الله', 'الرحمن', 'الرحيم']
    },
    1: {
        'text': "ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَٰلَمِينَ",
        'key_words': ['الحمد', 'لله', 'رب', 'العالمين']
    },
    2: {
        'text': "ٱلرَّحْمَٰنِ ٱلرَّحِيمِ",
        'key_words': ['الرحمن', 'الرحيم']
    },
    3: {
        'text': "مَٰلِكِ يَوْمِ ٱلدِّينِ",
        'key_words': ['مالك', 'يوم', 'الدين']
    },
    4: {
        'text': "إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ",
        'key_words': ['إياك', 'نعبد', 'وإياك', 'نستعين']
    },
    5: {
        'text': "ٱهْدِنَا ٱلصِّرَٰطَ ٱلْمُسْتَقِيمَ",
        'key_words': ['اهدنا', 'الصراط', 'المستقيم']
    },
    6: {
        'text': "صِرَٰطَ ٱلَّذِينَ أَنْعَمْتَ عَلَيْهِمْ غَيْرِ ٱلْمَغْضُوبِ عَلَيْهِمْ وَلَا ٱلضَّآلِّينَ",
        'key_words': ['صراط', 'الذين', 'أنعمت', 'عليهم', 'غير', 'المغضوب', 'عليهم', 'ولا', 'الضالين']
    }
}

def normalize_arabic_text(text):
    """Remove diacritics and normalize Arabic text for comparison."""
    # Use the more comprehensive normalization from text_matcher
    return text_matcher_normalize(text)

def check_word_presence(expected_words, actual_text):
    """Check if all expected words are present in the recitation."""
    feedback = []
    
    # Normalize the actual text
    normalized_actual = normalize_arabic_text(actual_text)
    actual_words = set(normalized_actual.split())
    
    # Normalize expected words
    normalized_expected = [normalize_arabic_text(word) for word in expected_words]
    
    # Check for missing words
    missing_words = []
    for i, word in enumerate(normalized_expected):
        if not any(similar(word, actual_word) > 0.8 for actual_word in actual_words):
            missing_words.append(expected_words[i])  # Use original word for feedback
    
    if missing_words:
        if len(missing_words) == len(expected_words):
            feedback.append({
                'type': 'missing_words',
                'message': "⚠️ None of the expected words were found. Please make sure you're reciting the correct ayah."
            })
        else:
            feedback.append({
                'type': 'missing_words',
                'message': f"⚠️ Some words were not clearly pronounced: {', '.join(missing_words)}"
            })
    
    return feedback

def check_extra_content(expected_text, actual_text):
    """Check for any unexpected additional content in the recitation."""
    feedback = []
    normalized_expected = normalize_arabic_text(expected_text)
    normalized_actual = normalize_arabic_text(actual_text)
    
    # Split into words
    expected_words = set(normalized_expected.split())
    actual_words = set(normalized_actual.split())
    
    # Find extra words
    extra_words = set()
    for word in actual_words:
        if not any(similar(word, expected) > 0.8 for expected in expected_words):
            extra_words.add(word)
    
    if extra_words:
        if len(extra_words) > 3:
            feedback.append({
                'type': 'extra_content',
                'message': "⚠️ Several unexpected words detected. Please focus on reciting only the intended ayah."
            })
        else:
            feedback.append({
                'type': 'extra_content',
                'message': f"⚠️ Additional words detected: {', '.join(extra_words)}"
            })
    
    return feedback

def analyze_ayah(ayah_number: int, user_transcript: str):
    """
    Analyze a recited ayah focusing on what can be reliably detected:
    - Word presence/absence
    - Extra content
    - Basic pronunciation verification
    
    Args:
        ayah_number: The number of the ayah being recited (0-6 for Al-Fatiha)
        user_transcript: The Whisper-generated transcript of the user's recitation
        
    Returns:
        List of dictionaries containing feedback about detected issues
    """
    ayah_data = SURAH_FATIHA.get(ayah_number)
    if not ayah_data:
        return [{
            'type': 'error',
            'message': "⚠️ Invalid ayah number."
        }]
    
    issues = []
    
    # Normalize the transcript
    normalized_transcript = normalize_arabic_text(user_transcript)
    
    # Check word presence and basic pronunciation
    issues.extend(check_word_presence(ayah_data['key_words'], normalized_transcript))
    
    # Check for extra content
    issues.extend(check_extra_content(ayah_data['text'], normalized_transcript))
    
    if not issues:
        return [{
            'type': 'success',
            'message': "✅ Basic pronunciation check passed! Note: Detailed Tajweed rules like Madd duration, Ghunnah, Qalqalah, and Idghaam cannot be automatically verified."
        }]
    
    # Add disclaimer about limitations
    issues.append({
        'type': 'disclaimer',
        'message': "ℹ️ Note: This tool can only verify basic word presence and pronunciation. Detailed Tajweed rules require a qualified teacher."
    })
    
    return issues

def get_formatted_feedback(feedback_list):
    """Convert feedback list to formatted strings for display."""
    return [item['message'] for item in feedback_list] 