#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Güvenlik modülü - Input validation, file security, error handling
"""

import os
import hashlib
import mimetypes
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Validasyon sonucu"""
    is_valid: bool
    error_message: Optional[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class FileSecurityValidator:
    """Dosya güvenliği validatörü"""
    
    # Güvenli dosya uzantıları
    SAFE_EXTENSIONS = {
        '.pdf', '.txt', '.docx', '.doc', '.rtf', 
        '.odt', '.html', '.xml', '.json', '.yaml', '.yml'
    }
    
    # Tehlikeli dosya uzantıları
    DANGEROUS_EXTENSIONS = {
        '.exe', '.bat', '.cmd', '.com', '.scr', '.pif',
        '.jar', '.js', '.vbs', '.ps1', '.sh', '.php'
    }
    
    # Maksimum dosya boyutları (MB)
    MAX_FILE_SIZES = {
        '.pdf': 100,
        '.docx': 50, 
        '.doc': 50,
        '.txt': 10,
        'default': 25
    }
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def validate_file_path(self, file_path: Union[str, Path]) -> ValidationResult:
        """Dosya yolu güvenlik validasyonu"""
        try:
            path = Path(file_path)
            
            # Path traversal saldırısı kontrolü
            if self._contains_path_traversal(str(path)):
                return ValidationResult(
                    is_valid=False,
                    error_message="Güvenlik riski: Path traversal algılandı"
                )
            
            # Dosya varlığı kontrolü
            if not path.exists():
                return ValidationResult(
                    is_valid=False,
                    error_message="Dosya bulunamadı"
                )
            
            # Dosya boyutu kontrolü
            size_result = self._validate_file_size(path)
            if not size_result.is_valid:
                return size_result
            
            # Dosya uzantısı kontrolü
            ext_result = self._validate_file_extension(path)
            if not ext_result.is_valid:
                return ext_result
            
            # MIME type kontrolü
            mime_result = self._validate_mime_type(path)
            if not mime_result.is_valid:
                return mime_result
            
            return ValidationResult(is_valid=True)
            
        except Exception as e:
            self.logger.error(f"File validation error: {e}")
            return ValidationResult(
                is_valid=False,
                error_message="Dosya validasyonu sırasında hata oluştu"
            )
    
    def _contains_path_traversal(self, path: str) -> bool:
        """Path traversal saldırısı kontrolü"""
        dangerous_patterns = [
            '../', '..\\', 
            '/./', '\\.\\',
            '%2e%2e%2f', '%2e%2e%5c',  # URL encoded
            '..%2f', '..%5c'
        ]
        
        path_lower = path.lower()
        return any(pattern in path_lower for pattern in dangerous_patterns)
    
    def _validate_file_size(self, path: Path) -> ValidationResult:
        """Dosya boyutu validasyonu"""
        try:
            size_mb = path.stat().st_size / (1024 * 1024)
            extension = path.suffix.lower()
            
            max_size = self.MAX_FILE_SIZES.get(extension, self.MAX_FILE_SIZES['default'])
            
            if size_mb > max_size:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Dosya boyutu çok büyük: {size_mb:.1f}MB (Maksimum: {max_size}MB)"
                )
            
            warnings = []
            if size_mb > max_size * 0.8:
                warnings.append(f"Dosya boyutu büyük: {size_mb:.1f}MB")
            
            return ValidationResult(is_valid=True, warnings=warnings)
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                error_message=f"Dosya boyutu kontrol edilemedi: {e}"
            )
    
    def _validate_file_extension(self, path: Path) -> ValidationResult:
        """Dosya uzantısı validasyonu"""
        extension = path.suffix.lower()
        
        if extension in self.DANGEROUS_EXTENSIONS:
            return ValidationResult(
                is_valid=False,
                error_message=f"Güvenlik riski: Tehlikeli dosya uzantısı ({extension})"
            )
        
        if extension not in self.SAFE_EXTENSIONS:
            return ValidationResult(
                is_valid=False,
                error_message=f"Desteklenmeyen dosya uzantısı: {extension}"
            )
        
        return ValidationResult(is_valid=True)
    
    def _validate_mime_type(self, path: Path) -> ValidationResult:
        """MIME type validasyonu"""
        try:
            mime_type, _ = mimetypes.guess_type(str(path))
            
            safe_mime_types = {
                'application/pdf',
                'text/plain',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/msword',
                'application/rtf',
                'text/html',
                'application/xml',
                'text/xml',
                'application/json'
            }
            
            if mime_type and mime_type not in safe_mime_types:
                return ValidationResult(
                    is_valid=True,  # Warning only
                    warnings=[f"Belirsiz MIME type: {mime_type}"]
                )
            
            return ValidationResult(is_valid=True)
            
        except (OSError, ImportError, AttributeError):
            return ValidationResult(
                is_valid=True,  # Don't fail on MIME detection issues
                warnings=["MIME type kontrol edilemedi"]
            )


class InputValidator:
    """Girdi validatörü"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def validate_search_query(self, query: str) -> ValidationResult:
        """Arama sorgusu validasyonu"""
        if not query or not query.strip():
            return ValidationResult(
                is_valid=False,
                error_message="Arama sorgusu boş olamaz"
            )
        
        # Maksimum uzunluk kontrolü
        if len(query) > 1000:
            return ValidationResult(
                is_valid=False,
                error_message="Arama sorgusu çok uzun (maksimum 1000 karakter)"
            )
        
        # SQL injection benzeri pattern kontrolü
        dangerous_patterns = [
            r"';.*--",  # SQL comment
            r"union\s+select",  # UNION SELECT
            r"drop\s+table",  # DROP TABLE
            r"<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>",  # XSS
            r"javascript:",  # JavaScript protocol
            r"vbscript:",  # VBScript protocol
        ]
        
        query_lower = query.lower()
        warnings = []
        
        for pattern in dangerous_patterns:
            if re.search(pattern, query_lower):
                warnings.append("Potansiyel güvenlik riski tespit edildi")
                break
        
        return ValidationResult(is_valid=True, warnings=warnings)
    
    def validate_document_metadata(self, metadata: Dict[str, Any]) -> ValidationResult:
        """Belge metadata validasyonu"""
        required_fields = ['title', 'document_type']
        warnings = []
        
        # Gerekli alanlar kontrolü
        for field in required_fields:
            if field not in metadata or not metadata[field]:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Gerekli alan eksik: {field}"
                )
        
        # String uzunluk kontrolü
        string_limits = {
            'title': 500,
            'law_number': 100,
            'category': 200,
            'subcategory': 200
        }
        
        for field, max_length in string_limits.items():
            if field in metadata and len(str(metadata[field])) > max_length:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"{field} çok uzun (maksimum {max_length} karakter)"
                )
        
        # Güvenli karakter kontrolü
        for field in ['title', 'law_number']:
            if field in metadata:
                if self._contains_unsafe_chars(str(metadata[field])):
                    warnings.append(f"{field} alanında özel karakterler var")
        
        return ValidationResult(is_valid=True, warnings=warnings)
    
    def _contains_unsafe_chars(self, text: str) -> bool:
        """Güvenli olmayan karakter kontrolü"""
        # Control characters ve potansiyel problemli karakterler
        unsafe_patterns = [
            r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]',  # Control chars
            r'[<>"\'\x60]',  # HTML/Script chars
        ]
        
        for pattern in unsafe_patterns:
            if re.search(pattern, text):
                return True
        
        return False
    
    def sanitize_text(self, text: str) -> str:
        """Metin temizleme"""
        if not text:
            return ""
        
        # Control karakterleri temizle
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Fazla boşlukları temizle
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text


class SecureErrorHandler:
    """Güvenli hata işleyici"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def handle_error(self, error: Exception, context: str = "", 
                    user_friendly: bool = True) -> str:
        """Güvenli hata işleme"""
        
        # Detaylı hata logu
        self.logger.error(f"Error in {context}: {type(error).__name__}: {error}")
        
        if user_friendly:
            # Kullanıcı dostu mesaj (teknik detaylar gizli)
            return self._get_user_friendly_message(error)
        else:
            # Geliştirici için detaylı mesaj
            return str(error)
    
    def _get_user_friendly_message(self, error: Exception) -> str:
        """Kullanıcı dostu hata mesajı"""
        
        error_mappings = {
            'FileNotFoundError': 'Dosya bulunamadı. Lütfen dosya yolunu kontrol edin.',
            'PermissionError': 'Dosya erişim izni yok. Lütfen yönetici ile iletişime geçin.',
            'sqlite3.Error': 'Veritabanı hatası oluştu. Lütfen tekrar deneyin.',
            'ConnectionError': 'Bağlantı hatası. Lütfen internet bağlantınızı kontrol edin.',
            'TimeoutError': 'İşlem zaman aşımına uğradı. Lütfen tekrar deneyin.',
            'MemoryError': 'Bellek yetersiz. Lütfen daha küçük dosyalar kullanın.',
        }
        
        error_type = type(error).__name__
        
        for error_pattern, message in error_mappings.items():
            if error_pattern in error_type or error_pattern in str(error):
                return message
        
        return "Beklenmeyen bir hata oluştu. Lütfen tekrar deneyin."


class ConfigSecurityValidator:
    """Konfigürasyon güvenlik validatörü"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def validate_config(self, config_data: Dict[str, Any]) -> ValidationResult:
        """Konfigürasyon güvenlik kontrolü"""
        warnings = []
        
        # Hassas bilgi kontrolü
        sensitive_keys = [
            'password', 'secret', 'key', 'token', 
            'api_key', 'private_key', 'credential'
        ]
        
        self._check_sensitive_data(config_data, sensitive_keys, warnings)
        
        # Dosya yolu güvenliği
        path_keys = ['base_folder', 'db_path', 'log_path']
        for key in path_keys:
            if key in config_data:
                path_value = config_data[key]
                if isinstance(path_value, str) and '../' in path_value:
                    warnings.append(f"Güvenlik riski: {key} path traversal içeriyor")
        
        # Network ayarları
        if 'network' in config_data:
            network_config = config_data['network']
            if isinstance(network_config, dict):
                if network_config.get('allow_external', False):
                    warnings.append("Güvenlik riski: External erişim aktif")
        
        return ValidationResult(is_valid=True, warnings=warnings)
    
    def _check_sensitive_data(self, data: Any, sensitive_keys: List[str], 
                            warnings: List[str], prefix: str = "") -> None:
        """Hassas veri kontrolü (recursive)"""
        if isinstance(data, dict):
            for key, value in data.items():
                current_key = f"{prefix}.{key}" if prefix else key
                
                # Key hassas mı?
                if any(sensitive in key.lower() for sensitive in sensitive_keys):
                    if isinstance(value, str) and len(value) > 0:
                        warnings.append(f"Hassas bilgi: {current_key}")
                
                # Recursive check
                self._check_sensitive_data(value, sensitive_keys, warnings, current_key)
        
        elif isinstance(data, list):
            for i, item in enumerate(data):
                current_key = f"{prefix}[{i}]" if prefix else f"[{i}]"
                self._check_sensitive_data(item, sensitive_keys, warnings, current_key)


# Utility functions
def generate_secure_hash(data: Union[str, bytes]) -> str:
    """Güvenli hash oluşturma"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    return hashlib.sha256(data).hexdigest()


def is_safe_filename(filename: str) -> bool:
    """Güvenli dosya adı kontrolü"""
    # Windows ve Unix için güvenli olmayan karakterler
    unsafe_chars = set('<>:"/\\|?*')
    
    # Control karakterleri
    if any(ord(char) < 32 for char in filename):
        return False
    
    # Güvenli olmayan karakterler
    if any(char in unsafe_chars for char in filename):
        return False
    
    # Reserved names (Windows)
    reserved_names = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    
    name_without_ext = Path(filename).stem.upper()
    if name_without_ext in reserved_names:
        return False
    
    return True
