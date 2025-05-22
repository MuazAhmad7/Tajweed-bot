import unittest
from utils.text_matcher import match_ayah_and_word, normalize_arabic_text
from utils.tajweed_checker import analyze_ayah

class TestTajweedMatching(unittest.TestCase):
    def test_ayah_1_matching(self):
        """Test matching of Ayah 1 (Al-Hamd)"""
        test_cases = [
            # Perfect match
            ("الحمد لله رب العالمين", (1, 0)),
            # With diacritics
            ("ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَٰلَمِينَ", (1, 0)),
            # Common variations
            ("الحمد للة رب العلمين", (1, 0)),
            ("الحمدلله رب العالمين", (1, 0)),
            # Partial recitation
            ("الحمد لله", (1, 0)),
            ("رب العالمين", (1, 2)),
        ]
        
        for text, expected in test_cases:
            ayah_num, word_idx = match_ayah_and_word(text)
            self.assertEqual((ayah_num, word_idx), expected, 
                           f"Failed to match '{text}'. Got {(ayah_num, word_idx)}, expected {expected}")
    
    def test_feedback_messages(self):
        """Test feedback messages for various recitation scenarios"""
        test_cases = [
            # Perfect recitation
            {
                'text': "الحمد لله رب العالمين",
                'ayah': 1,
                'expect_success': True
            },
            # Missing words
            {
                'text': "الحمد رب",
                'ayah': 1,
                'expect_missing': ['لله', 'العالمين']
            },
            # Extra words
            {
                'text': "الحمد لله رب العالمين الرحمن",
                'ayah': 1,
                'expect_extra': True
            },
            # Wrong ayah
            {
                'text': "اهدنا الصراط المستقيم",
                'ayah': 1,
                'expect_wrong_ayah': True
            }
        ]
        
        for case in test_cases:
            feedback = analyze_ayah(case['ayah'], case['text'])
            
            if case.get('expect_success'):
                self.assertTrue(any(msg['type'] == 'success' for msg in feedback),
                              f"Expected success for '{case['text']}' but got: {feedback}")
            
            if case.get('expect_missing'):
                missing_msg = next((msg for msg in feedback if msg['type'] == 'missing_words'), None)
                self.assertIsNotNone(missing_msg, f"Expected missing words feedback for '{case['text']}'")
                for word in case['expect_missing']:
                    self.assertIn(word, missing_msg['message'])
            
            if case.get('expect_extra'):
                self.assertTrue(any(msg['type'] == 'extra_content' for msg in feedback),
                              f"Expected extra content feedback for '{case['text']}'")
            
            if case.get('expect_wrong_ayah'):
                self.assertTrue(any('none of the expected words' in msg['message'].lower() 
                                  for msg in feedback),
                              f"Expected wrong ayah feedback for '{case['text']}'")
    
    def test_normalize_arabic_text(self):
        """Test Arabic text normalization"""
        test_cases = [
            # Diacritics removal
            ("ٱلْحَمْدُ", "الحمد"),
            # Alef variations
            ("إِيَّاكَ", "اياك"),
            # Letter variations
            ("صِرَٰطَ", "صراط"),
            # Combined cases
            ("ٱلرَّحْمَٰنِ ٱلرَّحِيمِ", "الرحمن الرحيم")
        ]
        
        for text, expected in test_cases:
            normalized = normalize_arabic_text(text)
            self.assertEqual(normalized, expected,
                           f"Normalization failed for '{text}'. Got '{normalized}', expected '{expected}'")

if __name__ == '__main__':
    unittest.main() 