"""
Testy modułu utils.config
"""
import os
import unittest
import tempfile
import yaml

from utils.config import load_config, get_default_config, merge_configs
from utils.exceptions import ConfigError


class TestConfig(unittest.TestCase):
    """Testy dla modułu utils.config."""
    
    def test_load_config(self):
        """Test wczytywania konfiguracji z pliku."""
        # Tworzenie tymczasowego pliku konfiguracyjnego
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
            yaml.dump({'test_key': 'test_value'}, f)
            config_path = f.name
        
        try:
            # Wczytanie konfiguracji z pliku
            config = load_config(config_path)
            
            # Sprawdzenie, czy konfiguracja została poprawnie wczytana
            self.assertEqual(config['test_key'], 'test_value')
        finally:
            # Usunięcie tymczasowego pliku
            os.unlink(config_path)
    
    def test_load_config_file_not_found(self):
        """Test wczytywania konfiguracji z nieistniejącego pliku."""
        # Sprawdzenie, czy zostanie zgłoszony wyjątek ConfigError
        with self.assertRaises(ConfigError):
            load_config('nonexistent_file.yaml')
    
    def test_get_default_config(self):
        """Test pobierania domyślnej konfiguracji."""
        # Pobranie domyślnej konfiguracji
        config = get_default_config()
        
        # Sprawdzenie, czy konfiguracja zawiera oczekiwane klucze
        self.assertIn('quality', config)
        self.assertIn('landscape', config)
        self.assertIn('short_size', config)
        self.assertIn('aspect_ratio', config)
        self.assertIn('background', config)
        self.assertIn('document', config)
        self.assertIn('effect', config)
    
    def test_merge_configs(self):
        """Test łączenia konfiguracji."""
        # Domyślna konfiguracja
        default_config = {
            'key1': 'value1',
            'key2': {
                'subkey1': 'subvalue1',
                'subkey2': 'subvalue2'
            }
        }
        
        # Konfiguracja użytkownika
        user_config = {
            'key2': {
                'subkey1': 'new_subvalue1',
                'subkey3': 'subvalue3'
            },
            'key3': 'value3'
        }
        
        # Łączenie konfiguracji
        merged_config = merge_configs(default_config, user_config)
        
        # Sprawdzenie, czy konfiguracja została poprawnie połączona
        self.assertEqual(merged_config['key1'], 'value1')
        self.assertEqual(merged_config['key2']['subkey1'], 'new_subvalue1')
        self.assertEqual(merged_config['key2']['subkey2'], 'subvalue2')
        self.assertEqual(merged_config['key2']['subkey3'], 'subvalue3')
        self.assertEqual(merged_config['key3'], 'value3')
    
    def test_merge_configs_with_none(self):
        """Test łączenia konfiguracji z None."""
        # Domyślna konfiguracja
        default_config = {'key': 'value'}
        
        # Łączenie konfiguracji z None
        merged_config = merge_configs(default_config, None)
        
        # Sprawdzenie, czy konfiguracja nie została zmieniona
        self.assertEqual(merged_config, default_config)


if __name__ == '__main__':
    unittest.main()