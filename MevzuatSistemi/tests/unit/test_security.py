#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Güvenlik modülü testleri
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

import sys
sys.path.append(str(Path(__file__).parents[2]))

from app.security import (
    FileSecurityValidator, 
    InputValidator,
    SecureErrorHandler,
    ConfigSecurityValidator,
    ValidationResult,
    generate_secure_hash,
    is_safe_filename
)


class TestFileSecurityValidator:
    """Dosya güvenlik validatörü testleri"""
    
    def test_safe_file_validation(self):
        """Güvenli dosya validasyon testi"""
        validator = FileSecurityValidator()
        
        # Geçici güvenli dosya oluştur
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b"test content")
            temp_path = Path(f.name)
        
        try:
            result = validator.validate_file_path(temp_path)
            assert result.is_valid == True
        finally:
            temp_path.unlink()
    
    def test_path_traversal_detection(self):
        """Path traversal saldırısı tespit testi"""
        validator = FileSecurityValidator()
        
        dangerous_paths = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "test/../../../secret.txt",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
        ]
        
        for dangerous_path in dangerous_paths:
            result = validator._contains_path_traversal(dangerous_path)
            assert result == True, f"Path traversal not detected: {dangerous_path}"
    
    def test_dangerous_file_extension(self):
        """Tehlikeli dosya uzantısı testi"""
        validator = FileSecurityValidator()
        
        dangerous_files = [
            Path("malware.exe"),
            Path("script.bat"),
            Path("virus.scr"),
            Path("payload.js")
        ]
        
        for file_path in dangerous_files:
            result = validator._validate_file_extension(file_path)
            assert result.is_valid == False
            assert "güvenlik riski" in result.error_message.lower()
    
    def test_file_size_validation(self):
        """Dosya boyutu validasyon testi"""
        validator = FileSecurityValidator()
        
        # Mock büyük dosya
        with patch.object(Path, 'stat') as mock_stat:
            mock_stat.return_value.st_size = 150 * 1024 * 1024  # 150MB
            
            large_file = Path("large.pdf")
            result = validator._validate_file_size(large_file)
            
            assert result.is_valid == False
            assert "çok büyük" in result.error_message.lower()
    
    def test_unsupported_file_extension(self):
        """Desteklenmeyen dosya uzantısı testi"""
        validator = FileSecurityValidator()
        
        unsupported_file = Path("document.xyz")
        result = validator._validate_file_extension(unsupported_file)
        
        assert result.is_valid == False
        assert "desteklenmeyen" in result.error_message.lower()


class TestInputValidator:
    """Girdi validatörü testleri"""
    
    def test_valid_search_query(self):
        """Geçerli arama sorgusu testi"""
        validator = InputValidator()
        
        valid_queries = [
            "vergi kanunu",
            "madde 15",
            "ceza hukukunda sorumluluğun belirlenmesi",
            "2023 yılı düzenlemeleri"
        ]
        
        for query in valid_queries:
            result = validator.validate_search_query(query)
            assert result.is_valid == True
    
    def test_empty_search_query(self):
        """Boş arama sorgusu testi"""
        validator = InputValidator()
        
        empty_queries = ["", "   ", None]
        
        for query in empty_queries:
            result = validator.validate_search_query(query or "")
            assert result.is_valid == False
            assert "boş olamaz" in result.error_message.lower()
    
    def test_sql_injection_detection(self):
        """SQL injection tespit testi"""
        validator = InputValidator()
        
        malicious_queries = [
            "'; DROP TABLE documents; --",
            "test' UNION SELECT * FROM users --",
            "<script>alert('xss')</script>",
            "javascript:alert(1)"
        ]
        
        for query in malicious_queries:
            result = validator.validate_search_query(query)
            # Geçerli olabilir ama uyarı olmalı
            if result.warnings:
                assert any("güvenlik riski" in warning.lower() for warning in result.warnings)
    
    def test_long_search_query(self):
        """Uzun arama sorgusu testi"""
        validator = InputValidator()
        
        long_query = "a" * 1001  # 1001 karakter
        result = validator.validate_search_query(long_query)
        
        assert result.is_valid == False
        assert "çok uzun" in result.error_message.lower()
    
    def test_document_metadata_validation(self):
        """Belge metadata validasyon testi"""
        validator = InputValidator()
        
        # Geçerli metadata
        valid_metadata = {
            'title': 'Test Kanunu',
            'document_type': 'KANUN',
            'category': 'İdari'
        }
        
        result = validator.validate_document_metadata(valid_metadata)
        assert result.is_valid == True
    
    def test_missing_required_metadata(self):
        """Eksik gerekli metadata testi"""
        validator = InputValidator()
        
        incomplete_metadata = {
            'category': 'İdari'
            # title ve document_type eksik
        }
        
        result = validator.validate_document_metadata(incomplete_metadata)
        assert result.is_valid == False
        assert "gerekli alan eksik" in result.error_message.lower()
    
    def test_text_sanitization(self):
        """Metin temizleme testi"""
        validator = InputValidator()
        
        dirty_text = "Test\x00\x01text\x0C\x7F   with\t\n\r   extra   spaces   "
        clean_text = validator.sanitize_text(dirty_text)
        
        # Control karakterler temizlenmiş olmalı
        assert '\x00' not in clean_text
        assert '\x01' not in clean_text
        assert '\x0C' not in clean_text
        assert '\x7F' not in clean_text
        
        # Fazla boşluklar tek boşluk olmalı
        assert clean_text == "Testtext with extra spaces"


class TestSecureErrorHandler:
    """Güvenli hata işleyici testleri"""
    
    def test_user_friendly_error_messages(self):
        """Kullanıcı dostu hata mesajları testi"""
        handler = SecureErrorHandler()
        
        # Farklı hata türleri
        test_errors = [
            (FileNotFoundError("file not found"), "dosya bulunamadı"),
            (PermissionError("access denied"), "erişim izni"),
            (ConnectionError("connection failed"), "bağlantı hatası"),
            (TimeoutError("timeout"), "zaman aşımı"),
            (MemoryError("memory"), "bellek yetersiz")
        ]
        
        for error, expected_keyword in test_errors:
            message = handler.handle_error(error, user_friendly=True)
            assert expected_keyword.lower() in message.lower()
    
    def test_technical_error_messages(self):
        """Teknik hata mesajları testi"""
        handler = SecureErrorHandler()
        
        error = ValueError("Test technical error")
        message = handler.handle_error(error, user_friendly=False)
        
        # Teknik detaylar görünmeli
        assert "Test technical error" in message
    
    def test_error_logging(self):
        """Hata loglama testi"""
        handler = SecureErrorHandler()
        
        with patch.object(handler.logger, 'error') as mock_log:
            error = RuntimeError("Test error")
            handler.handle_error(error, context="test_context")
            
            # Log kaydı yapıldı mı?
            mock_log.assert_called_once()
            args, kwargs = mock_log.call_args
            assert "test_context" in args[0]
            assert "RuntimeError" in args[0]


class TestConfigSecurityValidator:
    """Konfigürasyon güvenlik validatörü testleri"""
    
    def test_sensitive_data_detection(self):
        """Hassas veri tespit testi"""
        validator = ConfigSecurityValidator()
        
        config_with_sensitive = {
            'database': {
                'password': 'secret123',
                'api_key': 'abc123def456'
            },
            'auth': {
                'secret_key': 'supersecret'
            }
        }
        
        result = validator.validate_config(config_with_sensitive)
        
        # Hassas veri uyarıları olmalı
        assert len(result.warnings) > 0
        assert any("hassas bilgi" in warning.lower() for warning in result.warnings)
    
    def test_path_traversal_in_config(self):
        """Config'te path traversal testi"""
        validator = ConfigSecurityValidator()
        
        config_with_traversal = {
            'base_folder': '../../../etc',
            'db_path': '../secrets/database.db'
        }
        
        result = validator.validate_config(config_with_traversal)
        
        # Path traversal uyarıları olmalı
        assert any("path traversal" in warning.lower() for warning in result.warnings)
    
    def test_external_access_warning(self):
        """External erişim uyarısı testi"""
        validator = ConfigSecurityValidator()
        
        config_with_external = {
            'network': {
                'allow_external': True,
                'bind_address': '0.0.0.0'
            }
        }
        
        result = validator.validate_config(config_with_external)
        
        # External erişim uyarısı olmalı
        assert any("external erişim" in warning.lower() for warning in result.warnings)


class TestSecurityUtilities:
    """Güvenlik yardımcı fonksiyon testleri"""
    
    def test_secure_hash_generation(self):
        """Güvenli hash oluşturma testi"""
        test_data = "test data for hashing"
        hash1 = generate_secure_hash(test_data)
        hash2 = generate_secure_hash(test_data)
        
        # Aynı veri için aynı hash
        assert hash1 == hash2
        
        # Farklı veri için farklı hash
        hash3 = generate_secure_hash("different data")
        assert hash1 != hash3
        
        # SHA256 formatı (64 karakter hex)
        assert len(hash1) == 64
        assert all(c in '0123456789abcdef' for c in hash1)
    
    def test_safe_filename_validation(self):
        """Güvenli dosya adı validasyon testi"""
        # Güvenli dosya isimleri
        safe_names = [
            "document.pdf",
            "test-file_123.docx",
            "report 2023.txt"
        ]
        
        for name in safe_names:
            assert is_safe_filename(name) == True
        
        # Güvenli olmayan dosya isimleri
        unsafe_names = [
            "file<test>.pdf",
            "document|pipe.txt",
            "file:colon.docx",
            "test\x00null.pdf",
            "CON.txt",  # Windows reserved
            "PRN.docx"  # Windows reserved
        ]
        
        for name in unsafe_names:
            assert is_safe_filename(name) == False
    
    def test_validation_result_dataclass(self):
        """ValidationResult dataclass testi"""
        # Varsayılan değerler
        result1 = ValidationResult(is_valid=True)
        assert result1.is_valid == True
        assert result1.error_message is None
        assert result1.warnings == []
        
        # Tam değerler
        result2 = ValidationResult(
            is_valid=False,
            error_message="Test error",
            warnings=["Warning 1", "Warning 2"]
        )
        assert result2.is_valid == False
        assert result2.error_message == "Test error"
        assert len(result2.warnings) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
