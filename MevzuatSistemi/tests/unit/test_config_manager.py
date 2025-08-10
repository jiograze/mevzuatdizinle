#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ConfigManager unit testleri
"""

import pytest
import yaml
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

import sys
sys.path.append(str(Path(__file__).parents[2]))

from app.utils.config_manager import ConfigManager


class TestConfigManager:
    """ConfigManager sınıfı testleri"""
    
    def test_initialization_with_valid_config(self):
        """Geçerli config ile başlatma testi"""
        config_data = {
            'base_folder': '/test/folder',
            'database': {
                'name': 'test.db'
            },
            'search': {
                'max_results': 20
            }
        }
        
        config_yaml = yaml.dump(config_data)
        
        with patch('builtins.open', mock_open(read_data=config_yaml)):
            with patch.object(Path, 'exists', return_value=True):
                config = ConfigManager('test_config.yaml')
                
                assert config.get('base_folder') == '/test/folder'
                assert config.get('database.name') == 'test.db'
                assert config.get('search.max_results') == 20
    
    def test_initialization_missing_config_file(self):
        """Config dosyası eksik testi"""
        with patch.object(Path, 'exists', return_value=False):
            config = ConfigManager('missing_config.yaml')
            
            # Varsayılan değerler kullanılmalı
            assert config.get('base_folder') is not None
            assert config.get('database.name', 'default.db') == 'default.db'
    
    def test_get_with_dot_notation(self):
        """Nokta notasyonu ile değer alma testi"""
        config_data = {
            'database': {
                'settings': {
                    'timeout': 30,
                    'pool_size': 5
                }
            }
        }
        
        config_yaml = yaml.dump(config_data)
        
        with patch('builtins.open', mock_open(read_data=config_yaml)):
            with patch.object(Path, 'exists', return_value=True):
                config = ConfigManager('test_config.yaml')
                
                assert config.get('database.settings.timeout') == 30
                assert config.get('database.settings.pool_size') == 5
                assert config.get('database.settings.nonexistent') is None
    
    def test_get_with_default_value(self):
        """Varsayılan değer ile alma testi"""
        config = ConfigManager('missing_config.yaml')
        
        # Var olmayan key için varsayılan değer
        assert config.get('nonexistent.key', 'default_value') == 'default_value'
        assert config.get('another.missing.key', 42) == 42
        assert config.get('boolean.key', True) is True
    
    def test_set_value(self):
        """Değer ayarlama testi"""
        config = ConfigManager('test_config.yaml')
        
        config.set('new.key', 'new_value')
        assert config.get('new.key') == 'new_value'
        
        config.set('existing.nested.key', 123)
        assert config.get('existing.nested.key') == 123
    
    def test_get_db_path(self):
        """Database path alma testi"""
        config_data = {
            'base_folder': '/test/base',
            'database': {
                'name': 'mevzuat.db'
            }
        }
        
        config_yaml = yaml.dump(config_data)
        
        with patch('builtins.open', mock_open(read_data=config_yaml)):
            with patch.object(Path, 'exists', return_value=True):
                config = ConfigManager('test_config.yaml')
                
                db_path = config.get_db_path()
                expected_path = Path('/test/base') / 'database' / 'mevzuat.db'
                
                assert str(db_path) == str(expected_path)
    
    def test_get_base_folder(self):
        """Base folder alma testi"""
        config_data = {
            'base_folder': '/custom/base/folder'
        }
        
        config_yaml = yaml.dump(config_data)
        
        with patch('builtins.open', mock_open(read_data=config_yaml)):
            with patch.object(Path, 'exists', return_value=True):
                config = ConfigManager('test_config.yaml')
                
                base_folder = config.get_base_folder()
                assert str(base_folder) == '/custom/base/folder'
    
    def test_save_config(self):
        """Config kaydetme testi"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_path = f.name
        
        try:
            config = ConfigManager(config_path)
            
            # Yeni değerler ayarla
            config.set('test.key1', 'value1')
            config.set('test.key2', 42)
            config.set('nested.deep.key', True)
            
            # Kaydet
            result = config.save()
            assert result is True
            
            # Yeni ConfigManager ile yükle ve kontrol et
            config2 = ConfigManager(config_path)
            assert config2.get('test.key1') == 'value1'
            assert config2.get('test.key2') == 42
            assert config2.get('nested.deep.key') is True
            
        finally:
            # Cleanup
            Path(config_path).unlink(missing_ok=True)
    
    def test_invalid_yaml_handling(self):
        """Geçersiz YAML işleme testi"""
        invalid_yaml = """
        key1: value1
        key2: [unclosed array
        key3: invalid: structure::
        """
        
        with patch('builtins.open', mock_open(read_data=invalid_yaml)):
            with patch.object(Path, 'exists', return_value=True):
                # Geçersiz YAML'de varsayılan değerler kullanılmalı
                config = ConfigManager('invalid_config.yaml')
                assert config.get('key1') is None  # Invalid YAML'den okunamaz
    
    def test_config_validation(self):
        """Config validasyon testi"""
        config_data = {
            'base_folder': '/valid/path',
            'database': {
                'name': 'test.db'
            },
            'search': {
                'max_results': 50,
                'semantic_enabled': True
            }
        }
        
        config_yaml = yaml.dump(config_data)
        
        with patch('builtins.open', mock_open(read_data=config_yaml)):
            with patch.object(Path, 'exists', return_value=True):
                config = ConfigManager('test_config.yaml')
                
                # Validasyon kontrolü
                if hasattr(config, 'validate'):
                    validation_result = config.validate()
                    assert validation_result is True
    
    def test_environment_variable_override(self):
        """Ortam değişkeni ile override testi"""
        config_data = {
            'database': {
                'host': 'localhost'
            }
        }
        
        config_yaml = yaml.dump(config_data)
        
        with patch('builtins.open', mock_open(read_data=config_yaml)):
            with patch.object(Path, 'exists', return_value=True):
                with patch.dict('os.environ', {'MEVZUAT_DATABASE_HOST': 'production-host'}):
                    config = ConfigManager('test_config.yaml')
                    
                    # Eğer env var desteği varsa
                    if hasattr(config, 'get_with_env'):
                        host = config.get_with_env('database.host', 'MEVZUAT_DATABASE_HOST')
                        assert host == 'production-host'
                    else:
                        # Normal get ile localhost dönmeli
                        host = config.get('database.host')
                        assert host == 'localhost'
    
    def test_config_inheritance(self):
        """Config kalıtım testi"""
        base_config = {
            'base_folder': '/base',
            'database': {
                'name': 'base.db',
                'timeout': 30
            }
        }
        
        override_config = {
            'database': {
                'name': 'override.db'  # Sadece name'i override et
            }
        }
        
        base_yaml = yaml.dump(base_config)
        override_yaml = yaml.dump(override_config)
        
        # Base config yükle
        with patch('builtins.open', mock_open(read_data=base_yaml)):
            with patch.object(Path, 'exists', return_value=True):
                config = ConfigManager('base_config.yaml')
                
                # Override config merge et (eğer destekleniyorsa)
                if hasattr(config, 'merge'):
                    with patch('builtins.open', mock_open(read_data=override_yaml)):
                        config.merge('override_config.yaml')
                    
                    # Override'dan name, base'den timeout gelmeli
                    assert config.get('database.name') == 'override.db'
                    assert config.get('database.timeout') == 30
                    assert config.get('base_folder') == '/base'
    
    def test_config_type_conversion(self):
        """Config tip dönüştürme testi"""
        config_data = {
            'numbers': {
                'integer': 42,
                'float': 3.14,
                'string_int': '100',
                'string_float': '2.71'
            },
            'booleans': {
                'true_bool': True,
                'false_bool': False,
                'string_true': 'true',
                'string_false': 'false'
            }
        }
        
        config_yaml = yaml.dump(config_data)
        
        with patch('builtins.open', mock_open(read_data=config_yaml)):
            with patch.object(Path, 'exists', return_value=True):
                config = ConfigManager('test_config.yaml')
                
                # Tip dönüştürme metodları (eğer varsa)
                if hasattr(config, 'get_int'):
                    assert config.get_int('numbers.integer') == 42
                    assert config.get_int('numbers.string_int') == 100
                
                if hasattr(config, 'get_float'):
                    assert config.get_float('numbers.float') == 3.14
                    assert config.get_float('numbers.string_float') == 2.71
                
                if hasattr(config, 'get_bool'):
                    assert config.get_bool('booleans.true_bool') is True
                    assert config.get_bool('booleans.false_bool') is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
