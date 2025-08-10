#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Belge yönetimi özelliklerini test etmek için test scripti
"""

import sys
import os
import logging
from pathlib import Path

# Proje kök dizinini path'e ekle
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.database_manager import DatabaseManager
from app.core.search_engine import SearchEngine
from app.ui.document_viewer_widget import DocumentViewerWidget
from app.ui.result_widget import ResultWidget
from app.utils.config_manager import ConfigManager

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTabWidget
from PyQt5.QtCore import Qt

class TestMainWindow(QMainWindow):
    """Test ana penceresi"""
    
    def __init__(self):
        super().__init__()
        self.init_components()
        self.init_ui()
        
    def init_components(self):
        """Bileşenleri başlat"""
        # Logger
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Config manager
        self.config = ConfigManager()
        
        # Database
        self.db = DatabaseManager(self.config)
        
        # Search engine
        self.search_engine = SearchEngine(self.config, self.db)
        
    def init_ui(self):
        """UI'yı başlat"""
        self.setWindowTitle("Belge Yönetimi Test - Mevzuat Sistemi")
        self.setGeometry(100, 100, 1200, 800)
        
        # Ana widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # 1. Result Widget sekmesi
        self.result_widget = ResultWidget(self.db)
        self.result_widget.document_delete_requested.connect(self.on_delete_requested)
        self.result_widget.document_view_requested.connect(self.on_view_requested)
        self.tab_widget.addTab(self.result_widget, "Arama Sonuçları")
        
        # 2. Document Viewer sekmesi
        self.document_viewer = DocumentViewerWidget(self.db)
        self.document_viewer.document_updated.connect(self.on_document_updated)
        self.document_viewer.document_deleted.connect(self.on_document_deleted)
        self.tab_widget.addTab(self.document_viewer, "Belge Görüntüleme")
        
        # İlk belgeleri yükle
        self.load_sample_data()
        
    def load_sample_data(self):
        """Örnek veriyi yükle"""
        try:
            # Boş arama yaparak tüm belgeleri getir
            results = self.search_engine.search("")
            if results:
                self.result_widget.display_results(results)
                self.logger.info(f"{len(results)} belge yüklendi")
                
                # İlk belgeyi document viewer'da göster
                if results:
                    first_doc_id = results[0].document_id
                    self.document_viewer.load_document(first_doc_id)
            else:
                self.logger.info("Sistemde belge bulunamadı")
                
        except Exception as e:
            self.logger.error(f"Örnek veri yükleme hatası: {e}")
    
    def on_delete_requested(self, document_id: int):
        """Belge silme talebi"""
        try:
            from PyQt5.QtWidgets import QMessageBox
            
            doc = self.db.get_document(document_id)
            if doc:
                reply = QMessageBox.question(
                    self, "Belgeyi Sil",
                    f"'{doc.title}' belgesini silmek istediğinizden emin misiniz?",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    result = self.db.delete_document(document_id, delete_physical_file=False)
                    if result:
                        QMessageBox.information(self, "Başarılı", "Belge başarıyla silindi!")
                        self.refresh_data()
                    else:
                        QMessageBox.critical(self, "Hata", "Belge silinirken hata oluştu!")
                        
        except Exception as e:
            self.logger.error(f"Belge silme hatası: {e}")
    
    def on_view_requested(self, document_id: int):
        """Belge görüntüleme talebi"""
        try:
            # Document viewer sekmesini aktif et
            for i in range(self.tab_widget.count()):
                if self.tab_widget.tabText(i) == "Belge Görüntüleme":
                    self.tab_widget.setCurrentIndex(i)
                    break
            
            # Belgeyi yükle
            self.document_viewer.load_document(document_id)
            self.logger.info(f"Belge görüntülendi: {document_id}")
            
        except Exception as e:
            self.logger.error(f"Belge görüntüleme hatası: {e}")
    
    def on_document_updated(self, document_id: int):
        """Belge güncellendiğinde"""
        self.logger.info(f"Belge güncellendi: {document_id}")
        self.refresh_data()
    
    def on_document_deleted(self, document_id: int):
        """Belge silindiğinde"""
        self.logger.info(f"Belge silindi: {document_id}")
        self.refresh_data()
    
    def refresh_data(self):
        """Verileri yenile"""
        try:
            # Sonuçları yenile
            results = self.search_engine.search("")
            self.result_widget.display_results(results)
            self.logger.info("Veriler yenilendi")
            
        except Exception as e:
            self.logger.error(f"Veri yenileme hatası: {e}")

def main():
    """Ana fonksiyon"""
    app = QApplication(sys.argv)
    
    # Uygulama ayarları
    app.setApplicationName("Mevzuat Sistemi - Belge Yönetimi Test")
    app.setApplicationVersion("1.0")
    
    # Ana pencere
    window = TestMainWindow()
    window.show()
    
    # Event loop
    return app.exec_()

if __name__ == '__main__':
    sys.exit(main())
