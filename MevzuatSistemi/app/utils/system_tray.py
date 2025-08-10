"""
System Tray Integration - Sistem tepsisi entegrasyonu
"""

import sys
import logging
from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction, QApplication
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap


class SystemTrayManager(QObject):
    """Sistem tepsisi yöneticisi"""
    
    # Sinyaller
    show_requested = pyqtSignal()
    hide_requested = pyqtSignal()
    exit_requested = pyqtSignal()
    search_requested = pyqtSignal(str)
    quick_backup_requested = pyqtSignal()
    
    def __init__(self, config, main_window=None):
        super().__init__()
        
        self.config = config
        self.main_window = main_window
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # System tray kontrolü
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.logger.warning("Sistem tepsisi kullanılamıyor")
            self.system_tray = None
            return
        
        self.system_tray = QSystemTrayIcon()
        self._setup_tray_icon()
        self._setup_context_menu()
        self._connect_signals()
        
        # Tray etkinlik durumu
        self.tray_enabled = self.config.get('ui.system_tray_enabled', True)
        
        if self.tray_enabled:
            self.show_tray_icon()
    
    def _setup_tray_icon(self):
        """Tray ikonu ayarla"""
        if not self.system_tray:
            return
        
        # İkon yolu
        icon_path = Path('resources/icons/mevzuat.png')
        
        if icon_path.exists():
            icon = QIcon(str(icon_path))
        else:
            # Varsayılan ikon oluştur
            icon = self._create_default_icon()
        
        self.system_tray.setIcon(icon)
        self.system_tray.setToolTip("Mevzuat Sistemi")
    
    def _create_default_icon(self) -> QIcon:
        """Varsayılan ikon oluştur"""
        # Basit bir ikon oluştur
        pixmap = QPixmap(16, 16)
        pixmap.fill()
        return QIcon(pixmap)
    
    def _setup_context_menu(self):
        """Sağ tık context menu oluştur"""
        if not self.system_tray:
            return
        
        menu = QMenu()
        
        # Ana pencereyi göster/gizle
        self.show_hide_action = QAction("Göster", self)
        self.show_hide_action.triggered.connect(self._toggle_main_window)
        menu.addAction(self.show_hide_action)
        
        menu.addSeparator()
        
        # Hızlı arama
        quick_search_action = QAction("Hızlı Arama...", self)
        quick_search_action.triggered.connect(self._show_quick_search)
        menu.addAction(quick_search_action)
        
        # Yeni belge ekle
        add_document_action = QAction("Yeni Belge Ekle...", self)
        add_document_action.triggered.connect(self._add_document)
        menu.addAction(add_document_action)
        
        menu.addSeparator()
        
        # Hızlı yedekleme
        backup_action = QAction("Hızlı Yedekleme", self)
        backup_action.triggered.connect(self.quick_backup_requested)
        menu.addAction(backup_action)
        
        # Ayarlar
        settings_action = QAction("Ayarlar", self)
        settings_action.triggered.connect(self._show_settings)
        menu.addAction(settings_action)
        
        menu.addSeparator()
        
        # Çıkış
        exit_action = QAction("Çıkış", self)
        exit_action.triggered.connect(self.exit_requested)
        menu.addAction(exit_action)
        
        self.system_tray.setContextMenu(menu)
    
    def _connect_signals(self):
        """Sinyalleri bağla"""
        if not self.system_tray:
            return
        
        # Double-click ile pencereyi göster/gizle
        self.system_tray.activated.connect(self._on_tray_activated)
        
        # Balloon tip mesajları
        self.system_tray.messageClicked.connect(self._on_message_clicked)
    
    def _on_tray_activated(self, reason):
        """Tray ikonuna tıklandığında"""
        if reason == QSystemTrayIcon.DoubleClick:
            self._toggle_main_window()
        elif reason == QSystemTrayIcon.Trigger:
            # Tek tık - Linux için
            self._toggle_main_window()
    
    def _toggle_main_window(self):
        """Ana pencereyi göster/gizle"""
        if not self.main_window:
            self.show_requested.emit()
            return
        
        if self.main_window.isVisible() and not self.main_window.isMinimized():
            self.main_window.hide()
            self.show_hide_action.setText("Göster")
            self._show_notification("Mevzuat Sistemi", "Sistem tepsisine küçültüldü")
        else:
            self.main_window.show()
            self.main_window.raise_()
            self.main_window.activateWindow()
            self.show_hide_action.setText("Gizle")
    
    def _show_quick_search(self):
        """Hızlı arama dialogunu göster"""
        from PyQt5.QtWidgets import QInputDialog
        
        query, ok = QInputDialog.getText(
            None,
            "Hızlı Arama",
            "Arama terimi:",
            text=""
        )
        
        if ok and query.strip():
            self.search_requested.emit(query.strip())
            # Ana pencereyi göster
            if self.main_window:
                self.main_window.show()
                self.main_window.raise_()
    
    def _add_document(self):
        """Yeni belge ekleme"""
        from PyQt5.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getOpenFileName(
            None,
            "Belge Seç",
            "",
            "Tüm Dosyalar (*.pdf *.docx *.txt);;PDF (*.pdf);;Word (*.docx);;Metin (*.txt)"
        )
        
        if filename:
            # Ana pencereyi göster ve belge ekleme işlemini başlat
            if self.main_window:
                self.main_window.show()
                self.main_window.raise_()
                # Belge ekleme metodunu çağır
                if hasattr(self.main_window, 'add_document_file'):
                    self.main_window.add_document_file(filename)
    
    def _show_settings(self):
        """Ayarlar dialogunu göster"""
        if self.main_window:
            self.main_window.show()
            self.main_window.raise_()
            # Ayarlar metodunu çağır
            if hasattr(self.main_window, 'show_settings'):
                self.main_window.show_settings()
    
    def _on_message_clicked(self):
        """Bildirim mesajına tıklandığında"""
        self._toggle_main_window()
    
    def show_tray_icon(self):
        """Tray ikonunu göster"""
        if self.system_tray:
            self.system_tray.show()
            self.logger.info("System tray ikonu gösterildi")
    
    def hide_tray_icon(self):
        """Tray ikonunu gizle"""
        if self.system_tray:
            self.system_tray.hide()
            self.logger.info("System tray ikonu gizlendi")
    
    def _show_notification(self, title: str, message: str, 
                          icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.Information,
                          timeout: int = 5000):
        """Bildirim göster"""
        if self.system_tray and self.system_tray.supportsMessages():
            self.system_tray.showMessage(title, message, icon, timeout)
    
    def notify_document_processed(self, document_name: str):
        """Belge işlendiği bildirimi"""
        self._show_notification(
            "Belge İşlendi",
            f"'{document_name}' başarıyla sisteme eklendi",
            QSystemTrayIcon.Information
        )
    
    def notify_backup_completed(self, backup_name: str):
        """Yedekleme tamamlandı bildirimi"""
        self._show_notification(
            "Yedekleme Tamamlandı",
            f"'{backup_name}' yedekleme dosyası oluşturuldu",
            QSystemTrayIcon.Information
        )
    
    def notify_error(self, title: str, message: str):
        """Hata bildirimi"""
        self._show_notification(
            title,
            message,
            QSystemTrayIcon.Critical
        )
    
    def is_available(self) -> bool:
        """System tray kullanılabilir mi?"""
        return self.system_tray is not None
    
    def is_enabled(self) -> bool:
        """System tray etkin mi?"""
        return self.tray_enabled and self.is_available()
    
    def set_enabled(self, enabled: bool):
        """System tray'i etkinleştir/devre dışı bırak"""
        self.tray_enabled = enabled
        self.config.set('ui.system_tray_enabled', enabled)
        
        if enabled and self.is_available():
            self.show_tray_icon()
        elif self.is_available():
            self.hide_tray_icon()
    
    def cleanup(self):
        """Temizlik"""
        if self.system_tray:
            self.hide_tray_icon()
            self.system_tray = None
