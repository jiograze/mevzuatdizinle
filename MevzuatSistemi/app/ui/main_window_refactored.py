"""
SOLID Principles uygulanmış MainWindow - Refactored
Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion
"""

import sys
import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QTextEdit, QLabel, QComboBox, QCheckBox,
    QSplitter, QTreeWidget, QTreeWidgetItem, QTableWidget, QTableWidgetItem,
    QProgressBar, QStatusBar, QMenuBar, QMenu, QAction, QFileDialog,
    QMessageBox, QTabWidget, QGroupBox, QApplication
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QDragEnterEvent, QDropEvent

from ..core.search_engine import SearchResult


# Interface Segregation Principle - Küçük, spesifik interface'ler
class IMainWindowView(ABC):
    """Ana pencere görünüm interface'i"""
    @abstractmethod
    def show_message(self, message: str, duration: int = 0): pass
    
    @abstractmethod
    def show_progress(self, visible: bool, value: int = 0, maximum: int = 100): pass
    
    @abstractmethod
    def update_result_count(self, count: int): pass

class ISearchHandler(ABC):
    """Arama işlemleri interface'i"""
    @abstractmethod
    async def perform_search(self, query: str, search_type: str, filters: Dict[str, Any]) -> List[SearchResult]: pass
    
    @abstractmethod
    async def perform_faceted_search(self, query: str, facet_filters: Dict[str, Any]) -> Any: pass

class IDocumentHandler(ABC):
    """Belge işlemleri interface'i"""
    @abstractmethod
    async def add_documents(self, file_paths: List[str]) -> Dict[str, Any]: pass
    
    @abstractmethod
    def delete_document(self, document_id: int) -> bool: pass
    
    @abstractmethod
    def view_document(self, document_id: int): pass

class IFileOperations(ABC):
    """Dosya işlemleri interface'i"""
    @abstractmethod
    def scan_raw_folder(self) -> int: pass
    
    @abstractmethod
    def rebuild_semantic_index(self) -> bool: pass
    
    @abstractmethod
    def vacuum_database(self) -> bool: pass

class IMenuManager(ABC):
    """Menü yönetimi interface'i"""
    @abstractmethod
    def create_menu_bar(self) -> QMenuBar: pass
    
    @abstractmethod
    def create_toolbar(self): pass

class IThemeManager(ABC):
    """Tema yönetimi interface'i"""
    @abstractmethod
    def apply_theme(self, theme_name: str): pass
    
    @abstractmethod
    def get_available_themes(self) -> List[str]: pass


# Single Responsibility Principle - Her sınıf tek bir sorumluluğa sahip
@dataclass
class WindowState:
    """Pencere durum bilgilerini tutan veri sınıfı"""
    last_search_results: List[SearchResult]
    current_document: Optional[Dict[str, Any]]
    current_article_id: Optional[int]
    
    def __post_init__(self):
        if self.last_search_results is None:
            self.last_search_results = []


class AsyncSearchHandler(QThread, ISearchHandler):
    """Asenkron arama işlemlerini yöneten sınıf"""
    search_completed = pyqtSignal(list)  # List[SearchResult]
    search_error = pyqtSignal(str)
    
    def __init__(self, search_engine, db):
        super().__init__()
        self.search_engine = search_engine
        self.db = db
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Current search parameters
        self._query = ""
        self._search_type = "mixed"
        self._filters = {}
        
    async def perform_search(self, query: str, search_type: str, filters: Dict[str, Any]) -> List[SearchResult]:
        """Asenkron arama gerçekleştir"""
        self._query = query
        self._search_type = search_type
        self._filters = filters
        self.start()
        return []  # Sonuç signal ile dönecek
    
    async def perform_faceted_search(self, query: str, facet_filters: Dict[str, Any]) -> Any:
        """Asenkron faceted search"""
        try:
            results = self.search_engine.search_with_facets(
                query=query,
                search_type='mixed',
                facet_filters=facet_filters
            )
            return results
        except Exception as e:
            self.logger.error(f"Faceted search error: {e}")
            raise
    
    def run(self):
        """Thread çalışma metodu"""
        try:
            # Filtreleri hazırla
            document_types = self._filters.get('document_types', [])
            include_repealed = self._filters.get('include_repealed', False)
            
            # Arama yap
            results = self.search_engine.search(
                query=self._query,
                document_types=document_types,
                search_type=self._search_type,
                include_repealed=include_repealed
            )
            
            self.search_completed.emit(results)
            
        except Exception as e:
            self.logger.error(f"Search thread error: {e}")
            self.search_error.emit(str(e))


class DocumentOperationsManager(IDocumentHandler):
    """Belge işlemleri yöneticisi - Asenkron belge işlemleri"""
    
    def __init__(self, document_processor, db, progress_callback=None):
        self.document_processor = document_processor
        self.db = db
        self.progress_callback = progress_callback
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def add_documents(self, file_paths: List[str]) -> Dict[str, Any]:
        """Belgeleri asenkron olarak ekle"""
        result = {
            'processed_count': 0,
            'failed_files': [],
            'total_files': len(file_paths)
        }
        
        for i, file_path in enumerate(file_paths):
            try:
                if self.progress_callback:
                    self.progress_callback(i, len(file_paths), f"İşleniyor: {Path(file_path).name}")
                
                # Dosyayı işle
                process_result = self.document_processor.process_file(file_path)
                
                if process_result['success']:
                    result['processed_count'] += 1
                    self.logger.info(f"Document added: {file_path}")
                else:
                    result['failed_files'].append({
                        'file': Path(file_path).name,
                        'error': process_result.get('error', 'Unknown error')
                    })
                    
            except Exception as e:
                result['failed_files'].append({
                    'file': Path(file_path).name,
                    'error': str(e)
                })
                self.logger.error(f"Document processing error: {file_path} - {e}")
        
        return result
    
    def delete_document(self, document_id: int) -> bool:
        """Belgeyi sil"""
        try:
            return self.db.delete_document(document_id, delete_physical_file=False)
        except Exception as e:
            self.logger.error(f"Document deletion error: {e}")
            return False
    
    def view_document(self, document_id: int):
        """Belgeyi görüntüle"""
        # Implementation will be delegated to view layer
        pass


class FileOperationsManager(IFileOperations):
    """Dosya işlemleri yöneticisi"""
    
    def __init__(self, file_watcher, search_engine, db):
        self.file_watcher = file_watcher
        self.search_engine = search_engine
        self.db = db
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def scan_raw_folder(self) -> int:
        """Raw klasörünü tara"""
        try:
            if not self.file_watcher:
                raise ValueError("File watcher not available")
            return self.file_watcher.manual_scan()
        except Exception as e:
            self.logger.error(f"Raw folder scan error: {e}")
            raise
    
    def rebuild_semantic_index(self) -> bool:
        """Semantik indeksi yeniden oluştur"""
        try:
            return self.search_engine.rebuild_index()
        except Exception as e:
            self.logger.error(f"Index rebuild error: {e}")
            return False
    
    def vacuum_database(self) -> bool:
        """Veritabanı bakımı"""
        try:
            self.db.vacuum()
            return True
        except Exception as e:
            self.logger.error(f"Database vacuum error: {e}")
            return False


class MenuManager(IMenuManager):
    """Menü yönetim sınıfı"""
    
    def __init__(self, parent_window, action_handlers: Dict[str, callable]):
        self.parent_window = parent_window
        self.action_handlers = action_handlers
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def create_menu_bar(self) -> QMenuBar:
        """Menü çubuğunu oluştur"""
        menubar = self.parent_window.menuBar()
        
        # Dosya menüsü
        self._create_file_menu(menubar)
        
        # Belge yönetimi menüsü
        self._create_document_menu(menubar)
        
        # Araçlar menüsü
        self._create_tools_menu(menubar)
        
        # Yardım menüsü
        self._create_help_menu(menubar)
        
        return menubar
    
    def _create_file_menu(self, menubar):
        """Dosya menüsü oluştur"""
        file_menu = menubar.addMenu('📁 Dosya')
        
        # Belge ekleme
        add_files_action = QAction('➕ Dosya Seçerek Belge Ekle', self.parent_window)
        add_files_action.setShortcut('Ctrl+O')
        add_files_action.triggered.connect(self.action_handlers.get('add_files'))
        file_menu.addAction(add_files_action)
        
        # Raw klasör tarama
        scan_action = QAction('🔍 Raw Klasörü Tara', self.parent_window)
        scan_action.triggered.connect(self.action_handlers.get('scan_raw'))
        file_menu.addAction(scan_action)
        
        file_menu.addSeparator()
        
        # PDF rapor
        export_action = QAction('📄 PDF Rapor Oluştur', self.parent_window)
        export_action.setShortcut('Ctrl+E')
        export_action.triggered.connect(self.action_handlers.get('export_pdf'))
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Çıkış
        exit_action = QAction('🚪 Çıkış', self.parent_window)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.parent_window.close)
        file_menu.addAction(exit_action)
    
    def _create_document_menu(self, menubar):
        """Belge yönetimi menüsü oluştur"""
        doc_menu = menubar.addMenu('📄 Belge Yönetimi')
        
        list_docs_action = QAction('📋 Tüm Belgeler', self.parent_window)
        list_docs_action.triggered.connect(self.action_handlers.get('list_documents'))
        doc_menu.addAction(list_docs_action)
        
        doc_menu.addSeparator()
        
        check_docs_action = QAction('🔍 Eksik Belgeleri Kontrol Et', self.parent_window)
        check_docs_action.triggered.connect(self.action_handlers.get('check_missing'))
        doc_menu.addAction(check_docs_action)
    
    def _create_tools_menu(self, menubar):
        """Araçlar menüsü oluştur"""
        tools_menu = menubar.addMenu('🔧 Araçlar')
        
        rebuild_action = QAction('🔄 Semantik İndeksi Yeniden Oluştur', self.parent_window)
        rebuild_action.triggered.connect(self.action_handlers.get('rebuild_index'))
        tools_menu.addAction(rebuild_action)
        
        vacuum_action = QAction('🗂️ Veritabanı Bakımı', self.parent_window)
        vacuum_action.triggered.connect(self.action_handlers.get('vacuum_db'))
        tools_menu.addAction(vacuum_action)
        
        tools_menu.addSeparator()
        
        settings_action = QAction('⚙️ Ayarlar', self.parent_window)
        settings_action.setShortcut('Ctrl+,')
        settings_action.triggered.connect(self.action_handlers.get('open_settings'))
        tools_menu.addAction(settings_action)
    
    def _create_help_menu(self, menubar):
        """Yardım menüsü oluştur"""
        help_menu = menubar.addMenu('❓ Yardım')
        
        help_action = QAction('📚 Kullanım Kılavuzu', self.parent_window)
        help_action.setShortcut('F1')
        help_action.triggered.connect(self.action_handlers.get('show_help'))
        help_menu.addAction(help_action)
        
        help_menu.addSeparator()
        
        about_action = QAction('ℹ️ Hakkında', self.parent_window)
        about_action.triggered.connect(self.action_handlers.get('show_about'))
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        """Toolbar oluştur"""
        toolbar = self.parent_window.addToolBar('Ana Araçlar')
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        
        # Belge ekleme
        add_action = toolbar.addAction('📄➕ Belge Ekle')
        add_action.triggered.connect(self.action_handlers.get('add_files'))
        
        # Raw tara
        scan_action = toolbar.addAction('🔍 Raw Tara')
        scan_action.triggered.connect(self.action_handlers.get('scan_raw'))
        
        toolbar.addSeparator()
        
        # İndeks yenile
        rebuild_action = toolbar.addAction('🔄 İndeksi Yenile')
        rebuild_action.triggered.connect(self.action_handlers.get('rebuild_index'))
        
        toolbar.addSeparator()
        
        # Ayarlar
        settings_action = toolbar.addAction('⚙️ Ayarlar')
        settings_action.triggered.connect(self.action_handlers.get('open_settings'))


class ThemeManager(IThemeManager):
    """Tema yönetim sınıfı"""
    
    def __init__(self, config):
        self.config = config
        self.themes = {
            'light': self._get_light_theme(),
            'dark': self._get_dark_theme(),
            'system': self._get_system_theme()
        }
    
    def apply_theme(self, theme_name: str):
        """Temayı uygula"""
        if theme_name not in self.themes:
            theme_name = 'system'
        
        return self.themes[theme_name]
    
    def get_available_themes(self) -> List[str]:
        """Mevcut temaları getir"""
        return list(self.themes.keys())
    
    def _get_light_theme(self) -> str:
        """Açık tema CSS"""
        return """
            QMainWindow {
                background-color: #ffffff;
                color: #000000;
            }
            QWidget {
                background-color: #ffffff;
                color: #000000;
            }
        """
    
    def _get_dark_theme(self) -> str:
        """Koyu tema CSS"""
        return """
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLineEdit, QTextEdit, QComboBox {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                color: #ffffff;
                padding: 5px;
            }
            QPushButton {
                background-color: #0078d4;
                border: none;
                color: white;
                padding: 8px 16px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QTreeWidget, QTableWidget {
                background-color: #3c3c3c;
                alternate-background-color: #404040;
                border: 1px solid #555555;
            }
        """
    
    def _get_system_theme(self) -> str:
        """Sistem teması"""
        return ""  # Varsayılan sistem teması


# Open/Closed Principle - Genişlemeye açık, değişikliğe kapalı
class MainWindowController:
    """MainWindow kontrolcü sınıfı - iş mantığı burada"""
    
    def __init__(self, config, db, search_engine, document_processor, file_watcher):
        self.config = config
        self.db = db
        self.search_engine = search_engine
        self.document_processor = document_processor
        self.file_watcher = file_watcher
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # State
        self.window_state = WindowState([], None, None)
        
        # Handlers - Dependency Inversion Principle
        self.search_handler = AsyncSearchHandler(search_engine, db)
        self.document_handler = DocumentOperationsManager(document_processor, db)
        self.file_operations = FileOperationsManager(file_watcher, search_engine, db)
        self.theme_manager = ThemeManager(config)
        
        # Connect signals
        self.search_handler.search_completed.connect(self._on_search_completed)
        self.search_handler.search_error.connect(self._on_search_error)
    
    async def perform_search(self, query: str, search_type: str, filters: Dict[str, Any]):
        """Arama işlemini başlat"""
        await self.search_handler.perform_search(query, search_type, filters)
    
    async def add_documents_async(self, file_paths: List[str], progress_callback=None) -> Dict[str, Any]:
        """Belgeleri asenkron olarak ekle"""
        self.document_handler.progress_callback = progress_callback
        return await self.document_handler.add_documents(file_paths)
    
    def _on_search_completed(self, results: List[SearchResult]):
        """Arama tamamlandığında"""
        self.window_state.last_search_results = results
        self.logger.info(f"Search completed: {len(results)} results")
    
    def _on_search_error(self, error: str):
        """Arama hatası durumunda"""
        self.logger.error(f"Search error: {error}")


class RefactoredMainWindow(QMainWindow, IMainWindowView):
    """
    SOLID Principles uygulanmış ana pencere
    - Single Responsibility: UI bileşenlerini yönetir
    - Open/Closed: Yeni özellikler için genişletilebilir
    - Liskov Substitution: IMainWindowView interface'ini implement eder
    - Interface Segregation: Küçük, spesifik interface'ler kullanır
    - Dependency Inversion: Somut sınıflara değil, abstraction'lara bağımlı
    """
    
    def __init__(self, config, db, search_engine, document_processor, file_watcher):
        super().__init__()
        
        # Controller - iş mantığını yönetir
        self.controller = MainWindowController(
            config, db, search_engine, document_processor, file_watcher
        )
        
        # UI Managers
        self.menu_manager = MenuManager(self, self._get_action_handlers())
        self.theme_manager = self.controller.theme_manager
        
        # UI State
        self.progress_bar = None
        self.status_bar = None
        self.result_count_label = None
        
        # Initialize UI
        self._init_ui()
        self._setup_timers()
        self._apply_initial_theme()
        
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Refactored MainWindow initialized")
    
    def _init_ui(self):
        """UI'yı başlat"""
        self.setWindowTitle("Mevzuat Belge Analiz & Sorgulama Sistemi v1.0.2 (SOLID)")
        self.setGeometry(100, 100, 1400, 800)
        
        # Ana widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout
        main_layout = QVBoxLayout(central_widget)
        
        # Menü ve toolbar
        self.menu_manager.create_menu_bar()
        self.menu_manager.create_toolbar()
        
        # Ana içerik
        content_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(content_splitter)
        
        # Paneller (Bu kısım eski koddan alınacak)
        # Sol, orta, sağ paneller oluşturulacak
        
        # Status bar
        self._create_status_bar()
        
        # Drag & drop
        self.setAcceptDrops(True)
    
    def _create_status_bar(self):
        """Status bar oluştur"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Sonuç sayısı etiketi
        self.result_count_label = QLabel("Sonuç yok")
        self.status_bar.addWidget(self.result_count_label)
    
    def _setup_timers(self):
        """Timer'ları ayarla"""
        # Status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(5000)  # 5 saniye
    
    def _apply_initial_theme(self):
        """İlk temayı uygula"""
        theme_name = self.controller.config.get('preferences.theme', 'system')
        theme_css = self.theme_manager.apply_theme(theme_name)
        if theme_css:
            self.setStyleSheet(theme_css)
    
    def _get_action_handlers(self) -> Dict[str, callable]:
        """Menü aksiyonları için handler'ları döndür"""
        return {
            'add_files': self._add_files,
            'scan_raw': self._scan_raw,
            'export_pdf': self._export_pdf,
            'list_documents': self._list_documents,
            'check_missing': self._check_missing,
            'rebuild_index': self._rebuild_index,
            'vacuum_db': self._vacuum_db,
            'open_settings': self._open_settings,
            'show_help': self._show_help,
            'show_about': self._show_about
        }
    
    # IMainWindowView implementation
    def show_message(self, message: str, duration: int = 0):
        """Mesaj göster"""
        if self.status_bar:
            self.status_bar.showMessage(message, duration)
    
    def show_progress(self, visible: bool, value: int = 0, maximum: int = 100):
        """Progress bar göster/gizle"""
        if self.progress_bar:
            self.progress_bar.setVisible(visible)
            if visible:
                self.progress_bar.setRange(0, maximum)
                self.progress_bar.setValue(value)
    
    def update_result_count(self, count: int):
        """Sonuç sayısını güncelle"""
        if self.result_count_label:
            self.result_count_label.setText(f"{count} sonuç")
    
    # Action handlers
    def _add_files(self):
        """Dosya ekleme dialog'u"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Dosya Seçin", "",
            "Desteklenen (*.pdf *.docx *.doc *.txt);;Tüm (*)"
        )
        
        if files:
            self._process_files_async(files)
    
    async def _process_files_async(self, file_paths: List[str]):
        """Dosyaları asenkron işle"""
        self.show_progress(True, 0, len(file_paths))
        
        def progress_callback(current, total, message):
            self.show_progress(True, current, total)
            self.show_message(message)
            QApplication.processEvents()
        
        try:
            result = await self.controller.add_documents_async(file_paths, progress_callback)
            
            self.show_progress(False)
            
            if result['failed_files']:
                error_msg = f"İşlem tamamlandı:\n"
                error_msg += f"Başarılı: {result['processed_count']}\n"
                error_msg += f"Başarısız: {len(result['failed_files'])}\n"
                QMessageBox.warning(self, "Sonuç", error_msg)
            else:
                QMessageBox.information(self, "Başarılı", 
                    f"Tüm dosyalar eklendi: {result['processed_count']}")
            
        except Exception as e:
            self.show_progress(False)
            QMessageBox.critical(self, "Hata", f"Dosya ekleme hatası:\n{e}")
    
    def _scan_raw(self):
        """Raw klasör tarama"""
        try:
            count = self.controller.file_operations.scan_raw_folder()
            QMessageBox.information(self, "Tarama", f"{count} dosya işleme kuyruğuna eklendi")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Raw tarama hatası:\n{e}")
    
    def _export_pdf(self):
        """PDF export"""
        # PDF export mantığı
        QMessageBox.information(self, "Bilgi", "PDF export özelliği geliştirilecek")
    
    def _list_documents(self):
        """Belgeleri listele"""
        # Belge listeleme mantığı
        QMessageBox.information(self, "Bilgi", "Belge listeleme özelliği geliştirilecek")
    
    def _check_missing(self):
        """Eksik belgeleri kontrol et"""
        # Eksik belge kontrolü mantığı
        QMessageBox.information(self, "Bilgi", "Eksik belge kontrolü özelliği geliştirilecek")
    
    def _rebuild_index(self):
        """İndeksi yeniden oluştur"""
        reply = QMessageBox.question(self, "Onay", 
            "İndeks yeniden oluşturulacak. Devam?",
            QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.show_progress(True, 0, 0)  # Indeterminate
            try:
                success = self.controller.file_operations.rebuild_semantic_index()
                self.show_progress(False)
                if success:
                    QMessageBox.information(self, "Başarılı", "İndeks yenilendi")
                else:
                    QMessageBox.warning(self, "Uyarı", "İndeks yenilenirken sorun oluştu")
            except Exception as e:
                self.show_progress(False)
                QMessageBox.critical(self, "Hata", f"İndeks yenileme hatası:\n{e}")
    
    def _vacuum_db(self):
        """Veritabanı bakımı"""
        reply = QMessageBox.question(self, "Onay", 
            "Veritabanı bakımı yapılacak. Devam?",
            QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                success = self.controller.file_operations.vacuum_database()
                if success:
                    QMessageBox.information(self, "Başarılı", "Veritabanı bakımı tamamlandı")
                else:
                    QMessageBox.warning(self, "Uyarı", "Veritabanı bakımında sorun oluştu")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Veritabanı bakım hatası:\n{e}")
    
    def _open_settings(self):
        """Ayarlar penceresi"""
        QMessageBox.information(self, "Bilgi", "Ayarlar penceresi geliştirilecek")
    
    def _show_help(self):
        """Yardım penceresi"""
        help_text = """
        <h2>SOLID Principles Uygulanmış Mevzuat Sistemi</h2>
        <p>Bu versiyon SOLID prensipleri ile yeniden tasarlandı:</p>
        <ul>
        <li><b>Single Responsibility:</b> Her sınıf tek sorumluluğa sahip</li>
        <li><b>Open/Closed:</b> Genişlemeye açık, değişikliğe kapalı</li>
        <li><b>Liskov Substitution:</b> Interface'ler doğru implement edildi</li>
        <li><b>Interface Segregation:</b> Küçük, spesifik interface'ler</li>
        <li><b>Dependency Inversion:</b> Abstraction'lara bağımlılık</li>
        </ul>
        <p>Asenkron işlemler ve gelişmiş performans özellikleri eklendi.</p>
        """
        QMessageBox.about(self, "Yardım", help_text)
    
    def _show_about(self):
        """Hakkında penceresi"""
        about_text = """
        <h2>Mevzuat Sistemi v1.0.2 - SOLID Edition</h2>
        <p>SOLID Principles ve Clean Architecture ile geliştirildi</p>
        <p><b>Özellikler:</b></p>
        <ul>
        <li>Asenkron arama işlemleri</li>
        <li>Memory-optimized performance</li>
        <li>Modüler ve genişletilebilir mimari</li>
        <li>Gelişmiş error handling</li>
        </ul>
        """
        QMessageBox.about(self, "Hakkında", about_text)
    
    def _update_status(self):
        """Durumu güncelle"""
        try:
            # File watcher durumu vs. kontrol et
            pass
        except Exception as e:
            self.logger.error(f"Status update error: {e}")
    
    # Drag & Drop events
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Drag enter event"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            supported_extensions = {'.pdf', '.docx', '.doc', '.txt'}
            
            valid_files = [url for url in urls 
                          if url.isLocalFile() and 
                          Path(url.toLocalFile()).suffix.lower() in supported_extensions]
            
            if valid_files:
                event.acceptProposedAction()
                self.show_message(f"{len(valid_files)} desteklenen dosya algılandı")
        else:
            event.ignore()
    
    def dropEvent(self, event: QDropEvent):
        """Drop event"""
        try:
            urls = event.mimeData().urls()
            supported_extensions = {'.pdf', '.docx', '.doc', '.txt'}
            
            valid_files = [str(Path(url.toLocalFile())) for url in urls 
                          if url.isLocalFile() and 
                          Path(url.toLocalFile()).suffix.lower() in supported_extensions]
            
            if valid_files:
                event.acceptProposedAction()
                reply = QMessageBox.question(self, "Dosya Ekleme",
                    f"{len(valid_files)} dosya eklenecek. Devam?",
                    QMessageBox.Yes | QMessageBox.No)
                
                if reply == QMessageBox.Yes:
                    self._process_files_async(valid_files)
        
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Drop işlemi hatası:\n{e}")
    
    def closeEvent(self, event):
        """Pencere kapatılırken"""
        try:
            # Cleanup operations
            if hasattr(self.controller, 'file_operations'):
                # Stop any running operations
                pass
            
            self.logger.info("MainWindow closed")
            event.accept()
        except Exception as e:
            self.logger.error(f"Close event error: {e}")
            event.accept()
