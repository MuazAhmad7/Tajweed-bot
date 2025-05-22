from difflib import SequenceMatcher

import re

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
    # Special cases mapping (before diacritic removal)
    special_cases = {
        'صِرَٰطَ': 'صراط',
        'ٱلصِّرَٰطَ': 'الصراط',
        'صِرَٰطَ': 'صراط',
        'صِرَط': 'صراط',
        'صرط': 'صراط'
    }
    
    # First handle special cases
    for case, replacement in special_cases.items():
        text = text.replace(case, replacement)
    
    # Remove diacritics (harakat)
    text = re.sub(r'[\u064B-\u065F\u0670]', '', text)
    
    # Remove tatweel (elongation character)
    text = re.sub('\u0640', '', text)
    
    # Normalize alef variations
    text = re.sub('[آأإٱا]', 'ا', text)
    
    # Normalize other common variations
    text = re.sub('ة', 'ه', text)
    text = re.sub('[ىئ]', 'ي', text)
    text = re.sub('ؤ', 'و', text)
    
    # Remove any non-Arabic characters and extra spaces
    text = re.sub(r'[^\u0600-\u06FF\s]', '', text)
    text = ' '.join(text.split())
    
    # Final check for special cases (after normalization)
    for case, replacement in special_cases.items():
        text = text.replace(normalize_without_special_cases(case), replacement)
    
    return text

def normalize_without_special_cases(text):
    """Normalize text without applying special case rules."""
    import re
    text = re.sub(r'[\u064B-\u065F\u0670]', '', text)
    text = re.sub('\u0640', '', text)
    text = re.sub('[آأإٱا]', 'ا', text)
    text = re.sub('ة', 'ه', text)
    text = re.sub('[ىئ]', 'ي', text)
    text = re.sub('ؤ', 'و', text)
    text = re.sub(r'[^\u0600-\u06FF\s]', '', text)
    return ' '.join(text.split())

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
    highest_similarity = 0.5  # Threshold for matching
    
    # Clean up and normalize the transcribed text
    transcribed_text = normalize_arabic_text(transcribed_text.strip())
    transcribed_words = transcribed_text.split()
    
    # If no words were transcribed, return no match
    if not transcribed_words:
        return (None, None)
    
    # For each ayah, try to find the best matching word sequence
    for ayah_num, ayah_words in FATIHA_VERSES.items():
        # Normalize each word in the ayah
        normalized_ayah_words = [normalize_arabic_text(word) for word in ayah_words]
        ayah_text = ' '.join(normalized_ayah_words)
        
        # Try matching the full transcribed text against the full ayah
        full_similarity = similar(transcribed_text, ayah_text)
        if full_similarity > 0.8:  # High confidence full ayah match
            return (ayah_num, 0)
        
        # Try matching word sequences
        for i in range(len(normalized_ayah_words)):
            # Try different window sizes
            for window_size in range(1, min(len(transcribed_words) + 1, len(normalized_ayah_words) - i + 1)):
                ayah_window = ' '.join(normalized_ayah_words[i:i + window_size])
                
                # Try matching against different parts of the transcribed text
                for j in range(len(transcribed_words) - window_size + 1):
                    transcribed_window = ' '.join(transcribed_words[j:j + window_size])
                    similarity = similar(transcribed_window, ayah_window)
                    
                    if similarity > highest_similarity:
                        highest_similarity = similarity
                        best_match = (ayah_num, i)
                        
                        # If we have a very good match, return immediately
                        if similarity > 0.9:
                            return best_match
    
    # Only return matches that meet our minimum threshold
    if highest_similarity > 0.5:
        return best_match
    return (None, None)

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