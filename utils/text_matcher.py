from difflib import SequenceMatcher
import re

# Fatiha verses with their word-by-word text
FATIHA_VERSES = {
    1: ["بِسْمِ", "ٱللَّهِ", "ٱلرَّحْمَٰنِ", "ٱلرَّحِيمِ"],
    2: ["ٱلْحَمْدُ", "لِلَّهِ", "رَبِّ", "ٱلْعَٰلَمِينَ"],
    3: ["ٱلرَّحْمَٰنِ", "ٱلرَّحِيمِ"],
    4: ["مَٰلِكِ", "يَوْمِ", "ٱلدِّينِ"],
    5: ["إِيَّاكَ", "نَعْبُدُ", "وَإِيَّاكَ", "نَسْتَعِينُ"],
    6: ["ٱهْدِنَا", "ٱلصِّرَٰطَ", "ٱلْمُسْتَقِيمَ"],
    7: ["صِرَٰطَ", "ٱلَّذِينَ", "أَنْعَمْتَ", "عَلَيْهِمْ", "غَيْرِ", "ٱلْمَغْضُوبِ", "عَلَيْهِمْ", "وَلَا", "ٱلضَّآلِّينَ"]
}

# Phonetic mapping for common variations
PHONETIC_MAPPING = {
    'ا': ['ى', 'آ', 'أ', 'إ'],
    'ه': ['ة'],
    'ي': ['ى', 'ئ'],
    'و': ['ؤ'],
    'س': ['ص'],
    'ت': ['ط'],
    'ذ': ['ز', 'ظ'],
    'د': ['ض'],
    'ح': ['ه'],
    'ك': ['ق'],
}

def normalize_arabic_text(text):
    """Normalize Arabic text by removing diacritics and normalizing letters."""
    # Remove diacritics
    text = re.sub(r'[\u064B-\u065F\u0670]', '', text)
    
    # Normalize alef variations
    text = re.sub('[آأإٱ]', 'ا', text)
    
    # Normalize other common variations
    text = re.sub('ة', 'ه', text)
    text = re.sub('[ىئ]', 'ي', text)
    text = re.sub('ؤ', 'و', text)
    
    return text

def get_phonetic_variations(word):
    """Generate phonetic variations of a word."""
    variations = {word}
    normalized = normalize_arabic_text(word)
    variations.add(normalized)
    
    # Generate variations based on phonetic mapping
    for char in normalized:
        if char in PHONETIC_MAPPING:
            for variant in PHONETIC_MAPPING[char]:
                variations.add(normalized.replace(char, variant))
    
    return variations

def similar(a, b):
    """Calculate similarity ratio between two strings."""
    # Compare normalized versions
    a_norm = normalize_arabic_text(a)
    b_norm = normalize_arabic_text(b)
    
    # Get base similarity
    base_similarity = SequenceMatcher(None, a_norm, b_norm).ratio()
    
    # Check phonetic variations
    a_variations = get_phonetic_variations(a)
    b_variations = get_phonetic_variations(b)
    
    # Get best similarity score among all variations
    max_similarity = base_similarity
    for var_a in a_variations:
        for var_b in b_variations:
            similarity = SequenceMatcher(None, var_a, var_b).ratio()
            max_similarity = max(max_similarity, similarity)
    
    return max_similarity

def match_ayah_and_word(transcribed_text):
    """
    Match transcribed text with Fatiha verses and identify the current ayah and word.
    
    Args:
        transcribed_text (str): The transcribed Arabic text from Whisper
        
    Returns:
        tuple: (ayah_number, word_index) or (None, None) if no match found
    """
    best_match = (None, None)
    highest_similarity = 0.5  # Lower threshold for more lenient matching
    
    # Clean up the transcribed text
    transcribed_text = transcribed_text.strip()
    
    # Split transcribed text into words
    transcribed_words = transcribed_text.split()
    
    # Try to match each transcribed word with each word in Fatiha
    for word in transcribed_words:
        for ayah_num, ayah_words in FATIHA_VERSES.items():
            for i, ayah_word in enumerate(ayah_words):
                # Calculate similarity including phonetic variations
                similarity = similar(word, ayah_word)
                
                if similarity > highest_similarity:
                    highest_similarity = similarity
                    best_match = (ayah_num, i)
    
    return best_match

def get_context(ayah_number, word_index, window=2):
    """
    Get surrounding words for context.
    
    Args:
        ayah_number (int): The ayah number
        word_index (int): The index of the current word
        window (int): Number of words to include before and after
        
    Returns:
        list: List of surrounding words
    """
    if ayah_number not in FATIHA_VERSES:
        return []
        
    words = FATIHA_VERSES[ayah_number]
    start = max(0, word_index - window)
    end = min(len(words), word_index + window + 1)
    
    return words[start:end] 