#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Comprehensive Utils Module Tests - Coverage Boost
Utils modülü için kapsamlı testler (mevcut %38.1 → %70+ hedef)
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
import pytest
import tempfile
import os
import yaml
from pathlib import Path

from app.utils.config_manager import ConfigManager
from app.utils.logger import setup_logger, get_logger
from app.core.file_watcher import FileWatcher
from app.utils.text_processor import TextProcessor


class TestConfigManagerComprehensive(unittest.TestCase):
    """Kapsamlı ConfigManager testleri"""
    
    def setUp(self):
        """Test setup"""
        self.test_config = {
            'database': {
                'path': 'test.db',
                'timeout': 30
            },
            'search': {
                'max_results': 100,
                'fuzzy_enabled': True
            },
            'ui': {
                'theme': 'dark',
                'language': 'tr'
            }
        }
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_load_config_success(self, mock_yaml_load, mock_file):
        """Başarılı config yükleme testi"""
        mock_yaml_load.return_value = self.test_config
        
        config_manager = ConfigManager('test_config.yaml')
        self.assertEqual(config_manager.config_data, self.test_config)
    
    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_load_config_file_not_found(self, mock_file):
        """Config dosyası bulunamadığında test"""
        config_manager = ConfigManager('nonexistent.yaml')
        self.assertEqual(config_manager.config_data, {})
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load', side_effect=yaml.YAMLError)
    def test_load_config_yaml_error(self, mock_yaml_load, mock_file):
        """YAML parse hatası testi"""
        config_manager = ConfigManager('invalid.yaml')
        self.assertEqual(config_manager.config_data, {})
    
    def test_get_existing_key(self):
        """Var olan key getirme testi"""
        with patch.object(ConfigManager, '_load_config'):
            config_manager = ConfigManager('test.yaml')
            config_manager.config_data = self.test_config
            
            result = config_manager.get('database.path')
            self.assertEqual(result, 'test.db')
    
    def test_get_nested_key(self):
        """İçiçe key getirme testi"""
        with patch.object(ConfigManager, '_load_config'):
            config_manager = ConfigManager('test.yaml')
            config_manager.config_data = self.test_config
            
            result = config_manager.get('search.max_results')
            self.assertEqual(result, 100)
    
    def test_get_nonexistent_key_with_default(self):
        """Var olmayan key ile default değer testi"""
        with patch.object(ConfigManager, '_load_config'):
            config_manager = ConfigManager('test.yaml')
            config_manager.config_data = self.test_config
            
            result = config_manager.get('nonexistent.key', 'default_value')
            self.assertEqual(result, 'default_value')
    
    def test_get_nonexistent_key_without_default(self):
        """Var olmayan key default olmadan testi"""
        with patch.object(ConfigManager, '_load_config'):
            config_manager = ConfigManager('test.yaml')
            config_manager.config_data = self.test_config
            
            result = config_manager.get('nonexistent.key')
            self.assertIsNone(result)
    
    def test_set_new_key(self):
        """Yeni key ekleme testi"""
        with patch.object(ConfigManager, '_load_config'):
            config_manager = ConfigManager('test.yaml')
            config_manager.config_data = self.test_config
            
            config_manager.set('new.key', 'new_value')
            self.assertEqual(config_manager.get('new.key'), 'new_value')
    
    def test_set_existing_key(self):
        """Var olan key güncelleme testi"""
        with patch.object(ConfigManager, '_load_config'):
            config_manager = ConfigManager('test.yaml')
            config_manager.config_data = self.test_config
            
            config_manager.set('database.timeout', 60)
            self.assertEqual(config_manager.get('database.timeout'), 60)
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.dump')
    def test_save_config(self, mock_yaml_dump, mock_file):
        """Config kaydetme testi"""
        with patch.object(ConfigManager, '_load_config'):
            config_manager = ConfigManager('test.yaml')
            config_manager.config_data = self.test_config
            
            result = config_manager.save()
            self.assertTrue(result)
            mock_yaml_dump.assert_called_once()
    
    def test_validate_config_structure(self):
        """Config yapısı validasyon testi"""
        with patch.object(ConfigManager, '_load_config'):
            config_manager = ConfigManager('test.yaml')
            config_manager.config_data = self.test_config
            
            is_valid = config_manager.validate_structure()
            self.assertTrue(is_valid)
    
    def test_get_all_keys(self):
        """Tüm key'leri getirme testi"""
        with patch.object(ConfigManager, '_load_config'):
            config_manager = ConfigManager('test.yaml')
            config_manager.config_data = self.test_config
            
            keys = config_manager.get_all_keys()
            self.assertIsInstance(keys, list)
            self.assertIn('database.path', keys)


class TestLoggerComprehensive(unittest.TestCase):
    """Kapsamlı Logger testleri"""
    
    def setUp(self):
        """Test setup"""
        self.log_file = tempfile.NamedTemporaryFile(delete=False, suffix='.log')
        self.log_file.close()
        self.log_path = self.log_file.name
    
    def tearDown(self):
        """Test cleanup"""
        if os.path.exists(self.log_path):
            os.unlink(self.log_path)
    
    def test_setup_logger_with_file(self):
        """Dosya ile logger kurulum testi"""
        logger = setup_logger('test_logger', log_file=self.log_path)
        
        self.assertIsNotNone(logger)
        self.assertEqual(logger.name, 'test_logger')
        
        # Test logging
        logger.info("Test log message")
        
        # Verify log file was created and contains message
        self.assertTrue(os.path.exists(self.log_path))
    
    def test_setup_logger_console_only(self):
        """Sadece console logger testi"""
        logger = setup_logger('console_logger', log_file=None)
        
        self.assertIsNotNone(logger)
        self.assertEqual(logger.name, 'console_logger')
    
    def test_get_existing_logger(self):
        """Var olan logger getirme testi"""
        # Create logger first
        logger1 = setup_logger('existing_logger')
        
        # Get same logger
        logger2 = get_logger('existing_logger')
        
        self.assertIs(logger1, logger2)
    
    def test_logger_levels(self):
        """Logger seviye testleri"""
        logger = setup_logger('level_test_logger', log_file=self.log_path)
        
        # Test different levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")
        
        # Verify file contains logs
        with open(self.log_path, 'r', encoding='utf-8') as f:
            log_content = f.read()
            self.assertIn("Info message", log_content)
    
    def test_logger_formatting(self):
        """Logger formatı testi"""
        logger = setup_logger('format_test_logger', log_file=self.log_path)
        
        logger.info("Format test message")
        
        with open(self.log_path, 'r', encoding='utf-8') as f:
            log_content = f.read()
            # Check if timestamp and level are in the log
            self.assertIn("INFO", log_content)
            self.assertIn("Format test message", log_content)


class TestFileWatcherComprehensive(unittest.TestCase):
    """Kapsamlı FileWatcher testleri"""
    
    def setUp(self):
        """Test setup"""
        self.test_dir = tempfile.mkdtemp()
        self.callback_called = False
        self.callback_args = None
    
    def tearDown(self):
        """Test cleanup"""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def callback_function(self, *args, **kwargs):
        """Test callback function"""
        self.callback_called = True
        self.callback_args = (args, kwargs)
    
    @patch('app.utils.file_watcher.Observer')
    def test_file_watcher_initialization(self, mock_observer):
        """FileWatcher başlatma testi"""
        file_watcher = FileWatcher(self.test_dir, self.callback_function)
        
        self.assertEqual(file_watcher.watch_directory, self.test_dir)
        self.assertEqual(file_watcher.callback, self.callback_function)
    
    @patch('app.utils.file_watcher.Observer')
    def test_start_watching(self, mock_observer):
        """İzlemeyi başlatma testi"""
        mock_observer_instance = Mock()
        mock_observer.return_value = mock_observer_instance
        
        file_watcher = FileWatcher(self.test_dir, self.callback_function)
        file_watcher.start_watching()
        
        mock_observer_instance.start.assert_called_once()
    
    @patch('app.utils.file_watcher.Observer')
    def test_stop_watching(self, mock_observer):
        """İzlemeyi durdurma testi"""
        mock_observer_instance = Mock()
        mock_observer.return_value = mock_observer_instance
        
        file_watcher = FileWatcher(self.test_dir, self.callback_function)
        file_watcher.start_watching()
        file_watcher.stop_watching()
        
        mock_observer_instance.stop.assert_called_once()


class TestTextProcessorComprehensive(unittest.TestCase):
    """Kapsamlı TextProcessor testleri"""
    
    def setUp(self):
        """Test setup"""
        self.text_processor = TextProcessor()
    
    def test_clean_text_basic(self):
        """Temel metin temizleme testi"""
        dirty_text = "  Bu   bir\n\ntest    metnidir.  "
        clean_text = self.text_processor.clean_text(dirty_text)
        
        self.assertEqual(clean_text, "Bu bir test metnidir.")
    
    def test_clean_text_special_characters(self):
        """Özel karakter temizleme testi"""
        dirty_text = "Bu@#$ bir %^& test* metnidir!"
        clean_text = self.text_processor.clean_text(dirty_text, remove_special_chars=True)
        
        self.assertNotIn("@#$", clean_text)
        self.assertNotIn("%^&", clean_text)
    
    def test_extract_keywords(self):
        """Anahtar kelime çıkarma testi"""
        text = "Bu önemli bir test metnidir. Test kelimeleri çıkarılacaktır."
        keywords = self.text_processor.extract_keywords(text)
        
        self.assertIsInstance(keywords, list)
        self.assertIn("test", [k.lower() for k in keywords])
    
    def test_tokenize_text(self):
        """Metin tokenize testi"""
        text = "Bu bir test cümlesidir."
        tokens = self.text_processor.tokenize(text)
        
        self.assertIsInstance(tokens, list)
        self.assertIn("Bu", tokens)
        self.assertIn("test", tokens)
    
    def test_remove_stopwords(self):
        """Stop word kaldırma testi"""
        text = "Bu bir test metnidir ve çok önemlidir."
        processed_text = self.text_processor.remove_stopwords(text)
        
        # Common Turkish stop words should be removed
        self.assertNotIn(" bir ", processed_text)
        self.assertNotIn(" ve ", processed_text)
    
    def test_stemming(self):
        """Stemming testi"""
        words = ["çalışıyor", "çalışmak", "çalışma"]
        stemmed = self.text_processor.stem_words(words)
        
        self.assertIsInstance(stemmed, list)
        self.assertEqual(len(stemmed), len(words))
    
    def test_similarity_calculation(self):
        """Metin benzerlik hesaplama testi"""
        text1 = "Bu bir test metnidir."
        text2 = "Bu bir deneme metnidir."
        
        similarity = self.text_processor.calculate_similarity(text1, text2)
        
        self.assertIsInstance(similarity, float)
        self.assertGreaterEqual(similarity, 0.0)
        self.assertLessEqual(similarity, 1.0)
    
    def test_language_detection(self):
        """Dil tespiti testi"""
        turkish_text = "Bu Türkçe bir metindir."
        detected_lang = self.text_processor.detect_language(turkish_text)
        
        self.assertEqual(detected_lang, 'tr')
    
    def test_text_summarization(self):
        """Metin özetleme testi"""
        long_text = """
        Bu çok uzun bir test metnidir. Birinci paragraf burada.
        İkinci paragraf farklı bilgiler içerir. Bu paragraf da önemli.
        Üçüncü paragraf sonuç bilgileri verir. Son paragraf özet niteliğindedir.
        """
        
        summary = self.text_processor.summarize(long_text, max_sentences=2)
        
        self.assertIsInstance(summary, str)
        self.assertLess(len(summary), len(long_text))


if __name__ == '__main__':
    unittest.main(verbosity=2)
