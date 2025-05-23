# tajweed_checker.py
from .text_matcher import similar, normalize_arabic_text as text_matcher_normalize
from difflib import SequenceMatcher
import re

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

def check_specific_pronunciations(word, actual_text):
    """Check for specific pronunciation rules and common mistakes."""
    feedback = []
    
    # Normalize texts for comparison
    normalized_word = normalize_arabic_text(word)
    normalized_actual = normalize_arabic_text(actual_text)
    
    # Check for عليهم pronunciation
    if normalized_word == normalize_arabic_text("عليهم"):
        # Look for variations of alayhum (with different possible diacritics)
        alayhum_variations = ["عليهم", "عليهِم", "عليهُم", "عليهمْ", "عليهمُ"]
        correct_found = any(variant in actual_text for variant in ["عليهِم"])
        incorrect_found = any(
            "هُم" in word or "هُمْ" in word or "هُمُ" in word 
            for word in actual_text.split()
            if normalize_arabic_text(word) == normalize_arabic_text("عليهم")
        )
        
        if incorrect_found and not correct_found:
            feedback.append({
                'type': 'pronunciation_error',
                'message': "⚠️ Pronunciation Error: The word عليهم should be pronounced as 'alayhim', not 'alayhum'. The correct pronunciation is with a kasra (i) sound, not a damma (u) sound."
            })
    
    return feedback

def get_word_similarity(word1, word2):
    """Calculate similarity between two words."""
    return SequenceMatcher(None, word1, word2).ratio()

def is_phonetically_similar(word1, word2, threshold=0.7):
    """Check if two words are phonetically similar using Arabic phonetic rules."""
    # Arabic phonetic mappings (common substitutions)
    phonetic_mappings = {
        'ا': ['أ', 'إ', 'آ'],
        'و': ['ؤ'],
        'ي': ['ئ', 'ى'],
        'ه': ['ة'],
        'ث': ['س'],
        'ذ': ['ز'],
        'ض': ['د'],
        'ظ': ['ز'],
        'ط': ['ت'],
    }
    
    # Normalize both words
    w1 = normalize_arabic_text(word1)
    w2 = normalize_arabic_text(word2)
    
    # Direct similarity check
    if get_word_similarity(w1, w2) > threshold:
        return True
        
    # Apply phonetic substitutions and check again
    for char, alternatives in phonetic_mappings.items():
        for alt in alternatives:
            w1_mod = w1.replace(char, alt)
            w2_mod = w2.replace(char, alt)
            if get_word_similarity(w1_mod, w2_mod) > threshold:
                return True
    
    return False

def contains_hum_ending(word):
    """Check if a word ends with a 'hum' sound, accounting for various Arabic text representations."""
    # Remove common prefixes to isolate the ending
    word = normalize_arabic_text(word)
    endings_hum = ['هم', 'هُم', 'همُ', 'همْ', 'هُمْ', 'هُمُ']
    return any(word.endswith(ending) for ending in endings_hum)

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
    
    # Track alayhum mistakes to report multiple instances
    alayhum_positions = []
    
    # 1. Word Substitution and Mispronunciation
    for i, ref_word in enumerate(ref_words):
        if i < len(trans_words):
            trans_word = trans_words[i]
            norm_trans = normalize_arabic_text(trans_word)
            norm_ref = normalize_arabic_text(ref_word)
            
            # Special check for words that should end in 'him'
            if norm_ref == normalize_arabic_text("عليهم"):
                if contains_hum_ending(trans_word):
                    alayhum_positions.append(i)
                    mistakes.append({
                        "word": ref_word,
                        "type": "substitution",
                        "message": f"You said 'alayhum' instead of 'alayhim' at position {i+1}",
                        "severity": "critical",
                        "position": i
                    })
                    processed_words.add(trans_word)
                    continue
            
            # Regular word comparison
            if norm_trans != norm_ref:
                if is_phonetically_similar(trans_word, ref_word):
                    mistakes.append({
                        "word": ref_word,
                        "type": "mispronunciation",
                        "message": f"Mispronounced '{ref_word}' as '{trans_word}'",
                        "severity": "moderate",
                        "position": i
                    })
                else:
                    mistakes.append({
                        "word": ref_word,
                        "type": "substitution",
                        "message": f"Said '{trans_word}' instead of '{ref_word}'",
                        "severity": "critical",
                        "position": i
                    })
                processed_words.add(trans_word)
    
    # If multiple alayhum mistakes were found, add a summary message
    if len(alayhum_positions) > 1:
        positions_str = ", ".join(str(pos + 1) for pos in alayhum_positions)
        mistakes.append({
            "word": "عليهم",
            "type": "pattern_error",
            "message": f"⚠️ You consistently pronounced 'alayhum' instead of 'alayhim' at positions: {positions_str}. Remember to use kasra (i) sound, not damma (u) sound.",
            "severity": "critical",
            "positions": alayhum_positions
        })
    
    # Continue with other checks...
    # 2. Word Omission
    ref_set = set(normalize_arabic_text(w) for w in ref_words)
    trans_set = set(normalize_arabic_text(w) for w in trans_words)
    for word in ref_words:
        norm_word = normalize_arabic_text(word)
        if norm_word not in trans_set and not any(contains_hum_ending(w) for w in trans_words if normalize_arabic_text(w) == norm_word):
            position = ref_words.index(word)
            mistakes.append({
                "word": word,
                "type": "omission",
                "message": f"You skipped the word '{word}'. Make sure to recite every word.",
                "severity": "critical",
                "position": position
            })
    
    # 3. Word Insertion
    for i, word in enumerate(trans_words):
        if normalize_arabic_text(word) not in ref_set and word not in processed_words:
            mistakes.append({
                "word": word,
                "type": "insertion",
                "message": f"You added '{word}', which is not in this ayah.",
                "severity": "moderate",
                "position": i
            })
    
    # 4. Rhythm/Fluency Issues
    correct_words_positions = []
    for i, (trans, ref) in enumerate(zip(trans_words, ref_words)):
        if normalize_arabic_text(trans) == normalize_arabic_text(ref):
            correct_words_positions.append(i)
    
    for i in range(len(correct_words_positions) - 1):
        gap = correct_words_positions[i + 1] - correct_words_positions[i]
        if gap > 2:  # If there's a large gap between correct words
            mistakes.append({
                "word": "...",
                "type": "rhythm",
                "message": "Possible rhythm or fluency issue detected between words.",
                "severity": "minor",
                "position": correct_words_positions[i]
            })
    
    return mistakes

def analyze_ayah(ayah_number: int, user_transcript: str):
    """
    Analyze a recited ayah focusing on what can be reliably detected.
    """
    ayah_data = SURAH_FATIHA.get(ayah_number)
    if not ayah_data:
        return [{
            'type': 'error',
            'message': "⚠️ Invalid ayah number."
        }]
    
    # Analyze mistakes using the new system
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