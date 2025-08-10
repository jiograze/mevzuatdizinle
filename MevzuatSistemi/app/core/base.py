#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Ortak base sınıfları - Kod duplikasyonunu önlemek için
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from pathlib import Path

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QMessageBox
from PyQt5.QtCore import QObject, pyqtSignal, Qt

from ..utils.config_manager import ConfigManager
from ..core.database_manager import DatabaseManager
from ..security import SecureErrorHandler, ValidationResult


class BaseComponent(QObject):
    """Tüm bileşenler için temel sınıf"""
    
    # Common signals
    error_occurred = pyqtSignal(str, str)  # error_message, context
    status_changed = pyqtSignal(str)  # status_message
    progress_updated = pyqtSignal(int)  # progress_percent
    
    def __init__(self, config: ConfigManager, name: str = None):
        super().__init__()
        
        self.config = config
        self.component_name = name or self.__class__.__name__
        self.logger = logging.getLogger(self.component_name)
        self.error_handler = SecureErrorHandler()
        
        # Component state
        self._is_initialized = False
        self._is_active = False
        
        # Performance tracking
        self._stats = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'last_operation_time': None
        }
    
    def initialize(self) -> bool:
        """Bileşeni başlat"""
        try:
            self.logger.info(f"Initializing {self.component_name}")
            
            # Alt sınıfta override edilecek
            result = self._do_initialize()
            
            self._is_initialized = result
            if result:
                self.status_changed.emit(f"{self.component_name} initialized successfully")
            else:
                self.error_occurred.emit("Initialization failed", self.component_name)
            
            return result
            
        except Exception as e:
            error_msg = self.error_handler.handle_error(e, f"{self.component_name} initialization")
            self.error_occurred.emit(error_msg, self.component_name)
            return False
    
    @abstractmethod
    def _do_initialize(self) -> bool:
        """Alt sınıflarda implement edilmesi gereken initialization logic"""
        pass
    
    def cleanup(self):
        """Kaynakları temizle"""
        try:
            self.logger.info(f"Cleaning up {self.component_name}")
            self._do_cleanup()
            self._is_active = False
            self._is_initialized = False
            
        except Exception as e:
            self.logger.error(f"Cleanup error in {self.component_name}: {e}")
    
    def _do_cleanup(self):
        """Alt sınıflarda override edilebilir cleanup logic"""
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Bileşen istatistiklerini al"""
        return self._stats.copy()
    
    def _update_stats(self, success: bool = True):
        """İstatistikleri güncelle"""
        self._stats['total_operations'] += 1
        if success:
            self._stats['successful_operations'] += 1
        else:
            self._stats['failed_operations'] += 1
        
        from datetime import datetime
        self._stats['last_operation_time'] = datetime.now().isoformat()
    
    def is_ready(self) -> bool:
        """Bileşen hazır mı?"""
        return self._is_initialized and self._is_active
    
    def handle_config_change(self, key: str, value: Any):
        """Config değişikliği işleme"""
        self.logger.debug(f"Config change: {key} = {value}")
        # Alt sınıflarda override edilebilir


class BaseUIWidget(QWidget):
    """UI widget'ları için temel sınıf"""
    
    # Common UI signals
    data_changed = pyqtSignal()
    selection_changed = pyqtSignal(object)  # selected_item
    action_requested = pyqtSignal(str, object)  # action_name, data
    
    def __init__(self, parent=None, config: Optional[ConfigManager] = None):
        super().__init__(parent)
        
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.error_handler = SecureErrorHandler()
        
        # UI state
        self._ui_initialized = False
        self._current_data = None
        
        # Initialize UI
        self.init_ui()
        
    def init_ui(self):
        """UI'yı başlat - tüm UI widget'larında ortak pattern"""
        if self._ui_initialized:
            return
        
        try:
            # Ana layout oluştur
            self.main_layout = QVBoxLayout(self)
            self.setLayout(self.main_layout)
            
            # Alt sınıfta override edilecek
            self._create_widgets()
            self._setup_layouts()
            self._connect_signals()
            self._apply_styles()
            
            self._ui_initialized = True
            self.logger.debug(f"UI initialized for {self.__class__.__name__}")
            
        except Exception as e:
            error_msg = self.error_handler.handle_error(e, "UI initialization")
            self.show_error_message("UI Initialization Error", error_msg)
    
    @abstractmethod
    def _create_widgets(self):
        """Widget'ları oluştur - alt sınıflarda implement edilmeli"""
        pass
    
    @abstractmethod  
    def _setup_layouts(self):
        """Layout'ları düzenle - alt sınıflarda implement edilmeli"""
        pass
    
    def _connect_signals(self):
        """Signal'ları bağla - alt sınıflarda override edilebilir"""
        pass
    
    def _apply_styles(self):
        """Stil uygula - alt sınıflarda override edilebilir"""
        if self.config:
            theme = self.config.get('ui.theme', 'default')
            self._apply_theme(theme)
    
    def _apply_theme(self, theme: str):
        """Tema uygula"""
        # Temel tema stilleri
        if theme == 'dark':
            self.setStyleSheet("""
                QWidget {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QPushButton {
                    background-color: #404040;
                    border: 1px solid #555555;
                    padding: 5px 10px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #505050;
                }
            """)
        elif theme == 'light':
            self.setStyleSheet("""
                QWidget {
                    background-color: #ffffff;
                    color: #000000;
                }
                QPushButton {
                    background-color: #f0f0f0;
                    border: 1px solid #cccccc;
                    padding: 5px 10px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
            """)
    
    def show_error_message(self, title: str, message: str):
        """Hata mesajı göster"""
        QMessageBox.critical(self, title, message)
    
    def show_info_message(self, title: str, message: str):
        """Bilgi mesajı göster"""
        QMessageBox.information(self, title, message)
    
    def show_warning_message(self, title: str, message: str):
        """Uyarı mesajı göster"""
        QMessageBox.warning(self, title, message)
    
    def confirm_action(self, title: str, message: str) -> bool:
        """Onay dialogu göster"""
        reply = QMessageBox.question(
            self, title, message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        return reply == QMessageBox.Yes
    
    def set_loading_state(self, loading: bool):
        """Yükleme durumu ayarla"""
        self.setEnabled(not loading)
        if loading:
            self.setCursor(Qt.WaitCursor)
        else:
            self.unsetCursor()
    
    def update_data(self, data: Any):
        """Veri güncelleme - alt sınıflarda override edilebilir"""
        self._current_data = data
        self.data_changed.emit()
    
    def get_current_data(self) -> Any:
        """Mevcut veriyi al"""
        return self._current_data


class BaseDocumentOperation:
    """Belge işlemleri için temel sınıf"""
    
    def __init__(self, config: ConfigManager, db: DatabaseManager):
        self.config = config
        self.db = db
        self.logger = logging.getLogger(self.__class__.__name__)
        self.error_handler = SecureErrorHandler()
    
    def delete_document(self, document_id: int, delete_physical_file: bool = False) -> bool:
        """Belge silme - ortak implementation"""
        try:
            self.logger.info(f"Deleting document {document_id}")
            
            # Belge bilgilerini al
            document = self.db.get_document(document_id)
            if not document:
                self.logger.warning(f"Document {document_id} not found")
                return False
            
            # Fiziksel dosyayı sil (isteğe bağlı)
            if delete_physical_file and document.file_path:
                try:
                    file_path = Path(document.file_path)
                    if file_path.exists():
                        file_path.unlink()
                        self.logger.info(f"Physical file deleted: {file_path}")
                except Exception as e:
                    self.logger.warning(f"Could not delete physical file: {e}")
            
            # Veritabanından sil
            result = self.db.delete_document(document_id)
            
            if result:
                self.logger.info(f"Document {document_id} deleted successfully")
            else:
                self.logger.error(f"Failed to delete document {document_id}")
            
            return result
            
        except Exception as e:
            error_msg = self.error_handler.handle_error(e, f"delete_document({document_id})")
            self.logger.error(error_msg)
            return False
    
    def validate_document_data(self, document_data: Dict[str, Any]) -> ValidationResult:
        """Belge verisi validasyonu - ortak implementation"""
        from ..security import InputValidator
        
        validator = InputValidator()
        return validator.validate_document_metadata(document_data)
    
    def prepare_document_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Belge verisini hazırla - ortak preprocessing"""
        from ..security import InputValidator
        
        validator = InputValidator()
        
        # Temizle ve hazırla
        processed_data = {}
        for key, value in raw_data.items():
            if isinstance(value, str):
                processed_data[key] = validator.sanitize_text(value)
            else:
                processed_data[key] = value
        
        # Varsayılan değerler
        if 'created_at' not in processed_data:
            from datetime import datetime
            processed_data['created_at'] = datetime.now().isoformat()
        
        if 'status' not in processed_data:
            processed_data['status'] = 'ACTIVE'
        
        if 'version_number' not in processed_data:
            processed_data['version_number'] = 1
        
        return processed_data


class BaseSearchOperation:
    """Arama işlemleri için temel sınıf"""
    
    def __init__(self, config: ConfigManager, db: DatabaseManager):
        self.config = config
        self.db = db
        self.logger = logging.getLogger(self.__class__.__name__)
        self.error_handler = SecureErrorHandler()
        
        # Arama ayarları
        self.default_limit = config.get('search.default_limit', 20)
        self.max_limit = config.get('search.max_limit', 100)
    
    def validate_search_query(self, query: str) -> ValidationResult:
        """Arama sorgusu validasyonu - ortak implementation"""
        from ..security import InputValidator
        
        validator = InputValidator()
        return validator.validate_search_query(query)
    
    def normalize_search_query(self, query: str) -> str:
        """Arama sorgusunu normalize et"""
        if not query:
            return ""
        
        # Temizle
        from ..security import InputValidator
        validator = InputValidator()
        normalized = validator.sanitize_text(query)
        
        # Küçük harfe çevir
        normalized = normalized.lower()
        
        # Fazla boşlukları temizle
        import re
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def validate_search_limit(self, limit: Optional[int]) -> int:
        """Arama limit validasyonu"""
        if limit is None:
            return self.default_limit
        
        if limit <= 0:
            return self.default_limit
        
        if limit > self.max_limit:
            self.logger.warning(f"Search limit {limit} exceeds maximum {self.max_limit}")
            return self.max_limit
        
        return limit


class ComponentManager:
    """Bileşen yöneticisi - tüm bileşenlerin lifecycle'ını yönetir"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.components: Dict[str, BaseComponent] = {}
        self.initialization_order: List[str] = []
    
    def register_component(self, name: str, component: BaseComponent, 
                         depends_on: List[str] = None):
        """Bileşen kaydet"""
        self.components[name] = component
        
        # Dependency order'ı hesapla
        if depends_on:
            # Basit dependency resolution
            for dep in depends_on:
                if dep not in self.initialization_order:
                    self.initialization_order.append(dep)
        
        if name not in self.initialization_order:
            self.initialization_order.append(name)
        
        self.logger.debug(f"Component registered: {name}")
    
    def initialize_all(self) -> bool:
        """Tüm bileşenleri başlat"""
        self.logger.info("Initializing all components...")
        
        success_count = 0
        for name in self.initialization_order:
            if name in self.components:
                component = self.components[name]
                try:
                    if component.initialize():
                        success_count += 1
                        self.logger.info(f"✅ {name} initialized")
                    else:
                        self.logger.error(f"❌ {name} initialization failed")
                except Exception as e:
                    self.logger.error(f"❌ {name} initialization error: {e}")
        
        total_components = len(self.components)
        self.logger.info(f"Initialized {success_count}/{total_components} components")
        
        return success_count == total_components
    
    def cleanup_all(self):
        """Tüm bileşenleri temizle"""
        self.logger.info("Cleaning up all components...")
        
        # Reverse order'da cleanup
        for name in reversed(self.initialization_order):
            if name in self.components:
                try:
                    self.components[name].cleanup()
                    self.logger.info(f"✅ {name} cleaned up")
                except Exception as e:
                    self.logger.error(f"❌ {name} cleanup error: {e}")
    
    def get_component(self, name: str) -> Optional[BaseComponent]:
        """Bileşen al"""
        return self.components.get(name)
    
    def get_component_stats(self) -> Dict[str, Dict[str, Any]]:
        """Tüm bileşen istatistiklerini al"""
        stats = {}
        for name, component in self.components.items():
            stats[name] = component.get_stats()
        return stats
