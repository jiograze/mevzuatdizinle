"""
Ana uygulama yöneticisi - tüm bileşenleri koordine eder
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QThread

from ..utils.config_manager import ConfigManager
from ..utils.logger import setup_logger
from ..core.database_manager import DatabaseManager
from ..core.file_watcher import FileWatcher
from ..core.document_processor import DocumentProcessor
from ..core.search_engine import SearchEngine
from ..ui.main_window import MainWindow
from ..utils.backup_manager import BackupManager
from ..utils.system_tray import SystemTrayManager

class MevzuatApp:
    """Ana uygulama sınıfı - tüm bileşenleri yönetir"""
    
    def __init__(self):
        self.logger = setup_logger(self.__class__.__name__)
        self.config: Optional[ConfigManager] = None
        self.db: Optional[DatabaseManager] = None
        self.file_watcher: Optional[FileWatcher] = None
        self.document_processor: Optional[DocumentProcessor] = None
        self.search_engine: Optional[SearchEngine] = None
        self.main_window: Optional[MainWindow] = None
        self.qt_app: Optional[QApplication] = None
        self.backup_manager: Optional[BackupManager] = None
        self.system_tray: Optional[SystemTrayManager] = None
        
        self._initialize()
    
    def _initialize(self):
        """Tüm bileşenleri başlat"""
        try:
            self.logger.info("Mevzuat sistemi başlatılıyor...")
            
            # Konfigürasyonu yükle
            self.config = ConfigManager()
            
            # İlk çalışma kontrolü
            if self.config.get('exe.first_run_check', True):
                self._handle_first_run()
            
            # Veritabanını başlat
            self.db = DatabaseManager(self.config)
            self.db.initialize()
            
            # Belge işleyiciyi başlat
            self.document_processor = DocumentProcessor(self.config, self.db)
            
            # Arama motorunu başlat
            self.search_engine = SearchEngine(self.config, self.db)
            
            # Backup manager'ı başlat
            self.backup_manager = BackupManager(self.config, self.db)
            
            # Dosya izleyiciyi başlat (eğer etkinse)
            if self.config.get('watch_enabled', True):
                self.file_watcher = FileWatcher(
                    self.config, 
                    self.document_processor
                )
            
            self.logger.info("Tüm bileşenler başarıyla başlatıldı")
            
        except Exception as e:
            self.logger.error(f"Başlatma hatası: {e}")
            raise
    
    def _connect_tray_signals(self):
        """System tray sinyallerini bağla"""
        if not self.system_tray:
            return
        
        # Hızlı yedekleme
        self.system_tray.quick_backup_requested.connect(self._perform_quick_backup)
        
        # Hızlı arama
        self.system_tray.search_requested.connect(self._perform_tray_search)
        
        # Çıkış
        self.system_tray.exit_requested.connect(self._safe_exit)
    
    def _perform_quick_backup(self):
        """Hızlı yedekleme"""
        try:
            if self.backup_manager:
                backup_file = self.backup_manager.create_backup("quick_backup")
                if backup_file and self.system_tray:
                    self.system_tray.notify_backup_completed(backup_file.name)
                self.logger.info("Hızlı yedekleme tamamlandı")
        except Exception as e:
            self.logger.error(f"Hızlı yedekleme hatası: {e}")
            if self.system_tray:
                self.system_tray.notify_error("Yedekleme Hatası", str(e))
    
    def _perform_tray_search(self, query: str):
        """Tray'den arama"""
        try:
            if self.main_window:
                # Ana pencereyi göster ve aramayı başlat
                self.main_window.show()
                self.main_window.raise_()
                
                # Search widget'ına sorguyu gönder
                if hasattr(self.main_window, 'search_widget'):
                    self.main_window.search_widget.search_input.setText(query)
                    self.main_window.perform_search(query, "mixed")
        except Exception as e:
            self.logger.error(f"Tray arama hatası: {e}")
    
    def _safe_exit(self):
        """Güvenli çıkış"""
        self.shutdown()
        if self.qt_app:
            self.qt_app.quit()
    
    def _handle_first_run(self):
        """İlk çalışma kurulum sihirbazı"""
        self.logger.info("İlk çalışma kurulumu başlatılıyor...")
        
        # Temel klasör yapısını oluştur
        base_folder = self.config.get('base_folder')
        if base_folder and not os.path.exists(base_folder):
            self._create_directory_structure(base_folder)
        
        # İlk çalışma flag'ini kapat
        self.config.set('exe.first_run_check', False)
        self.config.save()
    
    def _create_directory_structure(self, base_folder: str):
        """Temel klasör yapısını oluştur"""
        directories = [
            'config',
            'raw',
            'mevzuat/Anayasa',
            'mevzuat/Kanun',
            'mevzuat/KHK',
            'mevzuat/Tüzük',
            'mevzuat/Yönetmelik',
            'mevzuat/Yönerge_Genelge',
            'mevzuat/Diger',
            'mevzuat/_Özel_Kategoriler',
            'db',
            'index',
            'logs',
            'temp/ocr',
            'temp/export',
            'quarantine',
            'backup',
            'models',
            'templates'
        ]
        
        for directory in directories:
            dir_path = os.path.join(base_folder, directory)
            os.makedirs(dir_path, exist_ok=True)
            self.logger.info(f"Klasör oluşturuldu: {dir_path}")
    
    def run(self):
        """Ana uygulamayı çalıştır"""
        try:
            # Qt uygulamasını başlat
            self.qt_app = QApplication(sys.argv)
            
            # Ana pencereyi oluştur ve göster
            self.main_window = MainWindow(
                config=self.config,
                db=self.db,
                search_engine=self.search_engine,
                document_processor=self.document_processor,
                file_watcher=self.file_watcher
            )
            
            self.main_window.show()
            
            # System tray'i başlat
            if self.config.get('ui.system_tray_enabled', True):
                self.system_tray = SystemTrayManager(self.config, self.main_window)
                self._connect_tray_signals()
            
            # Otomatik yedekleme kontrolü
            if self.backup_manager:
                self.backup_manager.auto_backup_check()
            
            # Dosya izleyiciyi başlat (eğer varsa)
            if self.file_watcher:
                self.file_watcher.start_watching()
            
            self.logger.info("GUI başlatıldı, uygulama hazır")
            
            # Olay döngüsünü başlat
            sys.exit(self.qt_app.exec_())
            
        except Exception as e:
            self.logger.error(f"Uygulama çalışma hatası: {e}")
            raise
    
    def shutdown(self):
        """Uygulamayı temiz şekilde kapat"""
        try:
            self.logger.info("Uygulama kapatılıyor...")
            
            # Dosya izleyiciyi durdur
            if self.file_watcher:
                self.file_watcher.stop_watching()
            
            # System tray'i temizle
            if self.system_tray:
                self.system_tray.cleanup()
            
            # Veritabanı bağlantısını kapat
            if self.db:
                self.db.close()
            
            # Konfigürasyonu kaydet
            if self.config:
                self.config.save()
            
            self.logger.info("Uygulama temiz şekilde kapatıldı")
            
        except Exception as e:
            self.logger.error(f"Kapatma hatası: {e}")
    
    def __del__(self):
        """Nesne yok edilirken temizlik yap"""
        try:
            self.shutdown()
        except:
            pass
