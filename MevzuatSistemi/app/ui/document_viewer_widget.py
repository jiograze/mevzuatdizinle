"""
Belge Görüntüleme Widget'ı - Belgeleri detaylı görüntüler
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, 
    QPushButton, QTabWidget, QTableWidget, QTableWidgetItem,
    QScrollArea, QFrame, QGroupBox, QTextBrowser, QSplitter,
    QHeaderView, QMenu, QAction, QMessageBox, QFileDialog,
    QProgressBar, QComboBox, QCheckBox, QSpinBox, QSlider
)
from PyQt5.QtCore import (
    Qt, pyqtSignal, QThread, QTimer, QUrl
)
from PyQt5.QtGui import (
    QFont, QColor, QPalette, QTextCursor, QTextCharFormat,
    QDesktopServices
)

class DocumentViewerWidget(QWidget):
    """Belge görüntüleme widget'ı"""
    
    # Sinyaller
    document_updated = pyqtSignal(int)  # Belge güncellendiğinde
    document_deleted = pyqtSignal(int)  # Belge silindiğinde
    note_added = pyqtSignal(int, int, str)  # Nota eklendiğinde
    article_selected = pyqtSignal(int)  # Madde seçildiğinde
    
    def __init__(self, config=None, db=None):
        super().__init__()
        
        self.config = config
        self.db = db
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.current_document_id = None
        self.current_document = None
        self.current_articles = []
        
        self.init_ui()
        self.setup_styles()
    
    def init_ui(self):
        """Arayüzü başlat"""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Üst toolbar
        self.create_toolbar()
        layout.addWidget(self.toolbar)
        
        # Ana splitter
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Sol panel - Belge bilgileri ve kontroller
        left_panel = self.create_left_panel()
        main_splitter.addWidget(left_panel)
        
        # Sağ panel - İçerik görüntüleme
        right_panel = self.create_right_panel()
        main_splitter.addWidget(right_panel)
        
        # Splitter oranları
        main_splitter.setSizes([300, 700])
        
        layout.addWidget(main_splitter)
        self.setLayout(layout)
    
    def create_toolbar(self):
        """Üst toolbar oluştur"""
        self.toolbar = QFrame()
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(5, 5, 5, 5)
        
        # Belge işlemleri
        self.edit_button = QPushButton("✏️ Düzenle")
        self.edit_button.clicked.connect(self.edit_document)
        
        self.delete_button = QPushButton("🗑️ Sil")
        self.delete_button.setStyleSheet("QPushButton { color: #d32f2f; }")
        self.delete_button.clicked.connect(self.delete_document)
        
        self.export_button = QPushButton("📄 PDF'e Aktar")
        self.export_button.clicked.connect(self.export_to_pdf)
        
        self.open_file_button = QPushButton("📂 Dosyayı Aç")
        self.open_file_button.clicked.connect(self.open_physical_file)
        
        # Spacer
        toolbar_layout.addWidget(self.edit_button)
        toolbar_layout.addWidget(self.delete_button)
        toolbar_layout.addWidget(self.export_button)
        toolbar_layout.addWidget(self.open_file_button)
        toolbar_layout.addStretch()
        
        # Zoom kontrolleri
        zoom_label = QLabel("Zoom:")
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(50, 200)
        self.zoom_slider.setValue(100)
        self.zoom_slider.valueChanged.connect(self.update_zoom)
        
        self.zoom_label = QLabel("100%")
        self.zoom_label.setMinimumWidth(40)
        
        toolbar_layout.addWidget(zoom_label)
        toolbar_layout.addWidget(self.zoom_slider)
        toolbar_layout.addWidget(self.zoom_label)
        
        self.toolbar.setLayout(toolbar_layout)
    
    def create_left_panel(self):
        """Sol panel oluştur - Belge bilgileri"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Belge bilgileri grubu
        info_group = QGroupBox("Belge Bilgileri")
        info_layout = QVBoxLayout()
        
        self.document_info_widget = QTextBrowser()
        self.document_info_widget.setMaximumHeight(200)
        info_layout.addWidget(self.document_info_widget)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Madde listesi grubu
        articles_group = QGroupBox("Maddeler")
        articles_layout = QVBoxLayout()
        
        # Filtre kontrolleri
        filter_layout = QHBoxLayout()
        
        self.article_filter = QComboBox()
        self.article_filter.addItems(["Tüm Maddeler", "Sadece Normal", "Mülga Maddeler", "Değişiklik Maddeler"])
        self.article_filter.currentTextChanged.connect(self.filter_articles)
        
        filter_layout.addWidget(QLabel("Filtre:"))
        filter_layout.addWidget(self.article_filter)
        
        articles_layout.addLayout(filter_layout)
        
        # Madde listesi
        self.articles_list = QTableWidget()
        self.articles_list.setColumnCount(3)
        self.articles_list.setHorizontalHeaderLabels(["Madde", "Tür", "Durum"])
        
        # Header ayarları
        header = self.articles_list.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        
        self.articles_list.setColumnWidth(0, 80)
        self.articles_list.setColumnWidth(2, 80)
        
        self.articles_list.itemSelectionChanged.connect(self.on_article_selected)
        self.articles_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.articles_list.customContextMenuRequested.connect(self.show_article_context_menu)
        
        articles_layout.addWidget(self.articles_list)
        
        articles_group.setLayout(articles_layout)
        layout.addWidget(articles_group)
        
        panel.setLayout(layout)
        return panel
    
    def create_right_panel(self):
        """Sağ panel oluştur - İçerik görüntüleme"""
        panel = QTabWidget()
        
        # İçerik sekmesi
        content_tab = QWidget()
        content_layout = QVBoxLayout()
        
        # İçerik görüntüleme alanı
        self.content_viewer = QTextBrowser()
        self.content_viewer.setOpenExternalLinks(False)
        self.content_viewer.anchorClicked.connect(self.handle_link_click)
        
        content_layout.addWidget(self.content_viewer)
        content_tab.setLayout(content_layout)
        
        # Madde detayı sekmesi
        article_tab = QWidget()
        article_layout = QVBoxLayout()
        
        # Madde içeriği
        self.article_viewer = QTextBrowser()
        self.article_viewer.setOpenExternalLinks(False)
        
        # Madde notları
        notes_group = QGroupBox("Notlar")
        notes_layout = QVBoxLayout()
        
        self.notes_viewer = QTextEdit()
        self.notes_viewer.setMaximumHeight(100)
        self.notes_viewer.setPlaceholderText("Bu madde için notlarınızı buraya yazın...")
        
        note_buttons = QHBoxLayout()
        self.save_note_button = QPushButton("💾 Notu Kaydet")
        self.save_note_button.clicked.connect(self.save_article_note)
        
        note_buttons.addWidget(self.save_note_button)
        note_buttons.addStretch()
        
        notes_layout.addWidget(self.notes_viewer)
        notes_layout.addLayout(note_buttons)
        notes_group.setLayout(notes_layout)
        
        article_layout.addWidget(self.article_viewer)
        article_layout.addWidget(notes_group)
        
        article_tab.setLayout(article_layout)
        
        # Sekmeleri ekle
        panel.addTab(content_tab, "📄 Tam İçerik")
        panel.addTab(article_tab, "📑 Madde Detayı")
        
        # Sekme değişikliği
        panel.currentChanged.connect(self.on_tab_changed)
        
        return panel
    
    def setup_styles(self):
        """Stil ayarlarını yap"""
        # Ana widget stili
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin: 3px 0px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QTextBrowser {
                border: 1px solid #cccccc;
                border-radius: 3px;
                background-color: white;
            }
            QTableWidget {
                gridline-color: #f0f0f0;
                background-color: white;
                alternate-background-color: #f8f8f8;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
        """)
        
        # Font ayarları
        content_font = QFont("Segoe UI", 11)
        self.content_viewer.setFont(content_font)
        self.article_viewer.setFont(content_font)
    
    def load_document(self, document_id: int):
        """Belgeyi yükle"""
        if not self.db:
            return False
        
        try:
            # Belge bilgilerini al
            document = self.db.get_document(document_id)
            if not document:
                QMessageBox.warning(self, "Hata", f"Belge bulunamadı: ID {document_id}")
                return False
            
            self.current_document_id = document_id
            self.current_document = document
            
            # Belge bilgilerini göster
            self.display_document_info(document)
            
            # Makaleleri yükle
            self.load_articles(document_id)
            
            # İçeriği yükle
            self.load_document_content()
            
            # Toolbar durumunu güncelle
            self.update_toolbar_state()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Belge yükleme hatası: {e}")
            QMessageBox.critical(self, "Hata", f"Belge yüklenirken hata oluştu:\n{e}")
            return False
    
    def display_document_info(self, document: Dict[str, Any]):
        """Belge bilgilerini göster"""
        html_content = f"""
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 10px; }}
            .header {{ color: #2c3e50; font-size: 14px; font-weight: bold; margin-bottom: 10px; }}
            .info-row {{ margin: 5px 0; }}
            .label {{ font-weight: bold; color: #34495e; }}
            .value {{ color: #2c3e50; }}
            .status {{ padding: 2px 6px; border-radius: 3px; font-size: 11px; }}
            .active {{ background-color: #d4edda; color: #155724; }}
            .repealed {{ background-color: #f8d7da; color: #721c24; }}
        </style>
        
        <div class="header">{document.get('title', 'Başlıksız Belge')}</div>
        
        <div class="info-row">
            <span class="label">Tür:</span> 
            <span class="value">{document.get('document_type', 'Bilinmiyor')}</span>
        </div>
        
        <div class="info-row">
            <span class="label">Numara:</span> 
            <span class="value">{document.get('law_number', 'Yok')}</span>
        </div>
        
        <div class="info-row">
            <span class="label">Durum:</span> 
            <span class="status {'active' if document.get('status') == 'active' else 'repealed'}">
                {'Yürürlükte' if document.get('status') == 'active' else 'Mülga'}
            </span>
        </div>
        
        <div class="info-row">
            <span class="label">Tarih:</span> 
            <span class="value">{document.get('publish_date', 'Bilinmiyor')}</span>
        </div>
        
        <div class="info-row">
            <span class="label">Dosya:</span> 
            <span class="value">{Path(document.get('file_path', '')).name if document.get('file_path') else 'Yok'}</span>
        </div>
        
        <div class="info-row">
            <span class="label">Boyut:</span> 
            <span class="value">{self.format_file_size(document.get('file_size', 0))}</span>
        </div>
        """
        
        self.document_info_widget.setHtml(html_content)
    
    def load_articles(self, document_id: int):
        """Makaleleri yükle"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("""
                SELECT id, article_number, article_type, is_repealed, is_amended, content_clean
                FROM articles 
                WHERE document_id = ? 
                ORDER BY CAST(article_number AS INTEGER), seq_index
            """, (document_id,))
            
            self.current_articles = []
            for row in cursor.fetchall():
                article = {
                    'id': row[0],
                    'number': row[1],
                    'type': row[2] or 'madde',
                    'is_repealed': bool(row[3]),
                    'is_amended': bool(row[4]),
                    'content': row[5] or ''
                }
                self.current_articles.append(article)
            
            cursor.close()
            
            # Tabloyu güncelle
            self.update_articles_table()
            
        except Exception as e:
            self.logger.error(f"Madde yükleme hatası: {e}")
    
    def update_articles_table(self):
        """Madde tablosunu güncelle"""
        # Filtreyi uygula
        filtered_articles = self.apply_article_filter()
        
        self.articles_list.setRowCount(len(filtered_articles))
        
        for row, article in enumerate(filtered_articles):
            # Madde numarası
            number_item = QTableWidgetItem(str(article['number']))
            number_item.setData(Qt.UserRole, article['id'])
            self.articles_list.setItem(row, 0, number_item)
            
            # Madde türü
            type_item = QTableWidgetItem(article['type'].title())
            self.articles_list.setItem(row, 1, type_item)
            
            # Durum
            status_text = ""
            if article['is_repealed']:
                status_text = "Mülga"
                number_item.setForeground(QColor("#d32f2f"))
            elif article['is_amended']:
                status_text = "Değişik"
                number_item.setForeground(QColor("#f57c00"))
            else:
                status_text = "Normal"
                number_item.setForeground(QColor("#388e3c"))
            
            status_item = QTableWidgetItem(status_text)
            self.articles_list.setItem(row, 2, status_item)
    
    def apply_article_filter(self) -> List[Dict]:
        """Madde filtresini uygula"""
        filter_text = self.article_filter.currentText()
        
        if filter_text == "Tüm Maddeler":
            return self.current_articles
        elif filter_text == "Sadece Normal":
            return [a for a in self.current_articles if not a['is_repealed'] and not a['is_amended']]
        elif filter_text == "Mülga Maddeler":
            return [a for a in self.current_articles if a['is_repealed']]
        elif filter_text == "Değişiklik Maddeler":
            return [a for a in self.current_articles if a['is_amended']]
        else:
            return self.current_articles
    
    def load_document_content(self):
        """Belge içeriğini yükle"""
        if not self.current_document:
            return
        
        try:
            # Tam metin içeriğini oluştur
            html_content = f"""
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; margin: 20px; }}
                h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
                h2 {{ color: #34495e; margin-top: 30px; }}
                .article {{ margin: 20px 0; padding: 15px; border-left: 3px solid #3498db; background-color: #f8f9fa; }}
                .article-number {{ font-weight: bold; color: #2980b9; }}
                .article-content {{ margin-top: 10px; }}
                .repealed {{ opacity: 0.6; text-decoration: line-through; }}
                .amended {{ background-color: #fff3cd; border-left-color: #ffc107; }}
            </style>
            
            <h1>{self.current_document.get('title', 'Başlıksız Belge')}</h1>
            """
            
            # Makaleleri ekle
            for article in self.current_articles:
                css_class = "article"
                if article['is_repealed']:
                    css_class += " repealed"
                elif article['is_amended']:
                    css_class += " amended"
                
                html_content += f"""
                <div class="{css_class}" id="article-{article['id']}">
                    <div class="article-number">Madde {article['number']}</div>
                    <div class="article-content">{article['content']}</div>
                </div>
                """
            
            self.content_viewer.setHtml(html_content)
            
        except Exception as e:
            self.logger.error(f"İçerik yükleme hatası: {e}")
    
    def filter_articles(self):
        """Madde filtresini uygula"""
        self.update_articles_table()
    
    def on_article_selected(self):
        """Madde seçildiğinde"""
        current_row = self.articles_list.currentRow()
        if current_row >= 0:
            item = self.articles_list.item(current_row, 0)
            if item:
                article_id = item.data(Qt.UserRole)
                self.load_article_detail(article_id)
                
                # Sinyal gönder
                self.article_selected.emit(article_id)
    
    def load_article_detail(self, article_id: int):
        """Madde detayını yükle"""
        try:
            # Maddeyi bul
            article = None
            for a in self.current_articles:
                if a['id'] == article_id:
                    article = a
                    break
            
            if not article:
                return
            
            # Madde içeriğini göster
            html_content = f"""
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; margin: 15px; }}
                .article-header {{ background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin-bottom: 15px; }}
                .article-number {{ font-size: 18px; font-weight: bold; color: #2980b9; }}
                .article-type {{ color: #7f8c8d; font-style: italic; }}
                .article-content {{ font-size: 14px; line-height: 1.7; }}
                .status-badge {{ padding: 3px 8px; border-radius: 12px; font-size: 11px; }}
                .normal {{ background-color: #d4edda; color: #155724; }}
                .repealed {{ background-color: #f8d7da; color: #721c24; }}
                .amended {{ background-color: #fff3cd; color: #856404; }}
            </style>
            
            <div class="article-header">
                <div class="article-number">Madde {article['number']}</div>
                <div class="article-type">{article['type'].title()}</div>
                <span class="status-badge {'normal' if not article['is_repealed'] and not article['is_amended'] else 'repealed' if article['is_repealed'] else 'amended'}">
                    {'Normal' if not article['is_repealed'] and not article['is_amended'] else 'Mülga' if article['is_repealed'] else 'Değişik'}
                </span>
            </div>
            
            <div class="article-content">
                {article['content']}
            </div>
            """
            
            self.article_viewer.setHtml(html_content)
            
            # Madde notlarını yükle
            self.load_article_notes(article_id)
            
        except Exception as e:
            self.logger.error(f"Madde detayı yükleme hatası: {e}")
    
    def load_article_notes(self, article_id: int):
        """Madde notlarını yükle"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("""
                SELECT note FROM user_notes 
                WHERE article_id = ? 
                ORDER BY created_at DESC 
                LIMIT 1
            """, (article_id,))
            
            row = cursor.fetchone()
            if row:
                self.notes_viewer.setPlainText(row[0])
            else:
                self.notes_viewer.clear()
            
            cursor.close()
            
        except Exception as e:
            self.logger.error(f"Not yükleme hatası: {e}")
    
    def save_article_note(self):
        """Madde notunu kaydet"""
        current_row = self.articles_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce bir madde seçin")
            return
        
        item = self.articles_list.item(current_row, 0)
        article_id = item.data(Qt.UserRole)
        note_text = self.notes_viewer.toPlainText().strip()
        
        if not note_text:
            QMessageBox.warning(self, "Uyarı", "Not metni boş olamaz")
            return
        
        try:
            # Mevcut notu kontrol et
            cursor = self.db.connection.cursor()
            cursor.execute("SELECT id FROM user_notes WHERE article_id = ?", (article_id,))
            existing = cursor.fetchone()
            
            if existing:
                # Güncelle
                cursor.execute("""
                    UPDATE user_notes 
                    SET note = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE article_id = ?
                """, (note_text, article_id))
            else:
                # Yeni ekle
                cursor.execute("""
                    INSERT INTO user_notes (article_id, note, created_at, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (article_id, note_text))
            
            self.db.connection.commit()
            cursor.close()
            
            QMessageBox.information(self, "Başarılı", "Not kaydedildi")
            
            # Sinyal gönder
            self.note_added.emit(self.current_document_id, article_id, note_text)
            
        except Exception as e:
            self.logger.error(f"Not kaydetme hatası: {e}")
            QMessageBox.critical(self, "Hata", f"Not kaydedilemedi:\n{e}")
    
    def show_article_context_menu(self, position):
        """Madde context menüsü"""
        if self.articles_list.itemAt(position):
            menu = QMenu(self)
            
            view_action = QAction("Görüntüle", self)
            view_action.triggered.connect(self.on_article_selected)
            menu.addAction(view_action)
            
            menu.addSeparator()
            
            copy_action = QAction("Metni Kopyala", self)
            copy_action.triggered.connect(self.copy_article_text)
            menu.addAction(copy_action)
            
            menu.exec_(self.articles_list.mapToGlobal(position))
    
    def copy_article_text(self):
        """Madde metnini kopyala"""
        current_row = self.articles_list.currentRow()
        if current_row >= 0:
            item = self.articles_list.item(current_row, 0)
            article_id = item.data(Qt.UserRole)
            
            # Maddeyi bul
            for article in self.current_articles:
                if article['id'] == article_id:
                    from PyQt5.QtWidgets import QApplication
                    clipboard = QApplication.clipboard()
                    clipboard.setText(article['content'])
                    QMessageBox.information(self, "Kopyalandı", "Madde metni panoya kopyalandı")
                    break
    
    def on_tab_changed(self, index):
        """Sekme değiştirildiğinde"""
        if index == 1:  # Madde detayı sekmesi
            self.on_article_selected()  # Seçili maddeyi yeniden yükle
    
    def edit_document(self):
        """Belgeyi düzenle"""
        if not self.current_document_id:
            return
        
        QMessageBox.information(self, "Bilgi", "Belge düzenleme özelliği yakında eklenecek")
    
    def delete_document(self):
        """Belgeyi sil"""
        if not self.current_document_id:
            return
        
        # Onay al
        reply = QMessageBox.question(
            self, "Belgeyi Sil", 
            f"'{self.current_document.get('title', 'Bu belge')}' kalıcı olarak silinecek.\n\n"
            "Bu işlem geri alınamaz!\n\nDevam etmek istiyor musunuz?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Fiziksel dosya seçeneği
        delete_file_reply = QMessageBox.question(
            self, "Fiziksel Dosya", 
            "Fiziksel dosya da silinsin mi?\n\n"
            "(Hayır seçerseniz sadece veritabanından kaldırılacak)",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        delete_physical = delete_file_reply == QMessageBox.Yes
        
        try:
            # Belgeyi sil
            success = self.db.delete_document(self.current_document_id, delete_physical)
            
            if success:
                QMessageBox.information(self, "Başarılı", "Belge başarıyla silindi")
                
                # Sinyal gönder
                self.document_deleted.emit(self.current_document_id)
                
                # Widget'ı temizle
                self.clear_document()
            else:
                QMessageBox.critical(self, "Hata", "Belge silinemedi")
                
        except Exception as e:
            self.logger.error(f"Belge silme hatası: {e}")
            QMessageBox.critical(self, "Hata", f"Belge silinirken hata oluştu:\n{e}")
    
    def export_to_pdf(self):
        """PDF'e aktar"""
        if not self.current_document_id:
            return
        
        # Dosya yolu seç
        filename, _ = QFileDialog.getSaveFileName(
            self, "PDF Olarak Kaydet", 
            f"{self.current_document.get('title', 'belge')}.pdf",
            "PDF Files (*.pdf)"
        )
        
        if filename:
            QMessageBox.information(self, "Bilgi", "PDF export özelliği yakında eklenecek")
    
    def open_physical_file(self):
        """Fiziksel dosyayı aç"""
        if not self.current_document or not self.current_document.get('file_path'):
            QMessageBox.warning(self, "Uyarı", "Dosya yolu bulunamadı")
            return
        
        file_path = self.current_document['file_path']
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "Uyarı", f"Dosya bulunamadı:\n{file_path}")
            return
        
        try:
            # Dosyayı sistem varsayılan uygulamasıyla aç
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
        except Exception as e:
            self.logger.error(f"Dosya açma hatası: {e}")
            QMessageBox.critical(self, "Hata", f"Dosya açılamadı:\n{e}")
    
    def update_zoom(self, value):
        """Zoom seviyesini güncelle"""
        self.zoom_label.setText(f"{value}%")
        
        # Font boyutunu ayarla
        base_size = 11
        new_size = int(base_size * (value / 100))
        
        font = self.content_viewer.font()
        font.setPointSize(new_size)
        self.content_viewer.setFont(font)
        self.article_viewer.setFont(font)
    
    def handle_link_click(self, url):
        """Link tıklandığında"""
        url_str = url.toString()
        
        # Madde linklerini işle
        if url_str.startswith("#article-"):
            article_id = int(url_str.replace("#article-", ""))
            
            # Maddeyi tabloda seç
            for row in range(self.articles_list.rowCount()):
                item = self.articles_list.item(row, 0)
                if item and item.data(Qt.UserRole) == article_id:
                    self.articles_list.selectRow(row)
                    break
    
    def update_toolbar_state(self):
        """Toolbar durumunu güncelle"""
        has_document = self.current_document_id is not None
        
        self.edit_button.setEnabled(has_document)
        self.delete_button.setEnabled(has_document)
        self.export_button.setEnabled(has_document)
        self.open_file_button.setEnabled(
            has_document and 
            self.current_document and 
            self.current_document.get('file_path') and
            os.path.exists(self.current_document.get('file_path', ''))
        )
    
    def clear_document(self):
        """Belgeyi temizle"""
        self.current_document_id = None
        self.current_document = None
        self.current_articles = []
        
        self.document_info_widget.clear()
        self.content_viewer.clear()
        self.article_viewer.clear()
        self.notes_viewer.clear()
        
        self.articles_list.setRowCount(0)
        
        self.update_toolbar_state()
    
    def format_file_size(self, size_bytes: int) -> str:
        """Dosya boyutunu formatla"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        size = float(size_bytes)
        
        while size >= 1024.0 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        
        return f"{size:.1f} {size_names[i]}"
