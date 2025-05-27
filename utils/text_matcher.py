from difflib import SequenceMatcher

import re

# Fatiha verses with their word-by-word text, including ASR-friendly variations
FATIHA_VERSES = {
    0: ["بسم", "الله", "الرحمن", "الرحيم"],  # Simplified without diacritics
    1: ["الحمد", "لله", "رب", "العالمين"],
    2: ["الرحمن", "الرحيم"],
    3: ["مالك", "مٰلك", "يوم", "الدين"],  # Added both forms of Maliki
    4: ["اياك", "نعبد", "واياك", "نستعين"],
    5: ["اهدنا", "الصراط", "المستقيم"],
    6: ["صراط", "الذين", "انعمت", "عليهم", "غير", "المغضوب", "عليهم", "ولا", "الضالين"]
}

# Phonetic mapping for common variations
PHONETIC_MAPPING = {
    'ا': ['ى', 'آ', 'أ', 'إ', 'ٱ', 'ٰ'],  # Added superscript alif
    'ه': ['ة'],
    'ي': ['ى', 'ئ'],
    'و': ['ؤ'],
    'س': ['ص'],
    'ت': ['ط'],
    'ذ': ['ز', 'ظ'],
    'د': ['ض'],
    'ح': ['ه'],
    'ك': ['ق'],
    'م': ['مٰ', 'مَٰ']  # Added madd variations for meem
}

# Add specific mappings for words with madd
MADD_WORD_MAPPING = {
    # Bismillah (Ayah 0)
    'الرحمن': ['الرحمٰن', 'الرحمان'],
    'الرحيم': ['الرحيم'],  # No madd variation but included for completeness
    
    # Al-Hamd (Ayah 1)
    'العالمين': ['العٰلمين', 'العالمين'],
    
    # Ar-Rahman Ar-Raheem (Ayah 2)
    # Already covered in Ayah 0
    
    # Maaliki Yawm id-Deen (Ayah 3)
    'مالك': ['مٰلك', 'مالك'],
    
    # Iyyaka Na'budu (Ayah 4)
    # No madd variations
    
    # Ihdina (Ayah 5)
    'الصراط': ['الصرٰط', 'الصراط'],
    'المستقيم': ['المستقيم'],  # Has madd in ي but that's handled differently
    
    # Siratal-ladhina (Ayah 6)
    'صراط': ['صرٰط', 'صراط'],
    'الذين': ['الذين'],  # Has madd in ي but that's handled differently
    'الضالين': ['الضٰلين', 'الضالين', 'الضآلين']  # Also handle آ form
}

def normalize_arabic_text(text):
    """Normalize Arabic text by removing diacritics and normalizing letters."""
    # First normalize madd and special characters
    text = re.sub('[آٱأإا]', 'ا', text)  # Normalize all alif forms
    text = re.sub('ـٰ', 'ا', text)        # Convert standalone madd to alif
    text = re.sub('ٰ', 'ا', text)         # Convert superscript alif to regular alif
    
    # Handle specific words with madd
    normalized = text
    for base_word, variations in MADD_WORD_MAPPING.items():
        pattern = '|'.join(map(re.escape, variations))
        normalized = re.sub(pattern, base_word, normalized)
    
    # Handle ya with madd (ي) separately since it's a different case
    normalized = re.sub('يْ', 'ي', normalized)  # Remove sukoon from ya
    normalized = re.sub('يِّ', 'ي', normalized)  # Remove shadda and kasra from ya
    
    # Remove ALL diacritical marks
    normalized = re.sub(r'[\u064B-\u065F\u0670]', '', normalized)  # Remove all tashkeel
    normalized = re.sub('ـ', '', normalized)                       # Remove tatweel
    
    # Normalize other letters
    normalized = re.sub('ة', 'ه', normalized)    # Normalize taa marbouta
    normalized = re.sub('[ىئ]', 'ي', normalized)  # Normalize ya variations
    normalized = re.sub('ؤ', 'و', normalized)     # Normalize waw
    
    # Remove any non-Arabic characters
    normalized = re.sub(r'[^\u0600-\u06FF\s]', '', normalized)
    
    # Remove extra spaces and return
    return ' '.join(normalized.split())

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
    # First normalize both strings
    a_norm = normalize_arabic_text(a)
    b_norm = normalize_arabic_text(b)
    
    # Direct comparison after normalization
    if a_norm == b_norm:
        return 1.0
    
    # Special handling for common words with more lenient matching
    common_words = ['بسم', 'الله', 'الرحمن', 'الرحيم']
    if a_norm in common_words or b_norm in common_words:
        base_similarity = SequenceMatcher(None, a_norm, b_norm).ratio()
        if base_similarity > 0.7:  # More lenient threshold for common words
            return 1.0
    
    # Get base similarity
    base_similarity = SequenceMatcher(None, a_norm, b_norm).ratio()
    
    # Check phonetic variations
    a_variations = get_phonetic_variations(a)
    b_variations = get_phonetic_variations(b)
    
    # Get best similarity score among all variations
    max_similarity = base_similarity
    for var_a in a_variations:
        for var_b in b_variations:
            # Check exact match first
            if var_a == var_b:
                return 1.0
            # Then check similarity
            similarity = SequenceMatcher(None, var_a, var_b).ratio()
            max_similarity = max(max_similarity, similarity)
    
    # Be more lenient with the similarity threshold
    # If the strings are very close (>0.8), consider them a match
    if max_similarity > 0.8:
        return 1.0
    
    return max_similarity

def match_ayah_and_word(transcribed_text):
    """Match transcribed text with Fatiha verses and identify the current ayah and word."""
    # Clean up and normalize the transcribed text
    transcribed_text = normalize_arabic_text(transcribed_text.strip())
    transcribed_words = transcribed_text.split()
    
    print(f"DEBUG: Normalized transcribed text: {transcribed_text}")
    print(f"DEBUG: Transcribed words: {transcribed_words}")
    
    # If no words were transcribed, return no match
    if not transcribed_words:
        print("DEBUG: No words transcribed")
        return (None, None)
    
    # Special case: Check if this is Ar-Rahmani Raheem (ayah 2)
    norm_trans = ' '.join(transcribed_words)
    print(f"DEBUG: Checking Ar-Rahmani Raheem case. Text: {norm_trans}")
    print(f"DEBUG: Contains رحمن/رحمان: {'رحمن' in norm_trans or 'رحمان' in norm_trans}")
    print(f"DEBUG: Contains الرحمن/الرحمان: {'الرحمن' in norm_trans or 'الرحمان' in norm_trans}")
    print(f"DEBUG: Contains رحيم: {'رحيم' in norm_trans}")
    print(f"DEBUG: Contains الرحيم: {'الرحيم' in norm_trans}")
    print(f"DEBUG: Contains بسم: {'بسم' in norm_trans}")
    print(f"DEBUG: Contains الله: {'الله' in norm_trans}")
    
    if len(transcribed_words) <= 3:  # Allow for slight ASR variations
        if ('رحمن' in norm_trans or 'الرحمن' in norm_trans or 'رحمان' in norm_trans or 'الرحمان' in norm_trans) and \
           ('رحيم' in norm_trans or 'الرحيم' in norm_trans):
            # Make sure it's not Bismillah by checking for absence of بسم and الله
            if 'بسم' not in norm_trans and 'الله' not in norm_trans:
                print("DEBUG: Matched as Ar-Rahmani Raheem (ayah 2)")
                return (2, 0)

    # First try exact matches for key words that uniquely identify ayahs
    unique_identifiers = {
        0: [["بسم", "الله"]],  # Must have BOTH for Bismillah
        1: ["الحمد"],  # Only appears in ayah 1
        2: [["الرحمن", "الرحمان"], ["الرحيم"]],  # Must have both Rahman/Rahman AND Raheem
        3: ["مالك", "يوم", "الدين"],  # Only appears in ayah 3
        4: ["نعبد", "نستعين"],  # Only appears in ayah 4
        5: ["اهدنا", "الصراط"],  # Only appears in ayah 5
        6: ["انعمت", "المغضوب", "الضالين"]  # Only appears in ayah 6
    }
    
    # Check for unique identifiers first
    for ayah_num, identifiers in unique_identifiers.items():
        print(f"DEBUG: Checking ayah {ayah_num} identifiers")
        if isinstance(identifiers[0], list):
            # For cases where we need ALL words to match (like Bismillah)
            matches_all = True
            for required_group in identifiers:
                if not any(normalize_arabic_text(word) in norm_trans for word in required_group):
                    matches_all = False
                    break
            if matches_all:
                print(f"DEBUG: Matched all required words for ayah {ayah_num}")
                return (ayah_num, 0)
        else:
            # For cases where ANY word can match
            if any(normalize_arabic_text(word) in norm_trans for word in identifiers):
                print(f"DEBUG: Matched identifier for ayah {ayah_num}")
                return (ayah_num, 0)
    
    print("DEBUG: No match found")
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