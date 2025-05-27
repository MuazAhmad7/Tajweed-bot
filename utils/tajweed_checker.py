# tajweed_checker.py
from .text_matcher import similar, normalize_arabic_text as text_matcher_normalize
from difflib import SequenceMatcher
import re
from flask import current_app

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
        'key_words': ['مٰلك', 'مالك', 'يوم', 'الدين']
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
    # First normalize using text_matcher's normalization
    text = text_matcher_normalize(text)
    
    # Special case for مَٰلِكِ and مَالِكِ
    text = re.sub('مَٰلِكِ|مَالِكِ|ملك|مٰلك', 'مالك', text)
    
    # Normalize all forms of madd and alif
    text = re.sub('[آٱأإاٰ]', 'ا', text)  # Normalize all alif forms including madd
    text = re.sub('ـٰ', '', text)         # Remove standalone madd symbol
    text = re.sub('ٰ', '', text)          # Remove superscript alif
    
    # Remove additional diacritical marks that might affect comparison
    text = re.sub('[\u064B-\u0652]', '', text)  # Remove all tashkeel (diacritics)
    text = re.sub('ـ', '', text)                # Remove tatweel (elongation)
    
    # Normalize other common variations
    text = re.sub('ى', 'ي', text)    # Normalize alif maqsura to ya
    text = re.sub('ة', 'ه', text)    # Normalize taa marbouta to haa
    
    # Remove any non-Arabic characters and extra spaces
    text = re.sub(r'[^\u0600-\u06FF\s]', '', text)
    return ' '.join(text.split())

def check_word_presence(expected_words, actual_text):
    """Check if all expected words are present in the recitation."""
    feedback = []
    
    # Normalize the actual text
    normalized_actual = normalize_arabic_text(actual_text)
    actual_words = set(normalized_actual.split())
    
    # Normalize expected words
    normalized_expected = [normalize_arabic_text(word) for word in expected_words]
    
    # Check for missing words (with more lenient matching)
    missing_words = []
    for i, word in enumerate(normalized_expected):
        if not any(similar(word, actual_word) > 0.7 for actual_word in actual_words):  # More lenient threshold
            # Double check with phonetic similarity before marking as missing
            if not any(is_phonetically_similar(word, actual_word) for actual_word in actual_words):
                missing_words.append(expected_words[i])
    
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

def get_word_similarity(word1, word2):
    """Calculate similarity between two words."""
    # Normalize both words
    word1 = normalize_arabic_text(word1)
    word2 = normalize_arabic_text(word2)
    
    # Use SequenceMatcher to get similarity ratio
    return SequenceMatcher(None, word1, word2).ratio()

def is_phonetically_similar(word1, word2, threshold=0.8):
    """Check if two words are phonetically similar."""
    # For now, just use text similarity
    return get_word_similarity(word1, word2) > threshold

def analyze_mistakes(transcribed_text, expected_text):
    """
    Analyze mistakes in the recitation based on ASR output.
    """
    mistakes = []
    
    # Tokenize both texts
    trans_words = transcribed_text.split()
    ref_words = expected_text.split()
    
    # Track processed words to avoid duplicate flags
    processed_words = set()
    
    # Special cases for common variations that can't be handled by normalization alone
    special_variations = {
        'العالمين': ['العالمين', 'العلمين'],  # Handle missing alif case
        'الرحمن': ['الرحمن'],
        'الرحيم': ['الرحيم']
    }
    
    # 1. Word Substitution and Mispronunciation
    for i, ref_word in enumerate(ref_words):
        if i < len(trans_words):
            trans_word = trans_words[i]
            norm_trans = normalize_arabic_text(trans_word)
            norm_ref = normalize_arabic_text(ref_word)
            
            # Check if this is a special case word
            is_special_match = False
            for base_word, variations in special_variations.items():
                if any(normalize_arabic_text(var) == norm_ref for var in variations) and \
                   any(normalize_arabic_text(var) == norm_trans for var in variations):
                    is_special_match = True
                    break
            
            if is_special_match:
                continue  # Skip further checks for this word
            
            # Regular word comparison
            if norm_trans != norm_ref and not is_phonetically_similar(trans_word, ref_word, 0.8):
                mistakes.append({
                    "word": ref_word,
                    "type": "substitution",
                    "message": f"Mispronounced '{ref_word}' as '{trans_word}'",
                    "severity": "critical",
                    "position": i
                })
                processed_words.add(trans_word)
    
    # 2. Word Omission (with special case handling)
    ref_set = set(normalize_arabic_text(w) for w in ref_words)
    trans_set = set(normalize_arabic_text(w) for w in trans_words)
    
    for word in ref_words:
        norm_word = normalize_arabic_text(word)
        # Check if the word or any of its variations are present
        is_present = False
        for variations in special_variations.values():
            if any(normalize_arabic_text(var) in trans_set for var in variations):
                is_present = True
                break
        
        if not is_present and norm_word not in trans_set:
            position = ref_words.index(word)
            mistakes.append({
                "word": word,
                "type": "omission",
                "message": f"You skipped the word '{word}'. Make sure to recite every word.",
                "severity": "critical",
                "position": position
            })
    
    return mistakes

def analyze_ayah(ayah_number: int, user_transcript: str):
    """
    Analyze a recited ayah focusing on what can be reliably detected.
    """
    # Debug logging
    current_app.logger.info(f"\nDEBUG: Analyzing ayah {ayah_number}")
    current_app.logger.info(f"DEBUG: Raw transcript: '{user_transcript}'")
    current_app.logger.info(f"DEBUG: Normalized transcript: '{normalize_arabic_text(user_transcript)}'")

    ayah_data = SURAH_FATIHA.get(ayah_number)
    if not ayah_data:
        return [{
            'type': 'error',
            'message': "⚠️ Invalid ayah number."
        }]
    
    # Special handling for Ar-Rahmanir-Raheem ayah (ayah 2)
    if ayah_number == 2:
        # Get the normalized words from the recitation
        norm_user = normalize_arabic_text(user_transcript)
        user_words = [w for w in norm_user.split() if w]  # Remove empty strings
        
        # Get the normalized expected words
        expected = normalize_arabic_text("الرحمن الرحيم")
        expected_words = [w for w in expected.split() if w]
        
        current_app.logger.info(f"DEBUG: User words: {user_words}")
        current_app.logger.info(f"DEBUG: Expected words: {expected_words}")
        
        # Check if we have exactly the right number of words
        if len(user_words) != len(expected_words):
            current_app.logger.info(f"DEBUG: Word count mismatch - got {len(user_words)}, expected {len(expected_words)}")
            return [{
                'type': 'wrong_ayah',
                'message': "⚠️ For this ayah, recite only 'Ar-Rahmanir-Raheem' (الرحمن الرحيم)."
            }]
        
        # Check each word individually with more lenient matching
        mistakes = []
        for i, (user_word, expected_word) in enumerate(zip(user_words, expected_words)):
            # Try different similarity checks
            direct_match = user_word == expected_word
            phonetic_match = is_phonetically_similar(user_word, expected_word, 0.7)  # More lenient threshold
            
            current_app.logger.info(f"DEBUG: Comparing '{user_word}' with '{expected_word}'")
            current_app.logger.info(f"DEBUG: Direct match: {direct_match}, Phonetic match: {phonetic_match}")
            
            if not direct_match and not phonetic_match:
                mistakes.append({
                    "word": expected_word,
                    "type": "substitution",
                    "message": f"Mispronounced '{expected_word}' as '{user_word}'",
                    "severity": "critical",
                    "position": i
                })
        
        if not mistakes:
            return [{
                'type': 'success',
                'message': "✅ Basic pronunciation check passed! Note: Detailed Tajweed rules like Madd duration, Ghunnah, Qalqalah, and Idghaam cannot be automatically verified."
            }]
        
        # Add disclaimer about limitations
        mistakes.append({
            'type': 'disclaimer',
            'message': "ℹ️ Note: This tool can only verify basic pronunciation and word accuracy. Detailed Tajweed rules require a qualified teacher."
        })
        
        return mistakes

    # For other ayahs, use the regular analysis
    mistakes = analyze_mistakes(user_transcript, ayah_data['text'])
    
    if not mistakes:
        return [{
            'type': 'success',
            'message': "✅ Basic pronunciation check passed! Note: Detailed Tajweed rules like Madd duration, Ghunnah, Qalqalah, and Idghaam cannot be automatically verified."
        }]
    
    # Convert mistakes to feedback format
    issues = []
    for mistake in mistakes:
        issues.append({
            'type': mistake['type'],
            'message': f"⚠️ {mistake['message']}"
        })
    
    # Add disclaimer about limitations
    issues.append({
        'type': 'disclaimer',
        'message': "ℹ️ Note: This tool can only verify basic pronunciation and word accuracy. Detailed Tajweed rules require a qualified teacher."
    })
    
    return issues

def get_formatted_feedback(feedback_list):
    """Convert feedback list to formatted strings for display."""
    return [item['message'] for item in feedback_list] 