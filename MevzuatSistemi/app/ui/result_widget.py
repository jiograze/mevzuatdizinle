"""
Sonuç görüntüleme widget'ı - arama sonuçlarını gösterir
"""

import logging
from typing import List, Optional
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QTextEdit, QLabel,
    QPushButton, QHeaderView, QAbstractItemView, QMenu,
    QFrame, QSplitter, QTabWidget, QListWidget, QListWidgetItem,
    QGroupBox, QCheckBox, QAction, QMessageBox
)
from PyQt5.QtCore import (
    Qt, pyqtSignal, QSize, QTimer
)
from PyQt5.QtGui import (
    QFont, QColor, QBrush, QIcon, QPixmap, QPainter
)

from ..core.search_engine import SearchResult

class ResultItem(QListWidgetItem):
    """Sonuç listesi item'ı"""
    
    def __init__(self, result: SearchResult):
        super().__init__()
        self.result = result
        
        # Görünümü ayarla
        self.update_display()
    
    def update_display(self):
        """Görünümü güncelle"""
        # Ana başlık
        title = self.result.title or f"{self.result.document_type} - Madde {self.result.article_number}"
        
        # Alt başlık bilgileri
        subtitle_parts = []
        if self.result.document_title:
            subtitle_parts.append(self.result.document_title)
        if self.result.law_number:
            subtitle_parts.append(f"Kanun No: {self.result.law_number}")
        
        subtitle = " | ".join(subtitle_parts)
        
        # Durum göstergeleri
        status_indicators = []
        if self.result.is_repealed:
            status_indicators.append("🚫 MÜLGA")
        elif self.result.is_amended:
            status_indicators.append("📝 DEĞİŞİK")
        
        # Skor gösterimi
        score_text = f"Skor: {self.result.score:.3f}"
        match_type_icon = "🎯" if self.result.match_type == "exact" else "🔍"
        
        # HTML formatında metin oluştur
        display_text = f"""
        <div style="padding: 8px;">
            <div style="font-weight: bold; font-size: 14px; margin-bottom: 4px;">
                {match_type_icon} {title}
            </div>
            <div style="color: #666; font-size: 12px; margin-bottom: 4px;">
                {subtitle}
            </div>
            <div style="color: #333; font-size: 13px; margin-bottom: 6px;">
                {self.result.content[:200]}...
            </div>
            <div style="font-size: 11px; color: #888;">
                <span>{score_text}</span>
                {' | '.join(status_indicators) if status_indicators else ''}
            </div>
        </div>
        """
        
        self.setText(display_text)
        self.setData(Qt.UserRole, self.result)

class ResultTableWidget(QTableWidget):
    """Sonuç tablosu widget'ı"""
    
    result_selected = pyqtSignal(SearchResult)
    document_delete_requested = pyqtSignal(int)  # document_id
    document_view_requested = pyqtSignal(int)    # document_id
    document_view_in_new_tab_requested = pyqtSignal(int)  # document_id for new tab
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.results: List[SearchResult] = []
        
        self.init_ui()
    
    def init_ui(self):
        """UI'yi oluştur"""
        # Sütun başlıkları
        headers = ["Tür", "Başlık", "Belge", "Madde", "Skor", "Durum"]
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        
        # Tablo ayarları
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        
        # Sütun genişlikleri
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Tür
        header.setSectionResizeMode(1, QHeaderView.Stretch)           # Başlık
        header.setSectionResizeMode(2, QHeaderView.Interactive)       # Belge
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Madde
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Skor
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Durum
        
        # Context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        # Seçim değişimi
        self.itemSelectionChanged.connect(self.on_selection_changed)
    
    def display_results(self, results: List[SearchResult]):
        """Sonuçları göster"""
        self.results = results
        
        # Tabloyu temizle
        self.setRowCount(0)
        
        if not results:
            return
        
        # Sonuçları ekle
        self.setRowCount(len(results))
        
        for row, result in enumerate(results):
            try:
                # Tür
                type_item = QTableWidgetItem(result.document_type)
                type_item.setData(Qt.UserRole, result)
                self.setItem(row, 0, type_item)
                
                # Başlık
                title = result.title or f"Madde {result.article_number}"
                title_item = QTableWidgetItem(title)
                self.setItem(row, 1, title_item)
                
                # Belge adı
                doc_title = result.document_title or ""
                if result.law_number:
                    doc_title += f" ({result.law_number})"
                doc_item = QTableWidgetItem(doc_title)
                self.setItem(row, 2, doc_item)
                
                # Madde numarası
                article_item = QTableWidgetItem(str(result.article_number) if result.article_number else "")
                self.setItem(row, 3, article_item)
                
                # Skor
                score_item = QTableWidgetItem(f"{result.score:.3f}")
                self.setItem(row, 4, score_item)
                
                # Durum
                status = ""
                if result.is_repealed:
                    status = "Mülga"
                elif result.is_amended:
                    status = "Değişik"
                else:
                    status = "Aktif"
                
                status_item = QTableWidgetItem(status)
                
                # Renk kodlaması
                if result.is_repealed:
                    status_item.setBackground(QBrush(QColor(255, 200, 200)))  # Kırmızımsı
                elif result.is_amended:
                    status_item.setBackground(QBrush(QColor(255, 255, 200)))  # Sarımsı
                else:
                    status_item.setBackground(QBrush(QColor(200, 255, 200)))  # Yeşilimsi
                
                self.setItem(row, 5, status_item)
                
                # Yüksek skor için vurgulama
                if result.score > 0.8:
                    for col in range(self.columnCount()):
                        item = self.item(row, col)
                        if item:
                            font = item.font()
                            font.setBold(True)
                            item.setFont(font)
            
            except Exception as e:
                self.logger.error(f"Sonuç gösterme hatası (satır {row}): {e}")
                continue
        
        # İlk sonucu seç
        if results:
            self.selectRow(0)
    
    def on_selection_changed(self):
        """Seçim değiştiğinde"""
        current_row = self.currentRow()
        if current_row >= 0 and current_row < len(self.results):
            result = self.results[current_row]
            self.result_selected.emit(result)
    
    def show_context_menu(self, position):
        """Context menu göster"""
        item = self.itemAt(position)
        if not item:
            return
        
        result = self.results[self.currentRow()]
        
        menu = QMenu(self)
        
        # Kopyala
        copy_action = menu.addAction("📋 İçeriği Kopyala")
        copy_action.triggered.connect(lambda: self.copy_result_content(result))
        
        # Favorilere ekle
        favorite_action = menu.addAction("⭐ Favorilere Ekle")
        favorite_action.triggered.connect(lambda: self.add_to_favorites(result))
        
        # Not ekle
        note_action = menu.addAction("📝 Not Ekle")
        note_action.triggered.connect(lambda: self.add_note(result))
        
        menu.addSeparator()
        
        # Detayları göster
        detail_action = menu.addAction("🔍 Detayları Göster")
        detail_action.triggered.connect(lambda: self.show_details(result))
        
        menu.addSeparator()
        
        # Belge görüntüle
        view_action = menu.addAction("📖 Belge Görüntüle")
        view_action.triggered.connect(lambda: self.view_document(result))
        
        # Yeni sekmede aç
        new_tab_action = menu.addAction("📑 Yeni Sekmede Aç")
        new_tab_action.triggered.connect(lambda: self.view_document_in_new_tab(result))
        
        menu.addSeparator()
        
        # Belge sil
        delete_action = menu.addAction("🗑️ Belgeyi Sil")
        delete_action.triggered.connect(lambda: self.delete_document(result))
        
        menu.exec_(self.mapToGlobal(position))
    
    def copy_result_content(self, result: SearchResult):
        """Sonuç içeriğini kopyala"""
        from PyQt5.QtWidgets import QApplication
        
        content = f"""
{result.title or f'Madde {result.article_number}'}
{result.document_title} ({result.law_number})
{result.content}
"""
        QApplication.clipboard().setText(content.strip())
    
    def add_to_favorites(self, result: SearchResult):
        """Favorilere ekle"""
        # TODO: Implement favorites functionality
        pass
    
    def add_note(self, result: SearchResult):
        """Not ekle"""
        # TODO: Implement note functionality
        pass
    
    def show_details(self, result: SearchResult):
        """Detayları göster"""
        self.result_selected.emit(result)
    
    def view_document(self, result: SearchResult):
        """Belgeyi görüntüle"""
        self.document_view_requested.emit(result.document_id)
    
    def view_document_in_new_tab(self, result: SearchResult):
        """Belgeyi yeni sekmede görüntüle"""
        self.document_view_in_new_tab_requested.emit(result.document_id)
    
    def delete_document(self, result: SearchResult):
        """Belgeyi sil"""
        from PyQt5.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self, "Belgeyi Sil",
            f"'{result.document_title}' belgesini silmek istediğinizden emin misiniz?\n\n"
            "Bu işlem geri alınamaz ve belgenin tüm maddeleri ve notları da silinecektir.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.document_delete_requested.emit(result.document_id)

class ResultListWidget(QListWidget):
    """Sonuç liste widget'ı (alternatif görünüm)"""
    
    result_selected = pyqtSignal(SearchResult)
    
    def __init__(self):
        super().__init__()
        self.results: List[SearchResult] = []
        
        self.init_ui()
    
    def init_ui(self):
        """UI'yi oluştur"""
        self.setAlternatingRowColors(True)
        self.itemClicked.connect(self.on_item_clicked)
    
    def display_results(self, results: List[SearchResult]):
        """Sonuçları göster"""
        self.clear()
        self.results = results
        
        for result in results:
            item = ResultItem(result)
            self.addItem(item)
    
    def on_item_clicked(self, item):
        """Item tıklandığında"""
        result = item.data(Qt.UserRole)
        if result:
            self.result_selected.emit(result)

class ResultWidget(QWidget):
    """Ana sonuç widget'ı"""
    
    result_selected = pyqtSignal(SearchResult)
    add_note_requested = pyqtSignal(SearchResult)
    document_delete_requested = pyqtSignal(int)  # Belge silme talebi
    document_view_requested = pyqtSignal(int)    # Belge görüntüleme talebi
    document_view_in_new_tab_requested = pyqtSignal(int)  # Yeni sekmede belge görüntüleme talebi
    
    def __init__(self, db=None):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.current_results: List[SearchResult] = []
        self.db = db
        
        self.init_ui()
    
    def init_ui(self):
        """UI'yi oluştur"""
        layout = QVBoxLayout(self)
        
        # Üst panel - görünüm seçenekleri
        top_panel = QWidget()
        top_layout = QHBoxLayout(top_panel)
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        # Görünüm türü seçimi
        view_label = QLabel("Görünüm:")
        top_layout.addWidget(view_label)
        
        self.table_view_btn = QPushButton("📊 Tablo")
        self.table_view_btn.setCheckable(True)
        self.table_view_btn.setChecked(True)
        self.table_view_btn.clicked.connect(lambda: self.set_view_mode('table'))
        top_layout.addWidget(self.table_view_btn)
        
        self.list_view_btn = QPushButton("📋 Liste")
        self.list_view_btn.setCheckable(True)
        self.list_view_btn.clicked.connect(lambda: self.set_view_mode('list'))
        top_layout.addWidget(self.list_view_btn)
        
        top_layout.addStretch()
        
        # Filtre seçenekleri
        self.show_repealed_cb = QCheckBox("Mülga olanları göster")
        self.show_repealed_cb.setChecked(True)
        self.show_repealed_cb.toggled.connect(self.filter_results)
        top_layout.addWidget(self.show_repealed_cb)
        
        self.show_amended_cb = QCheckBox("Değişiklik olanları göster")
        self.show_amended_cb.setChecked(True)
        self.show_amended_cb.toggled.connect(self.filter_results)
        top_layout.addWidget(self.show_amended_cb)
        
        layout.addWidget(top_panel)
        
        # Ana içerik alanı
        content_frame = QFrame()
        content_frame.setFrameStyle(QFrame.StyledPanel)
        content_layout = QVBoxLayout(content_frame)
        
        # Tablo görünümü
        self.table_widget = ResultTableWidget()
        self.table_widget.result_selected.connect(self.result_selected)
        self.table_widget.document_delete_requested.connect(self.document_delete_requested)
        self.table_widget.document_view_requested.connect(self.document_view_requested)
        self.table_widget.document_view_in_new_tab_requested.connect(self.document_view_in_new_tab_requested)
        content_layout.addWidget(self.table_widget)
        
        # Liste görünümü (başlangıçta gizli)
        self.list_widget = ResultListWidget()
        self.list_widget.result_selected.connect(self.result_selected)
        self.list_widget.setVisible(False)
        content_layout.addWidget(self.list_widget)
        
        layout.addWidget(content_frame)
        
        # Alt panel - istatistikler
        stats_frame = QFrame()
        stats_frame.setFrameStyle(QFrame.StyledPanel)
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setContentsMargins(8, 4, 8, 4)
        
        self.stats_label = QLabel("Sonuç bulunamadı")
        self.stats_label.setStyleSheet("color: #666; font-size: 12px;")
        stats_layout.addWidget(self.stats_label)
        
        stats_layout.addStretch()
        
        # Export butonu
        export_btn = QPushButton("📄 Dışa Aktar")
        export_btn.clicked.connect(self.export_results)
        stats_layout.addWidget(export_btn)
        
        layout.addWidget(stats_frame)
    
    def display_results(self, results: List[SearchResult]):
        """Sonuçları göster"""
        self.current_results = results
        
        # Filtrelenmiş sonuçları al
        filtered_results = self.get_filtered_results()
        
        # Her iki görünümü de güncelle
        self.table_widget.display_results(filtered_results)
        self.list_widget.display_results(filtered_results)
        
        # İstatistikleri güncelle
        self.update_stats(filtered_results)
        
        self.logger.info(f"{len(filtered_results)} sonuç görüntüleniyor")
    
    def get_filtered_results(self) -> List[SearchResult]:
        """Filtrelenmiş sonuçları al"""
        if not self.current_results:
            return []
        
        filtered = []
        
        for result in self.current_results:
            # Mülga filtresi
            if result.is_repealed and not self.show_repealed_cb.isChecked():
                continue
            
            # Değişiklik filtresi  
            if result.is_amended and not self.show_amended_cb.isChecked():
                continue
            
            filtered.append(result)
        
        return filtered
    
    def update_stats(self, results: List[SearchResult]):
        """İstatistikleri güncelle"""
        if not results:
            self.stats_label.setText("Sonuç bulunamadı")
            return
        
        total = len(results)
        
        # Tür dağılımı
        type_counts = {}
        active_count = 0
        repealed_count = 0
        amended_count = 0
        
        for result in results:
            # Tür sayımı
            doc_type = result.document_type
            type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
            
            # Durum sayımı
            if result.is_repealed:
                repealed_count += 1
            elif result.is_amended:
                amended_count += 1
            else:
                active_count += 1
        
        # İstatistik metnini oluştur
        stats_parts = [f"Toplam: {total}"]
        
        if active_count:
            stats_parts.append(f"Aktif: {active_count}")
        if amended_count:
            stats_parts.append(f"Değişik: {amended_count}")
        if repealed_count:
            stats_parts.append(f"Mülga: {repealed_count}")
        
        # En yaygın türü ekle
        if type_counts:
            most_common_type = max(type_counts, key=type_counts.get)
            stats_parts.append(f"En yaygın: {most_common_type} ({type_counts[most_common_type]})")
        
        stats_text = " | ".join(stats_parts)
        self.stats_label.setText(stats_text)
    
    def set_view_mode(self, mode: str):
        """Görünüm modunu ayarla"""
        if mode == 'table':
            self.table_widget.setVisible(True)
            self.list_widget.setVisible(False)
            self.table_view_btn.setChecked(True)
            self.list_view_btn.setChecked(False)
        elif mode == 'list':
            self.table_widget.setVisible(False)
            self.list_widget.setVisible(True)
            self.table_view_btn.setChecked(False)
            self.list_view_btn.setChecked(True)
    
    def filter_results(self):
        """Sonuçları filtrele"""
        filtered_results = self.get_filtered_results()
        
        # Görünümleri güncelle
        self.table_widget.display_results(filtered_results)
        self.list_widget.display_results(filtered_results)
        
        # İstatistikleri güncelle
        self.update_stats(filtered_results)
    
    def export_results(self):
        """Sonuçları dışa aktar"""
        if not self.current_results:
            return
        
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Sonuçları Kaydet",
            f"arama_sonuclari_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt);;CSV Files (*.csv);;All Files (*)"
        )
        
        if filename:
            try:
                self.save_results_to_file(filename)
                QMessageBox.information(self, "Başarılı", f"Sonuçlar {filename} dosyasına kaydedildi")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Dosya kaydetme hatası:\n{e}")
    
    def save_results_to_file(self, filename: str):
        """Sonuçları dosyaya kaydet"""
        filtered_results = self.get_filtered_results()
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"Arama Sonuçları - {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
            f.write("=" * 60 + "\n\n")
            
            for i, result in enumerate(filtered_results, 1):
                f.write(f"{i}. {result.title or f'Madde {result.article_number}'}\n")
                f.write(f"   Belge: {result.document_title}\n")
                if result.law_number:
                    f.write(f"   Kanun No: {result.law_number}\n")
                f.write(f"   Tür: {result.document_type}\n")
                f.write(f"   Skor: {result.score:.3f}\n")
                
                status = "Aktif"
                if result.is_repealed:
                    status = "Mülga"
                elif result.is_amended:
                    status = "Değişik"
                f.write(f"   Durum: {status}\n")
                
                f.write(f"   İçerik: {result.content[:200]}...\n")
                f.write("-" * 40 + "\n\n")
        
        self.logger.info(f"Sonuçlar {filename} dosyasına kaydedildi")
    
    def get_selected_result(self) -> Optional[SearchResult]:
        """Seçili sonucu al"""
        if self.table_widget.isVisible():
            current_row = self.table_widget.currentRow()
            if current_row >= 0 and current_row < len(self.current_results):
                return self.current_results[current_row]
        elif self.list_widget.isVisible():
            current_item = self.list_widget.currentItem()
            if current_item:
                return current_item.data(Qt.UserRole)
        
        return None
    
    def clear_results(self):
        """Sonuçları temizle"""
        self.current_results = []
        self.table_widget.display_results([])
        self.list_widget.display_results([])
        self.stats_label.setText("Sonuç bulunamadı")
