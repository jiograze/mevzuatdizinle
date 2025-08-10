"""
Faceted Search Widget - Çok boyutlu arama filtreleri
"""

import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QGroupBox, QScrollArea, QFrame, QPushButton, QSplitter,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QLineEdit,
    QComboBox, QSlider, QSpinBox, QButtonGroup, QRadioButton
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPalette

from typing import Dict, List, Any, Optional
from app.utils.faceted_search import Facet, FacetOption, FacetedResults
from app.core.base import BaseUIWidget

class FacetCheckBox(QCheckBox):
    """Facet seçeneği için özel checkbox"""
    
    def __init__(self, facet_option: FacetOption, parent=None):
        super().__init__(parent)
        self.facet_option = facet_option
        self.setText(f"{facet_option.label} ({facet_option.count})")
        self.setChecked(facet_option.selected)

class FacetGroupBox(QGroupBox):
    """Facet grubu için özel group box"""
    
    facetChanged = pyqtSignal(str, list)  # facet_name, selected_values
    
    def __init__(self, facet: Facet, parent=None):
        super().__init__(facet.label, parent)
        self.facet = facet
        self.checkboxes = []
        self.setup_ui()
        
    def setup_ui(self):
        """UI'ı kur"""
        layout = QVBoxLayout()
        
        # Facet seçenekleri için scroll area
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        # Seçenekleri ekle
        for option in self.facet.options:
            checkbox = FacetCheckBox(option)
            checkbox.stateChanged.connect(self.on_selection_changed)
            self.checkboxes.append(checkbox)
            scroll_layout.addWidget(checkbox)
        
        # Boş alan ekle
        scroll_layout.addStretch()
        
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(200)
        
        layout.addWidget(scroll)
        
        # Tümünü seç/temizle butonları
        button_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("Tümünü Seç")
        select_all_btn.setMaximumWidth(80)
        select_all_btn.clicked.connect(self.select_all)
        
        clear_all_btn = QPushButton("Temizle")
        clear_all_btn.setMaximumWidth(60)
        clear_all_btn.clicked.connect(self.clear_all)
        
        button_layout.addWidget(select_all_btn)
        button_layout.addWidget(clear_all_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def on_selection_changed(self):
        """Seçim değiştiğinde çağrılır"""
        selected_values = []
        for checkbox in self.checkboxes:
            if checkbox.isChecked():
                selected_values.append(checkbox.facet_option.value)
        
        self.facetChanged.emit(self.facet.name, selected_values)
    
    def select_all(self):
        """Tümünü seç"""
        for checkbox in self.checkboxes:
            checkbox.setChecked(True)
    
    def clear_all(self):
        """Tümünü temizle"""
        for checkbox in self.checkboxes:
            checkbox.setChecked(False)
    
    def update_facet(self, facet: Facet):
        """Facet verilerini güncelle"""
        self.facet = facet
        
        # Mevcut checkbox'ları temizle
        for checkbox in self.checkboxes:
            checkbox.deleteLater()
        self.checkboxes.clear()
        
        # Yeniden oluştur
        self.setup_ui()

class FacetWidget(QWidget):
    """Faceted search ana widget"""
    
    filtersChanged = pyqtSignal(dict)  # selected_facets dictionary
    clearFilters = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.facet_groups = {}  # facet_name -> FacetGroupBox
        self.selected_facets = {}  # facet_name -> [selected_values]
        self.setup_ui()
    
    def setup_ui(self):
        """UI'ı kur"""
        layout = QVBoxLayout()
        
        # Başlık
        title_label = QLabel("Arama Filtreleri")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Filtre temizleme butonu
        clear_btn = QPushButton("Tüm Filtreleri Temizle")
        clear_btn.clicked.connect(self.clear_all_filters)
        layout.addWidget(clear_btn)
        
        # Ayıraç
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # Facet grupları için scroll area
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout()
        
        self.scroll_widget.setLayout(self.scroll_layout)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        
        layout.addWidget(self.scroll_area)
        
        # Boş alan
        layout.addStretch()
        
        self.setLayout(layout)
        self.setMinimumWidth(250)
        self.setMaximumWidth(350)
    
    def update_facets(self, facets: List[Facet]):
        """Facetleri güncelle"""
        try:
            # Mevcut facet gruplarını temizle
            for group in self.facet_groups.values():
                group.deleteLater()
            self.facet_groups.clear()
            
            # Yeni facetleri ekle
            for facet in facets:
                group_box = FacetGroupBox(facet)
                group_box.facetChanged.connect(self.on_facet_changed)
                
                self.facet_groups[facet.name] = group_box
                self.scroll_layout.addWidget(group_box)
            
            # Boş alan ekle
            self.scroll_layout.addStretch()
            
        except Exception as e:
            self.logger.error(f"Facet güncelleme hatası: {e}")
    
    def on_facet_changed(self, facet_name: str, selected_values: List[str]):
        """Facet seçimi değiştiğinde çağrılır"""
        if selected_values:
            self.selected_facets[facet_name] = selected_values
        else:
            self.selected_facets.pop(facet_name, None)
        
        self.filtersChanged.emit(self.selected_facets.copy())
    
    def clear_all_filters(self):
        """Tüm filtreleri temizle"""
        for group in self.facet_groups.values():
            group.clear_all()
        
        self.selected_facets.clear()
        self.clearFilters.emit()
    
    def get_selected_facets(self) -> Dict[str, List[str]]:
        """Seçili facetleri döndür"""
        return self.selected_facets.copy()
    
    def set_selected_facets(self, facets: Dict[str, List[str]]):
        """Facet seçimlerini ayarla (URL'den gelen veriler için)"""
        self.selected_facets = facets.copy()
        
        # UI'ı güncelle
        for facet_name, selected_values in facets.items():
            if facet_name in self.facet_groups:
                group = self.facet_groups[facet_name]
                for checkbox in group.checkboxes:
                    checkbox.setChecked(
                        checkbox.facet_option.value in selected_values
                    )

class FacetedSearchWidget(BaseUIWidget):
    """Faceted search ana bileşeni - BaseUIWidget implementasyonu"""
    
    searchRequested = pyqtSignal(str, dict)  # query, facet_filters
    
    def __init__(self, parent=None, config=None):
        # Store references before calling super
        self.current_results: Optional[FacetedResults] = None
        self.facet_widget = None
        self.results_widget = None
        self.results_summary = None
        
        super().__init__(parent, config)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _create_widgets(self):
        """BaseUIWidget abstract method - create UI widgets"""
        # Sol panel - Facet filtreleri
        self.facet_widget = FacetWidget()
        
        # Sağ panel - Sonuçlar
        self.results_widget = QWidget()
        
        # Sonuç özeti
        self.results_summary = QLabel("Arama sonuçları burada gösterilecek")
    
    def _setup_layouts(self):
        """BaseUIWidget abstract method - setup layouts"""
        # Ana splitter
        splitter = QSplitter(Qt.Horizontal)
        
        splitter.addWidget(self.facet_widget)
        
        # Results widget layout
        results_layout = QVBoxLayout()
        results_layout.addWidget(self.results_summary)
        self.results_widget.setLayout(results_layout)
        
        splitter.addWidget(self.results_widget)
        
        # Splitter boyutları
        splitter.setSizes([300, 700])
        
        self.main_layout.addWidget(splitter)
    
    def _connect_signals(self):
        """BaseUIWidget abstract method - connect signals"""
        if self.facet_widget:
            self.facet_widget.filtersChanged.connect(self.on_filters_changed)
            self.facet_widget.clearFilters.connect(self.on_clear_filters)
    
    def update_results(self, results: FacetedResults, query: str = ""):
        """Arama sonuçlarını güncelle"""
        try:
            self.current_results = results
            
            # Facetleri güncelle
            if self.facet_widget:
                self.facet_widget.update_facets(results.facets)
            
            # Sonuç özetini güncelle
            if self.results_summary:
                summary_text = f"Toplam: {results.total_count}, Filtrelenmiş: {results.filtered_count}"
                if query:
                    summary_text += f" ('{query}' için)"
                self.results_summary.setText(summary_text)
            
            self.logger.debug(f"Results updated: {results.filtered_count}/{results.total_count}")
            
        except Exception as e:
            error_msg = self.error_handler.handle_error(e, "update_results")
            self.logger.error(error_msg)
    
    def on_filters_changed(self, selected_facets: Dict[str, List[str]]):
        """Filtreler değiştiğinde çağrılır"""
        try:
            self.logger.debug(f"Filters changed: {selected_facets}")
            self.searchRequested.emit("", selected_facets)
            
        except Exception as e:
            error_msg = self.error_handler.handle_error(e, "on_filters_changed")
            self.logger.error(error_msg)
    
    def on_clear_filters(self):
        """Filtreler temizlendiğinde çağrılır"""
        try:
            self.logger.debug("All filters cleared")
            self.searchRequested.emit("", {})
            
        except Exception as e:
            error_msg = self.error_handler.handle_error(e, "on_clear_filters")
            self.logger.error(error_msg)
    
    def get_results_widget(self) -> QWidget:
        """Sonuçlar için widget'ı döndür (dışarıdan doldurulmak için)"""
        return self.results_widget if self.results_widget else QWidget()
    
    def export_state(self) -> Dict[str, Any]:
        """Widget durumunu export et"""
        try:
            if self.current_results and self.facet_widget:
                return {
                    'selected_facets': self.facet_widget.get_selected_facets(),
                    'total_count': self.current_results.total_count,
                    'filtered_count': self.current_results.filtered_count
                }
        except Exception as e:
            error_msg = self.error_handler.handle_error(e, "export_state")
            self.logger.error(error_msg)
        
        return {}
    
    def import_state(self, state: Dict[str, Any]):
        """Widget durumunu import et"""
        try:
            selected_facets = state.get('selected_facets', {})
            if selected_facets and self.facet_widget:
                self.facet_widget.set_selected_facets(selected_facets)
                
        except Exception as e:
            error_msg = self.error_handler.handle_error(e, "import_state")
            self.logger.error(error_msg)
