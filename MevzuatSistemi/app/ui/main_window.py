"""
Ana pencere - Modern PyQt5 tabanlı kullanıcı arayüzü
Responsive tasarım ve modern bileşenlerle güncellenmiş ana uygulama penceresi
"""

import sys
import os
import logging
import time
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLineEdit, QTextEdit, QLabel, QComboBox, QCheckBox,
    QSplitter, QTreeWidget, QTreeWidgetItem, QTableWidget, QTableWidgetItem,
    QProgressBar, QStatusBar, QMenuBar, QMenu, QAction, QFileDialog,
    QMessageBox, QTabWidget, QGroupBox, QSpinBox, QSlider,
    QApplication, QHeaderView, QFrame
)
from PyQt5.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QSize, QPoint, QUrl
)
from PyQt5.QtGui import (
    QIcon, QFont, QPixmap, QPalette, QColor, QDragEnterEvent, QDropEvent
)

# Modern UI bileşenleri
from .modern import (
    MevzuatDesignSystem, ColorScheme, AdvancedThemeManager,
    ResponsiveManager, ModernButton, ModernCard, ResponsiveGrid,
    ButtonType, ButtonSize
)

from .search_widget import SearchWidget
from .result_widget import ResultWidget
from .document_tree_widget import DocumentTreeContainer
from .stats_widget import StatsWidget
from .document_viewer_widget import DocumentViewerWidget
from .settings_dialog import SettingsDialog
from .faceted_search_widget import FacetedSearchWidget
from ..core.search_engine import SearchResult

class FileWatcherStatus(QWidget):
    """Dosya izleyici durum widget'ı"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Status LED
        self.status_led = QLabel("●")
        self.status_led.setStyleSheet("color: red; font-size: 14px;")
        
        # Status text
        self.status_text = QLabel("File Watcher: Stopped")
        
        # Queue info
        self.queue_info = QLabel("Queue: 0")
        
        layout.addWidget(self.status_led)
        layout.addWidget(self.status_text)
        layout.addWidget(self.queue_info)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def update_status(self, is_running: bool, queue_size: int = 0):
        """Durumu güncelle"""
        if is_running:
            self.status_led.setStyleSheet("color: green; font-size: 14px;")
            self.status_text.setText("File Watcher: Running")
        else:
            self.status_led.setStyleSheet("color: red; font-size: 14px;")
            self.status_text.setText("File Watcher: Stopped")
        
        self.queue_info.setText(f"Queue: {queue_size}")

class MainWindow(QMainWindow):
    """Ana uygulama penceresi - Modern UI ile güncellenmiş"""
    
    def __init__(self, config, db, search_engine, document_processor, file_watcher):
        super().__init__()
        
        self.config = config
        self.db = db
        self.search_engine = search_engine
        self.document_processor = document_processor
        self.file_watcher = file_watcher
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Modern UI sistemi başlat
        self.design_system = MevzuatDesignSystem()
        self.design_system.apply_theme(ColorScheme.LIGHT_PROFESSIONAL)  # Tema uygula
        self.theme_manager = AdvancedThemeManager(self.design_system)  # design_system objesini geç
        self.responsive_manager = ResponsiveManager()
        
        # UI state
        self.last_search_results: List[SearchResult] = []
        self.current_document = None
        
        # Modern UI bileşenleri
        self.modern_components = {}
        
        # Timers
        self.status_update_timer = QTimer()
        self.status_update_timer.timeout.connect(self.update_status)
        self.status_update_timer.start(5000)  # 5 saniye
        
        # Drag & Drop desteği
        self.setAcceptDrops(True)
        
        # Responsive davranış
        self.responsive_manager.breakpoint_changed.connect(self.on_breakpoint_changed)
        
        self.init_modern_ui()
        self.load_settings()
        
        # Favoriler listesini yükle
        self.refresh_favorites()
        
        self.logger.info("Ana pencere başlatıldı - Modern UI aktif")
    
    def init_modern_ui(self):
        """Modern UI bileşenlerini oluştur"""
        self.setWindowTitle("Mevzuat Belge Analiz & Sorgulama Sistemi v1.0.2")
        self.setGeometry(100, 100, 1400, 800)
        
        # Ana widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Modern responsive layout
        self.main_grid = ResponsiveGrid(central_widget)
        
        # Menu bar
        self.create_modern_menu_bar()
        
        # Toolbar
        self.create_modern_toolbar()
        
        # Ana içerik kartları
        self.create_modern_layout()
        
        # Status bar
        self.create_modern_status_bar()
        
        # Modern tema uygula
        self.apply_modern_theme()
        
    def create_modern_layout(self):
        """Modern responsive layout oluştur"""
        # Sol panel - Belge ağacı ve filtreler
        left_card = ModernCard("Belgeler ve Filtreler")
        left_panel = self.create_modern_left_panel()
        left_card.set_content(left_panel)
        
        # Orta panel - Arama ve sonuçlar
        middle_card = ModernCard("Arama ve Sonuçlar")
        middle_panel = self.create_modern_middle_panel()
        middle_card.set_content(middle_panel)
        
        # Sağ panel - Detaylar
        right_card = ModernCard("Belge Detayları")
        right_panel = self.create_modern_right_panel()
        right_card.set_content(right_panel)
        
        # Responsive grid'e ekle
        self.main_grid.add_widget(left_card, 0, 0, 1, 1)    # Sol
        self.main_grid.add_widget(middle_card, 0, 1, 1, 2)  # Orta (2 kolon)
        self.main_grid.add_widget(right_card, 0, 3, 1, 1)   # Sağ
        
        # Modern bileşenleri sakla
        self.modern_components.update({
            'left_card': left_card,
            'middle_card': middle_card, 
            'right_card': right_card,
            'main_grid': self.main_grid
        })
    
    def on_breakpoint_changed(self, breakpoint):
        """Responsive breakpoint değiştiğinde layout'u ayarla"""
        if hasattr(self, 'main_grid') and self.main_grid:
            if breakpoint in ['mobile', 'tablet']:
                # Mobil/tablet için stacked layout
                self.main_grid.stack_layout()
            else:
                # Desktop için yan yana layout
                self.main_grid.grid_layout_mode()
    
    def create_modern_menu_bar(self):
        """Modern menu çubuğunu oluştur"""
        menubar = self.menuBar()
        
        # Modern stil uygula
        menubar.setStyleSheet(self.theme_manager.get_menu_styles())
        
        # Dosya menüsü
        file_menu = menubar.addMenu('📁 Dosya')
        
        # Belge ekleme seçenekleri
        add_files_action = QAction('➕ Dosya Seçerek Belge Ekle', self)
        add_files_action.setShortcut('Ctrl+O')
        add_files_action.setStatusTip('Bilgisayarınızdan dosya seçerek mevzuat belgesi ekleyin')
        add_files_action.triggered.connect(self.select_and_process_files)
        file_menu.addAction(add_files_action)
        
        # Raw klasör tarama
        scan_action = QAction('🔍 Raw Klasörü Tara', self)
        scan_action.setStatusTip('Raw klasöründeki işlenmemiş dosyaları sistem otomatik tarar')
        scan_action.triggered.connect(self.scan_raw_folder)
        file_menu.addAction(scan_action)
        
        file_menu.addSeparator()
        
        # Dışa aktar
        export_action = QAction('📄 PDF Rapor Oluştur', self)
        export_action.setShortcut('Ctrl+E')
        export_action.triggered.connect(self.export_results)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Çıkış
        exit_action = QAction('🚪 Çıkış', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Belge yönetimi menüsü
        document_menu = menubar.addMenu('📄 Belge Yönetimi')
        
        # Belge listesi
        list_docs_action = QAction('📋 Tüm Belgeler', self)
        list_docs_action.setStatusTip('Sistemdeki tüm belgeleri listeler')
        list_docs_action.triggered.connect(self.show_all_documents)
        document_menu.addAction(list_docs_action)
        
        document_menu.addSeparator()
        
        # Belge bakımı
        check_docs_action = QAction('🔍 Eksik Belgeleri Kontrol Et', self)
        check_docs_action.setStatusTip('Veritabanında kayıtlı ama dosyası eksik olan belgeleri bulur')
        check_docs_action.triggered.connect(self.check_missing_documents)
        document_menu.addAction(check_docs_action)
        
        # Araçlar menüsü
        tools_menu = menubar.addMenu('🔧 Araçlar')
        
        # İndeks yeniden oluştur
        rebuild_index_action = QAction('🔄 Semantik İndeksi Yeniden Oluştur', self)
        rebuild_index_action.setStatusTip('Tüm belgeler için arama indeksini yeniden oluşturur')
        rebuild_index_action.triggered.connect(self.rebuild_semantic_index)
        tools_menu.addAction(rebuild_index_action)
        
        # Veritabanı bakımı
        vacuum_action = QAction('🗂️ Veritabanı Bakımı', self)
        vacuum_action.setStatusTip('Veritabanını optimize eder ve gereksiz alanları temizler')
        vacuum_action.triggered.connect(self.vacuum_database)
        tools_menu.addAction(vacuum_action)
        
        tools_menu.addSeparator()
        
        # Ayarlar
        settings_action = QAction('⚙️ Ayarlar', self)
        settings_action.setShortcut('Ctrl+,')
        settings_action.triggered.connect(self.open_settings)
        tools_menu.addAction(settings_action)
        
        # Yardım menüsü
        help_menu = menubar.addMenu('❓ Yardım')
        
        # Kullanım Kılavuzu
        help_action = QAction('📚 Kullanım Kılavuzu', self)
        help_action.setShortcut('F1')
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)
        
        help_menu.addSeparator()
        
        # Hakkında
        about_action = QAction('ℹ️ Hakkında', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_modern_toolbar(self):
        """Modern toolbar oluştur"""
        toolbar = self.addToolBar('Ana Araçlar')
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        toolbar.setStyleSheet(self.design_system.get_toolbar_styles())
        
        # Modern butonları oluştur
        add_files_btn = ModernButton(
            "📄 Belge Ekle",
            ButtonType.PRIMARY,
            ButtonSize.MEDIUM
        )
        add_files_btn.setToolTip('Dosya seçerek yeni belge ekle (Ctrl+O)')
        add_files_btn.clicked.connect(self.select_and_process_files)
        toolbar.addWidget(add_files_btn)
        
        scan_btn = ModernButton(
            "🔍 Raw Tara", 
            ButtonType.SECONDARY,
            ButtonSize.MEDIUM
        )
        scan_btn.setToolTip('Raw klasörünü otomatik tara')
        scan_btn.clicked.connect(self.scan_raw_folder)
        toolbar.addWidget(scan_btn)
        
        toolbar.addSeparator()
        
        rebuild_btn = ModernButton(
            "🔄 İndeksi Yenile",
            ButtonType.ACCENT,
            ButtonSize.MEDIUM
        )
        rebuild_btn.setToolTip('Arama indeksini yeniden oluştur')
        rebuild_btn.clicked.connect(self.rebuild_semantic_index)
        toolbar.addWidget(rebuild_btn)
        
        toolbar.addSeparator()
        
        settings_btn = ModernButton(
            "⚙️ Ayarlar",
            ButtonType.TERTIARY,
            ButtonSize.MEDIUM
        )
        settings_btn.clicked.connect(self.open_settings)
        toolbar.addWidget(settings_btn)
        
        # Modern bileşenleri sakla
        self.modern_components.update({
            'toolbar_add_files': add_files_btn,
            'toolbar_scan': scan_btn,
            'toolbar_rebuild': rebuild_btn,
            'toolbar_settings': settings_btn
        })
        """Menu çubuğunu oluştur"""
        menubar = self.menuBar()
        
        # Dosya menüsü
        file_menu = menubar.addMenu('📁 Dosya')
        
        # Belge ekleme seçenekleri
        add_files_action = QAction('➕ Dosya Seçerek Belge Ekle', self)
        add_files_action.setShortcut('Ctrl+O')
        add_files_action.setStatusTip('Bilgisayarınızdan dosya seçerek mevzuat belgesi ekleyin')
        add_files_action.triggered.connect(self.select_and_process_files)
        file_menu.addAction(add_files_action)
        
        # Raw klasör tarama
        scan_action = QAction('🔍 Raw Klasörü Tara', self)
        scan_action.setStatusTip('Raw klasöründeki işlenmemiş dosyaları sistem otomatik tarar')
        scan_action.triggered.connect(self.scan_raw_folder)
        file_menu.addAction(scan_action)
        
        file_menu.addSeparator()
        
        # Dışa aktar
        export_action = QAction('📄 PDF Rapor Oluştur', self)
        export_action.setShortcut('Ctrl+E')
        export_action.triggered.connect(self.export_results)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Çıkış
        exit_action = QAction('🚪 Çıkış', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Belge yönetimi menüsü
        document_menu = menubar.addMenu('📄 Belge Yönetimi')
        
        # Belge listesi
        list_docs_action = QAction('📋 Tüm Belgeler', self)
        list_docs_action.setStatusTip('Sistemdeki tüm belgeleri listeler')
        list_docs_action.triggered.connect(self.show_all_documents)
        document_menu.addAction(list_docs_action)
        
        document_menu.addSeparator()
        
        # Belge bakımı
        check_docs_action = QAction('🔍 Eksik Belgeleri Kontrol Et', self)
        check_docs_action.setStatusTip('Veritabanında kayıtlı ama dosyası eksik olan belgeleri bulur')
        check_docs_action.triggered.connect(self.check_missing_documents)
        document_menu.addAction(check_docs_action)
        
        # Araçlar menüsü
        tools_menu = menubar.addMenu('🔧 Araçlar')
        
        # İndeks yeniden oluştur
        rebuild_index_action = QAction('🔄 Semantik İndeksi Yeniden Oluştur', self)
        rebuild_index_action.setStatusTip('Tüm belgeler için arama indeksini yeniden oluşturur')
        rebuild_index_action.triggered.connect(self.rebuild_semantic_index)
        tools_menu.addAction(rebuild_index_action)
        
        # Veritabanı bakımı
        vacuum_action = QAction('🗂️ Veritabanı Bakımı', self)
        vacuum_action.setStatusTip('Veritabanını optimize eder ve gereksiz alanları temizler')
        vacuum_action.triggered.connect(self.vacuum_database)
        tools_menu.addAction(vacuum_action)
        
        tools_menu.addSeparator()
        
        # Ayarlar
        settings_action = QAction('⚙️ Ayarlar', self)
        settings_action.setShortcut('Ctrl+,')
        settings_action.triggered.connect(self.open_settings)
        tools_menu.addAction(settings_action)
        
        # Yardım menüsü
        help_menu = menubar.addMenu('❓ Yardım')
        
        # Kullanım Kılavuzu
        help_action = QAction('📚 Kullanım Kılavuzu', self)
        help_action.setShortcut('F1')
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)
        
        help_menu.addSeparator()
        
        # Hakkında
        about_action = QAction('ℹ️ Hakkında', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        """Toolbar oluştur"""
        toolbar = self.addToolBar('Ana Araçlar')
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        
        # Belge ekleme butonu (ana özellik)
        add_files_action = toolbar.addAction('📄➕ Belge Ekle')
        add_files_action.setStatusTip('Dosya seçerek yeni belge ekle (Ctrl+O)')
        add_files_action.triggered.connect(self.select_and_process_files)
        
        # Raw klasör tarama
        scan_action = toolbar.addAction('� Raw Tara')
        scan_action.setStatusTip('Raw klasörünü otomatik tara')
        scan_action.triggered.connect(self.scan_raw_folder)
        
        toolbar.addSeparator()
        
        # İndeks yeniden oluşturma
        rebuild_action = toolbar.addAction('🔄 İndeksi Yenile')
        rebuild_action.setStatusTip('Arama indeksini yeniden oluştur')
        rebuild_action.triggered.connect(self.rebuild_semantic_index)
        
        toolbar.addSeparator()
        
        # Ayarlar
        settings_action = toolbar.addAction('⚙️ Ayarlar')
        settings_action.triggered.connect(self.open_settings)
    
    def create_left_panel(self) -> QWidget:
        """Sol panel - belge ağacı ve filtreler"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Başlık
        title_label = QLabel("Belgeler ve Filtreler")
        title_label.setFont(QFont("", 10, QFont.Bold))
        layout.addWidget(title_label)
        
        # Belge ağacı
        self.document_tree = DocumentTreeContainer(self.db)
        self.document_tree.document_selected.connect(self.on_document_selected)
        self.document_tree.document_view_in_new_tab_requested.connect(self.view_document)
        layout.addWidget(self.document_tree)
        
        # Filtre grubu
        filter_group = QGroupBox("Filtreler")
        filter_layout = QVBoxLayout(filter_group)
        
        # Belge türü filtresi
        filter_layout.addWidget(QLabel("Belge Türü:"))
        self.document_type_combo = QComboBox()
        self.document_type_combo.addItems([
            "Tümü", "ANAYASA", "KANUN", "KHK", "TÜZÜK", 
            "YÖNETMELİK", "YÖNERGE", "TEBLİĞ", "KARAR"
        ])
        self.document_type_combo.currentTextChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.document_type_combo)
        
        # Mülga dahil etme
        self.include_repealed_checkbox = QCheckBox("Mülga maddeleri dahil et")
        self.include_repealed_checkbox.toggled.connect(self.on_filter_changed)
        filter_layout.addWidget(self.include_repealed_checkbox)
        
        # Değişiklik dahil etme
        self.include_amended_checkbox = QCheckBox("Değişiklik içerenleri göster")
        self.include_amended_checkbox.setChecked(True)
        self.include_amended_checkbox.toggled.connect(self.on_filter_changed)
        filter_layout.addWidget(self.include_amended_checkbox)
        
        layout.addWidget(filter_group)
        
        # Favori maddeler
        favorites_group = QGroupBox("Favoriler")
        favorites_layout = QVBoxLayout(favorites_group)
        
        self.favorites_list = QTreeWidget()
        self.favorites_list.setHeaderLabels(["Başlık", "Belge"])
        self.favorites_list.itemDoubleClicked.connect(self.on_favorite_selected)
        favorites_layout.addWidget(self.favorites_list)
        
        # Favori ekleme butonu
        add_favorite_btn = QPushButton("Favori Ekle")
        add_favorite_btn.clicked.connect(self.add_to_favorites)
        favorites_layout.addWidget(add_favorite_btn)
        
        layout.addWidget(favorites_group)
        
        # Son aramalar
        recent_group = QGroupBox("Son Aramalar")
        recent_layout = QVBoxLayout(recent_group)
        
        self.recent_searches_list = QTreeWidget()
        self.recent_searches_list.setHeaderLabels(["Sorgu", "Tarih"])
        self.recent_searches_list.itemDoubleClicked.connect(self.on_recent_search_selected)
        recent_layout.addWidget(self.recent_searches_list)
        
        layout.addWidget(recent_group)
        
        return panel
    
    def create_middle_panel(self) -> QWidget:
        """Orta panel - arama ve sonuçlar"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Ana tab widget - arama türleri için
        self.search_tab_widget = QTabWidget()
        
        # 1. Klasik Arama sekmesi
        classic_search_tab = QWidget()
        classic_layout = QVBoxLayout(classic_search_tab)
        
        # Arama widget'ı
        self.search_widget = SearchWidget(self.search_engine, parent=self, config=self.config)
        self.search_widget.search_requested.connect(self.perform_search)
        classic_layout.addWidget(self.search_widget)
        
        # Sonuç sayısı ve bilgi
        info_layout = QHBoxLayout()
        self.result_count_label = QLabel("Sonuç bulunamadı")
        info_layout.addWidget(self.result_count_label)
        info_layout.addStretch()
        
        # Sıralama seçeneği
        info_layout.addWidget(QLabel("Sıralama:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Relevans", "Tarih (Yeni)", "Tarih (Eski)", "Belge Türü"])
        self.sort_combo.currentTextChanged.connect(self.sort_results)
        info_layout.addWidget(self.sort_combo)
        
        classic_layout.addLayout(info_layout)
        
        # Sonuç widget'ı
        self.result_widget = ResultWidget()
        self.result_widget.result_selected.connect(self.on_result_selected)
        self.result_widget.add_note_requested.connect(self.add_note_to_article)
        self.result_widget.document_delete_requested.connect(self.delete_document)
        self.result_widget.document_view_requested.connect(self.view_document)
        self.result_widget.document_view_in_new_tab_requested.connect(self.view_document)  # Aynı fonksiyon kullanılabilir
        classic_layout.addWidget(self.result_widget)
        
        self.search_tab_widget.addTab(classic_search_tab, "Klasik Arama")
        
        # 2. Faceted Search sekmesi
        self.faceted_search_widget = FacetedSearchWidget()
        self.faceted_search_widget.searchRequested.connect(self.perform_faceted_search)
        self.search_tab_widget.addTab(self.faceted_search_widget, "Gelişmiş Filtreleme")
        
        layout.addWidget(self.search_tab_widget)
        
        return panel
    
    def create_right_panel(self) -> QWidget:
        """Sağ panel - detay ve istatistikler"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Tab widget
        tab_widget = QTabWidget()
        
        # Detay sekmesi
        detail_tab = QWidget()
        detail_layout = QVBoxLayout(detail_tab)
        
        # Detay başlığı
        self.detail_title_label = QLabel("Detay")
        self.detail_title_label.setFont(QFont("", 12, QFont.Bold))
        detail_layout.addWidget(self.detail_title_label)
        
        # Detay içeriği
        self.detail_content = QTextEdit()
        self.detail_content.setReadOnly(True)
        detail_layout.addWidget(self.detail_content)
        
        # Not ekleme alanı
        notes_group = QGroupBox("Notlar")
        notes_layout = QVBoxLayout(notes_group)
        
        self.notes_text = QTextEdit()
        self.notes_text.setMaximumHeight(100)
        notes_layout.addWidget(self.notes_text)
        
        notes_btn_layout = QHBoxLayout()
        save_note_btn = QPushButton("Not Kaydet")
        save_note_btn.clicked.connect(self.save_note)
        notes_btn_layout.addWidget(save_note_btn)
        
        clear_note_btn = QPushButton("Temizle")
        clear_note_btn.clicked.connect(lambda: self.notes_text.clear())
        notes_btn_layout.addWidget(clear_note_btn)
        
        notes_layout.addLayout(notes_btn_layout)
        detail_layout.addWidget(notes_group)
        
        tab_widget.addTab(detail_tab, "Detay")
        
        # Belge görüntüleme sekmesi (varsayılan)
        self.document_viewer = DocumentViewerWidget(self.config, self.db)
        self.document_viewer.document_updated.connect(self.refresh_all)
        self.document_viewer.document_deleted.connect(self.on_document_deleted)
        self.document_viewer.note_added.connect(self.refresh_all)
        self.document_viewer.open_in_new_tab_requested.connect(self.view_document)
        tab_widget.addTab(self.document_viewer, "Belge Görüntüleme")
        
        # İstatistik sekmesi
        self.stats_widget = StatsWidget(self.db, self.search_engine)
        tab_widget.addTab(self.stats_widget, "İstatistikler")
        
        # Tab widget'ı sınıf değişkeni olarak sakla
        self.right_panel_tabs = tab_widget
        
        # Sekme kapama özelliği
        tab_widget.setTabsClosable(True)
        tab_widget.tabCloseRequested.connect(self.close_document_tab)
        
        layout.addWidget(tab_widget)
        
        return panel
    
    def create_status_bar(self):
        """Status bar oluştur"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # File watcher status
        self.file_watcher_status = FileWatcherStatus()
        self.status_bar.addPermanentWidget(self.file_watcher_status)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Ana klasör gösterimi
        base_folder = self.config.get('base_folder', '')
        self.status_bar.showMessage(f"Ana Klasör: {base_folder}")
    
    def apply_theme(self):
        """Tema uygula"""
        theme = self.config.get('preferences.theme', 'system')
        
        if theme == 'dark':
            self.setStyleSheet("""
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
            """)
    
    def load_settings(self):
        """Ayarları yükle"""
        # Pencere pozisyonu ve boyutu
        if self.config.get('preferences.save_window_position', True):
            # TODO: Implement window position loading
            pass
        
        # Font boyutu
        font_size = self.config.get('preferences.font_size', 'medium')
        if font_size == 'large':
            font = self.font()
            font.setPointSize(font.pointSize() + 2)
            self.setFont(font)
        elif font_size == 'small':
            font = self.font()
            font.setPointSize(font.pointSize() - 1)
            self.setFont(font)
    
    def perform_search(self, query: str, search_type: str):
        """Arama gerçekleştir"""
        if not query.strip():
            return
        
        self.status_bar.showMessage("Arama yapılıyor...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        
        try:
            # Filtreleri al
            document_types = []
            selected_type = self.document_type_combo.currentText()
            if selected_type != "Tümü":
                document_types = [selected_type]
            
            include_repealed = self.include_repealed_checkbox.isChecked()
            
            # Arama yap
            results = self.search_engine.search(
                query=query,
                document_types=document_types,
                search_type=search_type,
                include_repealed=include_repealed
            )
            
            self.last_search_results = results
            
            # Sonuçları göster
            self.result_widget.display_results(results)
            
            # Sonuç sayısını güncelle
            self.result_count_label.setText(f"{len(results)} sonuç bulundu")
            
            # Status
            self.status_bar.showMessage(f"Arama tamamlandı: {len(results)} sonuç")
            
        except Exception as e:
            self.logger.error(f"Arama hatası: {e}")
            QMessageBox.critical(self, "Hata", f"Arama sırasında hata oluştu:\n{e}")
            self.status_bar.showMessage("Arama başarısız")
        
        finally:
            self.progress_bar.setVisible(False)

    def perform_faceted_search(self, query: str, facet_filters: dict):
        """Faceted search gerçekleştir"""
        # Boş query ise varsayılan arama yap
        if not query.strip():
            query = "*"  # Tüm dokümanları getir
        
        self.status_bar.showMessage("Gelişmiş filtreleme yapılıyor...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        
        try:
            # Faceted search gerçekleştir
            faceted_results = self.search_engine.search_with_facets(
                query=query,
                search_type='mixed',  # Hibrit arama kullan
                facet_filters=facet_filters
            )
            
            # Sonuçları faceted search widget'ına aktar
            self.faceted_search_widget.update_results(faceted_results, query)
            
            # Ana sonuç widget'ına da aktar (faceted search sekmesi için)
            faceted_results_widget = self.faceted_search_widget.get_results_widget()
            
            # Faceted search sonuçları için özel result widget oluştur
            if not hasattr(self, 'faceted_result_widget'):
                from .result_widget import ResultWidget
                self.faceted_result_widget = ResultWidget()
                self.faceted_result_widget.result_selected.connect(self.on_result_selected)
                self.faceted_result_widget.add_note_requested.connect(self.add_note_to_article)
                self.faceted_result_widget.document_delete_requested.connect(self.delete_document)
                self.faceted_result_widget.document_view_requested.connect(self.view_document)
                
                # Faceted search sekmesinin results widget'ına ekle
                faceted_results_layout = QVBoxLayout()
                faceted_results_layout.addWidget(self.faceted_result_widget)
                faceted_results_widget.setLayout(faceted_results_layout)
            
            # Sonuçları göster
            self.faceted_result_widget.display_results(faceted_results.documents)
            
            # Status
            self.status_bar.showMessage(
                f"Gelişmiş filtreleme tamamlandı: {faceted_results.filtered_count} / {faceted_results.total_count} sonuç"
            )
            
        except Exception as e:
            self.logger.error(f"Faceted search hatası: {e}")
            QMessageBox.critical(self, "Hata", f"Gelişmiş filtreleme sırasında hata oluştu:\n{e}")
            self.status_bar.showMessage("Gelişmiş filtreleme başarısız")
        
        finally:
            self.progress_bar.setVisible(False)

    def sort_results(self, sort_type: str):
        """Sonuçları sırala"""
        if not self.last_search_results:
            return
        
        if sort_type == "Relevans":
            self.last_search_results.sort(key=lambda x: x.score, reverse=True)
        elif sort_type == "Tarih (Yeni)":
            # TODO: Implement date sorting
            pass
        elif sort_type == "Tarih (Eski)":
            # TODO: Implement date sorting
            pass
        elif sort_type == "Belge Türü":
            self.last_search_results.sort(key=lambda x: x.document_type)
        
        self.result_widget.display_results(self.last_search_results)
    
    def on_result_selected(self, result: SearchResult):
        """Sonuç seçildiğinde"""
        self.display_article_detail(result)
    
    def display_article_detail(self, result: SearchResult):
        """Madde detayını göster"""
        # Aktif madde ID'sini sakla
        self.current_article_id = result.id
        
        # Başlık
        title = f"{result.document_title}"
        if result.law_number:
            title += f" (Kanun No: {result.law_number})"
        if result.article_number:
            title += f" - Madde {result.article_number}"
        
        self.detail_title_label.setText(title)
        
        # İçerik
        content = f"<h3>{result.title}</h3>\n" if result.title else ""
        content += f"<p>{result.content}</p>"
        
        # Highlight'ları ekle
        if result.highlights:
            content += "<h4>İlgili Bölümler:</h4>"
            for highlight in result.highlights:
                content += f"<p><i>...{highlight}...</i></p>"
        
        # Meta bilgiler
        content += "<hr><h4>Belge Bilgileri:</h4>"
        content += f"<p><strong>Tür:</strong> {result.document_type}</p>"
        if result.law_number:
            content += f"<p><strong>Kanun Numarası:</strong> {result.law_number}</p>"
        content += f"<p><strong>Durum:</strong> "
        if result.is_repealed:
            content += "Mülga"
        elif result.is_amended:
            content += "Değişiklik var"
        else:
            content += "Aktif"
        content += "</p>"
        content += f"<p><strong>Skor:</strong> {result.score:.3f} ({result.match_type})</p>"
        
        self.detail_content.setHtml(content)
        
        # Mevcut notları yükle
        self.load_article_notes(result.id)
    
    def load_article_notes(self, article_id: int):
        """Madde notlarını yükle"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("""
                SELECT content FROM user_notes 
                WHERE article_id = ? 
                ORDER BY created_at DESC 
                LIMIT 1
            """, (article_id,))
            
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                self.notes_text.setPlainText(result[0])
            else:
                self.notes_text.clear()
                
        except Exception as e:
            self.logger.error(f"Not yükleme hatası: {e}")
    
    def save_note(self):
        """Not kaydet"""
        if not hasattr(self, 'current_article_id'):
            QMessageBox.information(self, "Bilgi", "Önce bir madde seçin")
            return
        
        note_content = self.notes_text.toPlainText().strip()
        if not note_content:
            return
        
        try:
            from datetime import datetime
            
            with self.db.transaction() as cursor:
                # Mevcut notu kontrol et
                cursor.execute("""
                    SELECT id FROM user_notes WHERE article_id = ?
                """, (self.current_article_id,))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Güncelle
                    cursor.execute("""
                        UPDATE user_notes 
                        SET content = ?, updated_at = ?
                        WHERE article_id = ?
                    """, (note_content, datetime.now().isoformat(), self.current_article_id))
                else:
                    # Yeni ekle
                    cursor.execute("""
                        INSERT INTO user_notes (article_id, content, created_at)
                        VALUES (?, ?, ?)
                    """, (self.current_article_id, note_content, datetime.now().isoformat()))
            
            self.status_bar.showMessage("Not kaydedildi", 3000)
            
        except Exception as e:
            self.logger.error(f"Not kaydetme hatası: {e}")
            QMessageBox.critical(self, "Hata", f"Not kaydedilirken hata oluştu:\n{e}")
    
    def on_document_selected(self, document_data: dict):
        """Belge seçildiğinde"""
        self.current_document = document_data
        # TODO: Implement document details display
    
    def on_filter_changed(self):
        """Filtre değiştiğinde"""
        # Eğer aktif arama varsa yeniden çalıştır
        if hasattr(self.search_widget, 'last_query') and self.search_widget.last_query:
            self.perform_search(self.search_widget.last_query, self.search_widget.last_search_type)
    
    def manual_scan(self):
        """Manuel tarama başlat - dosya seçimi veya raw klasör taraması"""
        # İki seçenek sun: Dosya seçimi veya raw klasör taraması
        reply = QMessageBox.question(
            self, "Belge Ekleme Seçimi",
            "Belge ekleme yöntemini seçin:\n\n" +
            "YES: Dosya seçerek ekle\n" +
            "NO: Raw klasörünü tara\n" +
            "CANCEL: İptal",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
        )
        
        if reply == QMessageBox.Yes:
            # Dosya seçim dialog'u
            self.select_and_process_files()
        elif reply == QMessageBox.No:
            # Raw klasör taraması
            self.scan_raw_folder()
        # Cancel ise hiçbir şey yapma
    
    def select_and_process_files(self):
        """Dosya seçim dialog'u ile belge ekleme"""
        try:
            files, _ = QFileDialog.getOpenFileNames(
                self, 
                "Mevzuat Belgelerini Seçin",
                "",
                "Desteklenen Dosyalar (*.pdf *.docx *.doc *.txt);;PDF Dosyaları (*.pdf);;Word Dosyaları (*.docx *.doc);;Metin Dosyaları (*.txt);;Tüm Dosyalar (*)"
            )
            
            if not files:
                return
            
            # Progress bar göster
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, len(files))
            
            processed_count = 0
            failed_files = []
            
            for i, file_path in enumerate(files):
                self.progress_bar.setValue(i)
                self.status_bar.showMessage(f"İşleniyor: {Path(file_path).name}")
                QApplication.processEvents()  # UI'yı güncelle
                
                try:
                    # Dosyayı doğrudan işle
                    result = self.document_processor.process_file(file_path)
                    
                    if result['success']:
                        processed_count += 1
                        self.logger.info(f"Dosya başarıyla eklendi: {file_path}")
                    else:
                        failed_files.append(f"{Path(file_path).name}: {result.get('error', 'Bilinmeyen hata')}")
                        self.logger.error(f"Dosya ekleme başarısız: {file_path} - {result.get('error')}")
                        
                except Exception as e:
                    failed_files.append(f"{Path(file_path).name}: {str(e)}")
                    self.logger.error(f"Dosya işleme exception: {file_path} - {e}")
            
            # Sonucu göster
            self.progress_bar.setVisible(False)
            
            if failed_files:
                error_msg = f"İşlem tamamlandı:\n\n" +\
                           f"Başarılı: {processed_count} dosya\n" +\
                           f"Başarısız: {len(failed_files)} dosya\n\n" +\
                           "Başarısız dosyalar:\n" + "\n".join(failed_files[:10])
                if len(failed_files) > 10:
                    error_msg += f"\n... ve {len(failed_files)-10} dosya daha"
                    
                QMessageBox.warning(self, "Belge Ekleme Sonucu", error_msg)
            else:
                QMessageBox.information(
                    self, "Başarılı", 
                    f"Tüm dosyalar başarıyla eklendi!\n\nToplam: {processed_count} dosya"
                )
            
            # Belge ağacını yenile
            self.document_tree.refresh_tree()
            self.stats_widget.refresh_stats()
            self.status_bar.showMessage(f"Belge ekleme tamamlandı: {processed_count} başarılı", 5000)
            
        except Exception as e:
            self.progress_bar.setVisible(False)
            self.logger.error(f"Dosya seçimi hatası: {e}")
            QMessageBox.critical(self, "Hata", f"Dosya seçimi sırasında hata oluştu:\n{e}")
    
    def scan_raw_folder(self):
        """Raw klasörünü tara"""
        if not self.file_watcher:
            QMessageBox.information(self, "Bilgi", "File Watcher aktif değil")
            return
        
        reply = QMessageBox.question(
            self, "Raw Klasör Tarama",
            "Raw klasöründeki işlenmemiş dosyalar taranacak. Devam edilsin mi?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                files_added = self.file_watcher.manual_scan()
                QMessageBox.information(
                    self, "Manuel Tarama",
                    f"Tarama tamamlandı. {files_added} dosya işleme kuyruğuna eklendi."
                )
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Manuel tarama hatası:\n{e}")
    
    def rebuild_semantic_index(self):
        """Semantik indeksi yeniden oluştur"""
        reply = QMessageBox.question(
            self, "İndeks Yenileme",
            "Tüm semantik indeks yeniden oluşturulacak. Bu işlem uzun sürebilir. Devam edilsin mi?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.status_bar.showMessage("Semantik indeks yeniden oluşturuluyor...")
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)
            
            try:
                success = self.search_engine.rebuild_index()
                if success:
                    QMessageBox.information(self, "Başarılı", "Semantik indeks yeniden oluşturuldu")
                    self.status_bar.showMessage("İndeks yenileme tamamlandı", 3000)
                else:
                    QMessageBox.warning(self, "Uyarı", "İndeks yenileme sırasında sorunlar oluştu")
                    self.status_bar.showMessage("İndeks yenileme başarısız", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"İndeks yenileme hatası:\n{e}")
                self.status_bar.showMessage("İndeks yenileme hatası", 3000)
            finally:
                self.progress_bar.setVisible(False)
    
    def vacuum_database(self):
        """Veritabanı bakımı"""
        reply = QMessageBox.question(
            self, "Veritabanı Bakımı",
            "Veritabanı bakımı yapılacak. Bu işlem birkaç dakika sürebilir. Devam edilsin mi?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.status_bar.showMessage("Veritabanı bakımı yapılıyor...")
                self.db.vacuum()
                QMessageBox.information(self, "Başarılı", "Veritabanı bakımı tamamlandı")
                self.status_bar.showMessage("Veritabanı bakımı tamamlandı", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Veritabanı bakım hatası:\n{e}")
    
    def export_results(self):
        """Sonuçları PDF'e aktar"""
        if not self.last_search_results:
            QMessageBox.information(self, "Bilgi", "Dışa aktarılacak sonuç bulunamadı")
            return
        
        # Dosya adı seç
        filename, _ = QFileDialog.getSaveFileName(
            self, "PDF Rapor Kaydet", 
            f"arama_sonuclari_{int(time.time())}.pdf",
            "PDF Files (*.pdf)"
        )
        
        if filename:
            try:
                from ..utils.pdf_exporter import PDFExporter
                
                # PDF exporter oluştur
                pdf_exporter = PDFExporter(self.config)
                
                if not pdf_exporter.is_available():
                    QMessageBox.warning(
                        self, "Uyarı", 
                        "PDF export için ReportLab kütüphanesi kurulu değil.\n\n"
                        "Kurulum için: pip install reportlab"
                    )
                    return
                
                # Progress bar göster
                self.progress_bar.setVisible(True)
                self.progress_bar.setRange(0, 0)  # Indeterminate
                self.status_bar.showMessage("PDF raporu oluşturuluyor...")
                
                # Export işlemi
                result = pdf_exporter.export_search_results(
                    results=self.current_results,
                    query=self.search_input.text() if hasattr(self, 'search_input') else 'Arama sorgusu',
                    output_path=filename,
                    include_highlights=True,
                    include_metadata=True
                )
                
                self.progress_bar.setVisible(False)
                
                if result['success']:
                    file_size_mb = result['file_size'] / (1024 * 1024)
                    QMessageBox.information(
                        self, "Başarılı", 
                        f"PDF raporu başarıyla oluşturuldu!\n\n"
                        f"Dosya: {filename}\n"
                        f"Sonuç Sayısı: {result['results_count']}\n"
                        f"Dosya Boyutu: {file_size_mb:.2f} MB"
                    )
                    
                    # Dosyayı açma seçeneği
                    reply = QMessageBox.question(
                        self, "PDF Aç", 
                        "PDF dosyasını şimdi açmak ister misiniz?",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    
                    if reply == QMessageBox.Yes:
                        import subprocess
                        subprocess.run(['start', filename], shell=True, check=False)
                else:
                    QMessageBox.critical(
                        self, "Hata", 
                        f"PDF oluşturulamadı:\n{result['error']}"
                    )
                
            except ImportError:
                QMessageBox.warning(self, "Eksik Bağımlılık", "reportlab yüklü değil. requirements.txt içinden yükleyin: pip install reportlab")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"PDF export hatası:\n{e}")
    
    def open_settings(self):
        """Ayarlar penceresini aç"""
        dialog = SettingsDialog(self.config, self)
        if dialog.exec_() == SettingsDialog.Accepted:
            # Ayarlar değişti, UI'yi güncelle
            self.apply_theme()
            # File watcher'ı restart et (gerekiyorsa)
            # TODO: Implement settings application
    
    def update_status(self):
        """Durumu güncelle"""
        try:
            # File watcher durumu
            if self.file_watcher:
                status = self.file_watcher.get_status()
                self.file_watcher_status.update_status(
                    status['is_watching'],
                    status['queue_size']
                )
            
            # İstatistikleri güncelle
            if hasattr(self, 'stats_widget'):
                self.stats_widget.refresh_stats()
            
        except Exception as e:
            self.logger.error(f"Status güncelleme hatası: {e}")
    
    def show_help(self):
        """Kullanım kılavuzu göster"""
        help_text = """
        <h2>📚 Mevzuat Sistemi Kullanım Kılavuzu</h2>
        
        <h3>🔹 Belge Ekleme Yöntemleri:</h3>
        <ul>
        <li><b>Dosya Seçimi (Önerilen):</b> Menü > Dosya > "Dosya Seçerek Belge Ekle" veya Ctrl+O</li>
        <li><b>Drag & Drop:</b> Dosyaları doğrudan ana pencereye sürükleyip bırakın</li>
        <li><b>Raw Klasör Tarama:</b> Raw klasörüne dosya koyup "Raw Klasörü Tara" butonunu kullanın</li>
        </ul>
        
        <h3>🔹 Desteklenen Dosya Türleri:</h3>
        <ul>
        <li>📄 PDF dosyaları (.pdf)</li>
        <li>📝 Word belgeleri (.docx, .doc)</li>
        <li>📋 Metin dosyaları (.txt)</li>
        </ul>
        
        <h3>🔹 Arama Özellikleri:</h3>
        <ul>
        <li><b>Semantik Arama:</b> Anlamsal benzerlik ile arama</li>
        <li><b>Anahtar Kelime:</b> Klasik kelime bazlı arama</li>
        <li><b>Karma Arama:</b> Her iki yöntemin kombinasyonu</li>
        <li><b>Filtreler:</b> Belge türü, mülga/aktif durumu filtreleme</li>
        </ul>
        
        <h3>🔹 İpuçları:</h3>
        <ul>
        <li>Dosya ekleme öncesi duplicate kontrol yapılır</li>
        <li>Minimum 50 karakter metin gerekliliği vardır</li>
        <li>Maksimum dosya boyutu: 50MB</li>
        <li>İndeksi düzenli olarak yenileyin (🔄)</li>
        <li>Favoriler ve notlar ekleyebilirsiniz</li>
        </ul>
        
        <h3>🔹 Sorun Giderme:</h3>
        <ul>
        <li><b>Dosya eklenmiyor:</b> Dosya boyutunu ve türünü kontrol edin</li>
        <li><b>Arama sonuç vermez:</b> İndeksi yenileyin</li>
        <li><b>Yavaş çalışma:</b> Veritabanı bakımı yapın</li>
        </ul>
        """
        
        QMessageBox.about(self, "Kullanım Kılavuzu", help_text)
    
    def show_about(self):
        """Hakkında dialog'u göster"""
        about_text = f"""
        <h2>Mevzuat Belge Analiz & Sorgulama Sistemi</h2>
        <p><b>Versiyon:</b> {self.config.get('app_version', '1.0.2')}</p>
        <p><b>Oluşturma Tarihi:</b> {self.config.get('creation_date', '')}</p>
        <p><b>Kullanıcı:</b> {self.config.get('user_id', '')}</p>
        <hr>
        <p>Bu yazılım mevzuat belgelerini otomatik olarak işleyip</p>
        <p>sorgulama imkanı sunan bir masaüstü uygulamasıdır.</p>
        <hr>
        <p><b>Ana Klasör:</b> {self.config.get('base_folder', '')}</p>
        <p><b>Veritabanı:</b> {self.config.get_db_path()}</p>
        """
        
        QMessageBox.about(self, "Hakkında", about_text)
    
    def on_favorite_selected(self, item, column):
        """Favori seçildiğinde"""
        try:
            # Favori item'dan madde bilgilerini al
            article_id = item.data(0, Qt.UserRole)
            if article_id:
                # Maddeyi veritabanından getir
                cursor = self.db.connection.cursor()
                cursor.execute("""
                    SELECT a.*, d.title as document_title, d.law_number, d.document_type
                    FROM articles a
                    JOIN documents d ON a.document_id = d.id
                    WHERE a.id = ?
                """, (article_id,))
                
                result = cursor.fetchone()
                cursor.close()
                
                if result:
                    columns = [desc[0] for desc in cursor.description]
                    article_data = dict(zip(columns, result))
                    
                    # SearchResult benzeri obje oluştur
                    from ..core.search_engine import SearchResult
                    search_result = SearchResult(
                        id=article_data['id'],
                        document_id=article_data['document_id'],
                        document_title=article_data['document_title'],
                        law_number=article_data.get('law_number', ''),
                        document_type=article_data['document_type'],
                        article_number=article_data.get('article_number', ''),
                        title=article_data.get('title', ''),
                        content=article_data['content'],
                        score=1.0,
                        match_type="favorite",
                        is_repealed=article_data.get('is_repealed', False),
                        is_amended=article_data.get('is_amended', False)
                    )
                    
                    self.display_article_detail(search_result)
                    
        except Exception as e:
            self.logger.error(f"Favori seçim hatası: {e}")
            QMessageBox.critical(self, "Hata", f"Favori açılırken hata oluştu:\n{e}")
    
    def on_recent_search_selected(self, item, column):
        """Son arama seçildiğinde"""
        try:
            query = item.text(0)
            if query:
                # Arama widget'ına sorguyu yükle ve çalıştır
                self.search_widget.set_query(query)
                self.perform_search(query, "mixed")
                
        except Exception as e:
            self.logger.error(f"Son arama seçim hatası: {e}")
    
    def add_to_favorites(self):
        """Aktif maddeyi favorilere ekle"""
        if not hasattr(self, 'current_article_id') or not self.current_article_id:
            QMessageBox.information(self, "Bilgi", "Önce bir madde seçin")
            return
        
        try:
            # Madde bilgilerini al
            cursor = self.db.connection.cursor()
            cursor.execute("""
                SELECT a.title, a.article_number, d.title as document_title
                FROM articles a
                JOIN documents d ON a.document_id = d.id
                WHERE a.id = ?
            """, (self.current_article_id,))
            
            result = cursor.fetchone()
            
            if result:
                title = result[0] or f"Madde {result[1] or ''}"
                document_title = result[2]
                
                # Favorilerde var mı kontrol et
                cursor.execute("""
                    SELECT id FROM favorites WHERE article_id = ?
                """, (self.current_article_id,))
                
                if cursor.fetchone():
                    QMessageBox.information(self, "Bilgi", "Bu madde zaten favorilerinizde")
                    cursor.close()
                    return
                
                # Favoriye ekle
                cursor.execute("""
                    INSERT INTO favorites (article_id, title, created_at)
                    VALUES (?, ?, ?)
                """, (self.current_article_id, f"{title} ({document_title})", datetime.now().isoformat()))
                
                self.db.connection.commit()
                cursor.close()
                
                # Favori listesini güncelle
                self.refresh_favorites()
                
                self.status_bar.showMessage("Favoriye eklendi", 3000)
                
            else:
                cursor.close()
                QMessageBox.warning(self, "Uyarı", "Madde bilgisi bulunamadı")
                
        except Exception as e:
            self.logger.error(f"Favori ekleme hatası: {e}")
            QMessageBox.critical(self, "Hata", f"Favori eklenirken hata oluştu:\n{e}")
    
    def refresh_favorites(self):
        """Favori listesini güncelle"""
        try:
            self.favorites_list.clear()
            
            cursor = self.db.connection.cursor()
            cursor.execute("""
                SELECT f.article_id, f.title, d.title as document_title
                FROM favorites f
                JOIN articles a ON f.article_id = a.id
                JOIN documents d ON a.document_id = d.id
                ORDER BY f.created_at DESC
            """)
            
            for row in cursor.fetchall():
                item = QTreeWidgetItem([row[1], row[2]])
                item.setData(0, Qt.UserRole, row[0])  # article_id'yi sakla
                self.favorites_list.addTopLevelItem(item)
            
            cursor.close()
            
        except Exception as e:
            self.logger.error(f"Favori listesi yenileme hatası: {e}")
    
    def add_note_to_article(self, article_id: int, note: str):
        """Maddeye not ekle"""
        try:
            with self.db.transaction() as cursor:
                cursor.execute("""
                    INSERT INTO user_notes (article_id, content, created_at)
                    VALUES (?, ?, ?)
                """, (article_id, note, datetime.now().isoformat()))
            
            self.logger.info(f"Not eklendi: article_id={article_id}")
            
        except Exception as e:
            self.logger.error(f"Not ekleme hatası: {e}")
            raise
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Drag enter event - dosya sürüklendiğinde"""
        if event.mimeData().hasUrls():
            # Sadece desteklenen dosya türlerini kabul et
            urls = event.mimeData().urls()
            supported_extensions = {'.pdf', '.docx', '.doc', '.txt'}
            
            valid_files = []
            for url in urls:
                if url.isLocalFile():
                    file_path = Path(url.toLocalFile())
                    if file_path.suffix.lower() in supported_extensions:
                        valid_files.append(file_path)
            
            if valid_files:
                event.acceptProposedAction()
                # Visual feedback
                self.status_bar.showMessage(f"{len(valid_files)} desteklenen dosya algılandı")
            else:
                event.ignore()
                self.status_bar.showMessage("Desteklenmeyen dosya türü")
        else:
            event.ignore()
    
    def dragLeaveEvent(self, event):
        """Drag leave event - sürükleme bırakıldığında"""
        self.status_bar.clearMessage()
        event.accept()
    
    def dropEvent(self, event: QDropEvent):
        """Drop event - dosya bırakıldığında"""
        try:
            urls = event.mimeData().urls()
            supported_extensions = {'.pdf', '.docx', '.doc', '.txt'}
            
            valid_files = []
            for url in urls:
                if url.isLocalFile():
                    file_path = Path(url.toLocalFile())
                    if file_path.suffix.lower() in supported_extensions:
                        valid_files.append(str(file_path))
            
            if valid_files:
                event.acceptProposedAction()
                
                # Onay dialog'u göster
                reply = QMessageBox.question(
                    self, "Dosya Ekleme Onayı",
                    f"{len(valid_files)} dosya sisteme eklenecek. Devam edilsin mi?\n\n" + 
                    "\n".join([Path(f).name for f in valid_files[:5]]) + 
                    (f"\n... ve {len(valid_files)-5} dosya daha" if len(valid_files) > 5 else ""),
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # Dosyaları işle
                    self.process_dropped_files(valid_files)
            else:
                event.ignore()
                QMessageBox.information(self, "Bilgi", "Desteklenmeyen dosya türü")
                
        except Exception as e:
            self.logger.error(f"Drop event hatası: {e}")
            QMessageBox.critical(self, "Hata", f"Dosya ekleme sırasında hata oluştu:\n{e}")
    
    def process_dropped_files(self, file_paths: List[str]):
        """Drag & drop ile eklenen dosyaları işle"""
        try:
            # Progress bar göster
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, len(file_paths))
            
            processed_count = 0
            failed_files = []
            
            for i, file_path in enumerate(file_paths):
                self.progress_bar.setValue(i)
                self.status_bar.showMessage(f"İşleniyor: {Path(file_path).name}")
                QApplication.processEvents()  # UI'yı güncelle
                
                try:
                    # Dosyayı doğrudan işle
                    result = self.document_processor.process_file(file_path)
                    
                    if result['success']:
                        processed_count += 1
                        self.logger.info(f"Dosya başarıyla eklendi (D&D): {file_path}")
                    else:
                        failed_files.append(f"{Path(file_path).name}: {result.get('error', 'Bilinmeyen hata')}")
                        self.logger.error(f"Dosya ekleme başarısız (D&D): {file_path} - {result.get('error')}")
                        
                except Exception as e:
                    failed_files.append(f"{Path(file_path).name}: {str(e)}")
                    self.logger.error(f"Dosya işleme exception (D&D): {file_path} - {e}")
            
            # Sonucu göster
            self.progress_bar.setVisible(False)
            
            if failed_files:
                error_msg = f"Drag & Drop işlemi tamamlandı:\n\n" +\
                           f"Başarılı: {processed_count} dosya\n" +\
                           f"Başarısız: {len(failed_files)} dosya\n\n" +\
                           "Başarısız dosyalar:\n" + "\n".join(failed_files[:10])
                if len(failed_files) > 10:
                    error_msg += f"\n... ve {len(failed_files)-10} dosya daha"
                    
                QMessageBox.warning(self, "Belge Ekleme Sonucu", error_msg)
            else:
                QMessageBox.information(
                    self, "Başarılı", 
                    f"Tüm dosyalar başarıyla eklendi! (Drag & Drop)\n\nToplam: {processed_count} dosya"
                )
            
            # UI'yı güncelle
            self.document_tree.refresh_tree()
            self.stats_widget.refresh_stats()
            self.status_bar.showMessage(f"Drag & Drop tamamlandı: {processed_count} başarılı", 5000)
            
        except Exception as e:
            self.progress_bar.setVisible(False)
            self.logger.error(f"Drag & Drop işleme hatası: {e}")
            QMessageBox.critical(self, "Hata", f"Dosya işleme sırasında hata oluştu:\n{e}")
    
    def closeEvent(self, event):
        """Pencere kapatılırken"""
        try:
            # Ayarları kaydet
            if self.config.get('preferences.save_window_position', True):
                # TODO: Save window position and size
                pass
            
            # Temizlik
            if self.file_watcher:
                self.file_watcher.stop_watching()
            
            self.logger.info("Ana pencere kapatıldı")
            event.accept()
            
        except Exception as e:
            self.logger.error(f"Kapatma hatası: {e}")
            event.accept()
    
    def delete_document(self, document_id: int):
        """Belgeyi sil"""
        try:
            # Onay iste
            doc = self.db.get_document(document_id)
            if not doc:
                QMessageBox.warning(self, "Hata", "Belge bulunamadı!")
                return
            
            reply = QMessageBox.question(
                self, "Belgeyi Sil",
                f"'{doc.title}' belgesini silmek istediğinizden emin misiniz?\n\n"
                "Bu işlem geri alınamaz ve belgenin tüm maddeleri ve notları da silinecektir.\n"
                "Belge dosyası da silinsin mi?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Cancel:
                return
                
            delete_file = reply == QMessageBox.Yes
            
            # Silme işlemini gerçekleştir
            result = self.db.delete_document(document_id, delete_physical_file=delete_file)
            if result:
                QMessageBox.information(self, "Başarılı", "Belge başarıyla silindi!")
                
                # UI'yı güncelle
                self.refresh_all()
                self.logger.info(f"Belge silindi: {document_id} - {doc.title}")
            else:
                QMessageBox.critical(self, "Hata", "Belge silinirken hata oluştu!")
                
        except Exception as e:
            self.logger.error(f"Belge silme hatası: {e}")
            QMessageBox.critical(self, "Hata", f"Belge silinirken hata oluştu:\n{e}")
    
    def close_document_tab(self, index: int):
        """Belge sekmesini kapat"""
        try:
            # Varsayılan sekmeleri kapatmaya izin verme (index 0, 1, 2 -> Detay, Belge Görüntüleme, İstatistikler)
            if index < 3:
                return
            
            # Widget'ı al ve temizle
            widget = self.right_panel_tabs.widget(index)
            if widget and isinstance(widget, DocumentViewerWidget):
                document_id = getattr(widget, 'current_document_id', None)
                self.logger.info(f"Belge sekmesi kapatıldı: {document_id}")
                widget.clear_document()
                widget.deleteLater()
            
            # Sekmeyi kaldır
            self.right_panel_tabs.removeTab(index)
            
        except Exception as e:
            self.logger.error(f"Sekme kapatma hatası: {e}")
    
    def view_document(self, document_id: int):
        """Belgeyi yeni sekmede görüntüle"""
        try:
            # Belge bilgilerini al
            document = self.db.get_document(document_id)
            if not document:
                QMessageBox.warning(self, "Hata", f"Belge bulunamadı: ID {document_id}")
                return
            
            # Aynı belge zaten açık mı kontrol et
            for i in range(self.right_panel_tabs.count()):
                tab_widget = self.right_panel_tabs.widget(i)
                if isinstance(tab_widget, DocumentViewerWidget) and hasattr(tab_widget, 'current_document_id'):
                    if tab_widget.current_document_id == document_id:
                        # Aynı belge zaten açık, o sekmeyi aktif et
                        self.right_panel_tabs.setCurrentIndex(i)
                        self.logger.info(f"Belge zaten açık, sekme aktif edildi: {document_id}")
                        return
            
            # Yeni DocumentViewerWidget oluştur
            new_viewer = DocumentViewerWidget(self.config, self.db)
            new_viewer.document_updated.connect(self.refresh_all)
            new_viewer.document_deleted.connect(self.on_document_deleted)
            new_viewer.note_added.connect(self.refresh_all)
            
            # Belgeyi yükle
            if new_viewer.load_document(document_id):
                # Sekme başlığını hazırla
                doc_title = document.get('title', f'Belge #{document_id}')
                if len(doc_title) > 30:
                    doc_title = doc_title[:27] + "..."
                
                # Yeni sekme ekle
                tab_index = self.right_panel_tabs.addTab(new_viewer, f"📄 {doc_title}")
                self.right_panel_tabs.setCurrentIndex(tab_index)
                
                # Tab'a tooltip ekle
                self.right_panel_tabs.setTabToolTip(tab_index, document.get('title', ''))
                
                self.logger.info(f"Belge yeni sekmede açıldı: {document_id}")
            else:
                # Yükleme başarısız olduysa widget'ı temizle
                new_viewer.deleteLater()
                QMessageBox.critical(self, "Hata", "Belge yüklenirken hata oluştu!")
            
        except Exception as e:
            self.logger.error(f"Belge görüntüleme hatası: {e}")
            QMessageBox.critical(self, "Hata", f"Belge görüntülenirken hata oluştu:\n{e}")
    
    def on_document_deleted(self, document_id: int):
        """Belge silindiğinde çağrılır"""
        # UI'yı güncelle
        self.refresh_all()
        self.status_bar.showMessage(f"Belge silindi: ID {document_id}", 3000)
    
    def refresh_all(self):
        """Tüm UI bileşenlerini yenile"""
        try:
            self.document_tree.refresh_tree()
            self.stats_widget.refresh_stats()
            # Arama sonuçlarını yenile (eğer varsa)
            if hasattr(self, 'last_search_query') and self.last_search_query:
                # Son aramayı tekrarla
                pass
        except Exception as e:
            self.logger.error(f"UI yenileme hatası: {e}")
    
    def show_all_documents(self):
        """Tüm belgeleri listele"""
        try:
            # Boş arama yaparak tüm belgeleri getir
            all_results = self.search_engine.search("")
            if all_results:
                self.result_widget.display_results(all_results)
                self.status_bar.showMessage(f"Toplam {len(all_results)} belge listelendi", 3000)
            else:
                QMessageBox.information(self, "Bilgi", "Sistemde belge bulunamadı.")
        except Exception as e:
            self.logger.error(f"Belge listeleme hatası: {e}")
            QMessageBox.critical(self, "Hata", f"Belgeler listelenemedi:\n{e}")
    
    def check_missing_documents(self):
        """Eksik belgeleri kontrol et"""
        try:
            missing_docs = []
            all_docs = self.db.get_all_documents()
            
            for doc in all_docs:
                if doc.file_path and not os.path.exists(doc.file_path):
                    missing_docs.append(doc)
            
            if missing_docs:
                msg = f"Toplam {len(missing_docs)} belgenin dosyası bulunamadı:\n\n"
                for doc in missing_docs[:10]:  # İlk 10 tanesi
                    msg += f"• {doc.title}\n  Dosya: {doc.file_path}\n\n"
                
                if len(missing_docs) > 10:
                    msg += f"... ve {len(missing_docs)-10} belge daha"
                
                reply = QMessageBox.question(
                    self, "Eksik Belgeler", 
                    msg + "\nBu belgeleri veritabanından silmek istiyor musunuz?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    removed_count = 0
                    for doc in missing_docs:
                        if self.db.delete_document(doc.id):
                            removed_count += 1
                    
                    QMessageBox.information(
                        self, "Tamamlandı",
                        f"Toplam {removed_count} eksik belge veritabanından silindi."
                    )
                    self.refresh_all()
            else:
                QMessageBox.information(self, "Tamamlandı", "Tüm belgelerin dosyaları mevcut.")
                
        except Exception as e:
            self.logger.error(f"Eksik belge kontrolü hatası: {e}")
            QMessageBox.critical(self, "Hata", f"Eksik belge kontrolü yapılamadı:\n{e}")
    
    # Modern UI methodları
    def create_modern_left_panel(self) -> QWidget:
        """Modern sol panel - belge ağacı ve filtreler"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(self.design_system.tokens.spacing.md)
        
        # Belge ağacı container'ı
        tree_card = ModernCard("Belgeler")
        self.document_tree = DocumentTreeContainer(self.db)
        self.document_tree.document_selected.connect(self.on_document_selected)
        self.document_tree.document_view_in_new_tab_requested.connect(self.view_document)
        tree_card.set_content(self.document_tree)
        layout.addWidget(tree_card)
        
        # Filtreler kartı
        filter_card = ModernCard("Filtreler")
        filter_panel = QWidget()
        filter_layout = QVBoxLayout(filter_panel)
        filter_layout.setSpacing(self.design_system.tokens.spacing.sm)
        
        # Belge türü filtresi
        type_label = QLabel("Belge Türü:")
        type_label.setStyleSheet(self.design_system.get_text_styles('caption'))
        filter_layout.addWidget(type_label)
        
        self.document_type_combo = QComboBox()
        self.document_type_combo.addItems([
            "Tümü", "ANAYASA", "KANUN", "KHK", "TÜZÜK", 
            "YÖNETMELİK", "YÖNERGE", "TEBLİĞ", "KARAR"
        ])
        self.document_type_combo.setStyleSheet(self.design_system.get_input_styles())
        self.document_type_combo.currentTextChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.document_type_combo)
        
        # Modern checkbox'lar
        self.include_repealed_checkbox = QCheckBox("Mülga maddeleri dahil et")
        self.include_repealed_checkbox.setStyleSheet(self.design_system.get_checkbox_styles())
        self.include_repealed_checkbox.toggled.connect(self.on_filter_changed)
        filter_layout.addWidget(self.include_repealed_checkbox)
        
        self.include_amended_checkbox = QCheckBox("Değişiklik içerenleri göster")
        self.include_amended_checkbox.setChecked(True)
        self.include_amended_checkbox.setStyleSheet(self.design_system.get_checkbox_styles())
        self.include_amended_checkbox.toggled.connect(self.on_filter_changed)
        filter_layout.addWidget(self.include_amended_checkbox)
        
        filter_card.set_content(filter_panel)
        layout.addWidget(filter_card)
        
        return panel
    
    def create_modern_middle_panel(self) -> QWidget:
        """Modern orta panel - arama ve sonuçlar"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(self.design_system.tokens.spacing.md)
        
        # Arama kartı
        search_card = ModernCard("Arama")
        self.search_widget = SearchWidget(self.db, self.search_engine, self.config)
        self.search_widget.search_completed.connect(self.on_search_completed)
        search_card.set_content(self.search_widget)
        layout.addWidget(search_card)
        
        # Sonuçlar kartı
        results_card = ModernCard("Sonuçlar")
        self.result_widget = ResultWidget(self.db)
        self.result_widget.document_selected.connect(self.on_document_selected)
        self.result_widget.document_requested.connect(self.view_document)
        results_card.set_content(self.result_widget)
        layout.addWidget(results_card)
        
        return panel
    
    def create_modern_right_panel(self) -> QWidget:
        """Modern sağ panel - belge detayları ve istatistikler"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(self.design_system.tokens.spacing.md)
        
        # Belge görüntüleyici kartı
        viewer_card = ModernCard("Belge Detayları")
        self.document_viewer = DocumentViewerWidget(self.db)
        viewer_card.set_content(self.document_viewer)
        layout.addWidget(viewer_card)
        
        # İstatistikler kartı
        stats_card = ModernCard("İstatistikler")
        self.stats_widget = StatsWidget(self.db, self.search_engine)
        stats_card.set_content(self.stats_widget)
        layout.addWidget(stats_card)
        
        return panel
    
    def create_modern_toolbar(self):
        """Modern toolbar oluştur"""
        toolbar = self.addToolBar('Ana Araçlar')
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        toolbar.setStyleSheet(self.design_system.get_toolbar_styles())
        
        # Modern butonları oluştur
        add_files_btn = ModernButton(
            "📄 Belge Ekle",
            ButtonType.PRIMARY,
            ButtonSize.MEDIUM
        )
        add_files_btn.setToolTip('Dosya seçerek yeni belge ekle (Ctrl+O)')
        add_files_btn.clicked.connect(self.select_and_process_files)
        toolbar.addWidget(add_files_btn)
        
        scan_btn = ModernButton(
            "🔍 Raw Tara", 
            ButtonType.SECONDARY,
            ButtonSize.MEDIUM
        )
        scan_btn.setToolTip('Raw klasörünü otomatik tara')
        scan_btn.clicked.connect(self.scan_raw_folder)
        toolbar.addWidget(scan_btn)
        
        toolbar.addSeparator()
        
        rebuild_btn = ModernButton(
            "🔄 İndeksi Yenile",
            ButtonType.ACCENT,
            ButtonSize.MEDIUM
        )
        rebuild_btn.setToolTip('Arama indeksini yeniden oluştur')
        rebuild_btn.clicked.connect(self.rebuild_semantic_index)
        toolbar.addWidget(rebuild_btn)
        
        toolbar.addSeparator()
        
        settings_btn = ModernButton(
            "⚙️ Ayarlar",
            ButtonType.TERTIARY,
            ButtonSize.MEDIUM
        )
        settings_btn.clicked.connect(self.open_settings)
        toolbar.addWidget(settings_btn)
        
        # Modern bileşenleri sakla
        self.modern_components.update({
            'toolbar_add_files': add_files_btn,
            'toolbar_scan': scan_btn,
            'toolbar_rebuild': rebuild_btn,
            'toolbar_settings': settings_btn
        })
    
    def create_modern_status_bar(self):
        """Modern status bar oluştur"""
        status_bar = self.statusBar()
        status_bar.setStyleSheet(self.design_system.get_status_bar_styles())
        
        # File watcher status - Modern stil
        self.file_watcher_status = FileWatcherStatus()
        self.file_watcher_status.setStyleSheet(self.design_system.get_text_styles('body2'))
        status_bar.addPermanentWidget(self.file_watcher_status)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(self.design_system.get_progress_bar_styles())
        self.progress_bar.setVisible(False)
        status_bar.addWidget(self.progress_bar)
        
        # Ana durum mesajı
        status_bar.showMessage("Sistem hazır")
    
    def apply_modern_theme(self):
        """Modern tema stillerini uygula"""
        # Ana pencere stili
        main_styles = self.theme_manager.get_main_window_styles()
        self.setStyleSheet(main_styles)
        
        # Responsive davranış başlat
        self.responsive_manager.start_monitoring(self)
