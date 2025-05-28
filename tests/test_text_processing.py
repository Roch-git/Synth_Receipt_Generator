"""
Testy modułu utils.text_processing
"""
import unittest

from utils.text_processing import format_number, split_long_text, weighted_choice, format_price


class TestTextProcessing(unittest.TestCase):
    """Testy dla modułu utils.text_processing."""
    
    def test_format_number(self):
        """Test formatowania liczby."""
        # Test formatowania liczby z domyślnym separatorem
        self.assertEqual(format_number(123.45), '123.45')
        
        # Test formatowania liczby z innym separatorem
        self.assertEqual(format_number(123.45, ','), '123,45')
        
        # Test formatowania liczby z inną liczbą miejsc po przecinku
        self.assertEqual(format_number(123.45, '.', 3), '123.450')
    
    def test_split_long_text(self):
        """Test dzielenia długiego tekstu na fragmenty."""
        # Test dzielenia tekstu na fragmenty o długości 5
        self.assertEqual(
            split_long_text('abcdefghij', 5),
            ['abcde', 'fghij']
        )
        
        # Test dzielenia tekstu na fragmenty o długości 3
        self.assertEqual(
            split_long_text('abcdefghij', 3),
            ['abc', 'def', 'ghi', 'j']
        )
        
        # Test dzielenia krótkiego tekstu
        self.assertEqual(
            split_long_text('abc', 5),
            ['abc']
        )
    
    def test_weighted_choice(self):
        """Test wybierania elementu z listy opcji na podstawie wag."""
        # Opcje z równymi wagami
        options = [
            {'value': 'A', 'weight': 1},
            {'value': 'B', 'weight': 1},
            {'value': 'C', 'weight': 1}
        ]
        
        # Sprawdzenie, czy wybierany jest jeden z elementów
        choice = weighted_choice(options, 'value')
        self.assertIn(choice, ['A', 'B', 'C'])
        
        # Test wybierania z pustej listy
        self.assertIsNone(weighted_choice([], 'value'))
        
        # Test wybierania z listy zawierającej jeden element
        self.assertEqual(
            weighted_choice([{'value': 'A', 'weight': 1}], 'value'),
            'A'
        )
    
    def test_format_price(self):
        """Test formatowania ceny produktu."""
        # Test formatowania ceny w standardowym formacie
        self.assertEqual(
            format_price(
                quantity=2,
                unit_price=3.50,
                total_price=7.00,
                vat_symbol='A',
                unit='szt.',
                multiply_sign='x',
                decimal_separator='.',
                price_format='standard'
            ),
            '2 szt. x 3.50 = 7.00 A'
        )
        
        # Test formatowania ceny bez jednostki
        self.assertEqual(
            format_price(
                quantity=2,
                unit_price=3.50,
                total_price=7.00,
                vat_symbol='A',
                unit='',
                multiply_sign='x',
                decimal_separator='.',
                price_format='standard'
            ),
            '2 x 3.50 = 7.00 A'
        )
        
        # Test formatowania ceny w formacie bez spacji
        self.assertEqual(
            format_price(
                quantity=2,
                unit_price=3.50,
                total_price=7.00,
                vat_symbol='A',
                unit='szt.',
                multiply_sign='x',
                decimal_separator='.',
                price_format='no_spaces'
            ),
            '2szt.x3.50=7.00A'
        )
        
        # Test formatowania ceny w formacie hybrydowym
        self.assertEqual(
            format_price(
                quantity=2,
                unit_price=3.50,
                total_price=7.00,
                vat_symbol='A',
                unit='szt.',
                multiply_sign='x',
                decimal_separator='.',
                price_format='hybrid'
            ),
            '2 szt. x 3.50 = 7.00A'
        )


if __name__ == '__main__':
    unittest.main()