"""
Arama widget'ı - Modern UI ile gelişmiş arama arayüzü
BaseUIWidget'tan türetilmiş ve modern bileşenlerle güncellenmiş implementasyon
"""

import logging
from typing import List, Optional, Dict

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLineEdit, QLabel, QComboBox, 
    QCheckBox, QGroupBox, QSpinBox, QSlider,
    QButtonGroup, QRadioButton, QFrame,
    QCompleter, QTextEdit
)
from PyQt5.QtCore import (
    Qt, pyqtSignal, QTimer, QStringListModel
)
from PyQt5.QtGui import QFont

from ..core.base import BaseUIWidget
from .modern import (
    MevzuatDesignSystem, ModernButton, SmartInput,
    ButtonType, ButtonSize, InputState
)

class AdvancedSearchWidget(BaseUIWidget):
    """Gelişmiş arama widget'ı - Modern UI ile güncellenmiş BaseUIWidget implementasyonu"""
    
    # Signals
    search_requested = pyqtSignal(dict)
    
    def __init__(self, parent=None, config=None):
        """Initialize AdvancedSearchWidget
        
        Args:
            parent: Parent widget
            config: Configuration object
        """
        super().__init__(parent, config)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Modern UI desteği
        self.design_system = MevzuatDesignSystem()
        
        # Initialize UI components
        self._create_widgets()
        self._setup_layouts()
        self._connect_signals()
        self._apply_modern_styles()
    
    def _apply_modern_styles(self):
        """Modern stilleri uygula"""
        self.setStyleSheet(f"""
        AdvancedSearchWidget {{
            background-color: {self.design_system.tokens.surface if self.design_system.tokens else '#FFFFFF'};
            border-radius: 8px;
            padding: 16px;
        }}
        """)
        
    def _create_widgets(self):
        """BaseUIWidget abstract method - create UI widgets"""
        layout = QVBoxLayout(self)
        
        # Başlık
        title_label = QLabel("Gelişmiş Arama")
        title_label.setFont(QFont("", 10, QFont.Bold))
        layout.addWidget(title_label)
        
        # Arama kriterleri
        criteria_layout = QGridLayout()
        
        # Tüm kelimeler
        criteria_layout.addWidget(QLabel("Tüm kelimeler:"), 0, 0)
        self.all_words_edit = QLineEdit()
        criteria_layout.addWidget(self.all_words_edit, 0, 1)
        
        # Tam ifade
        criteria_layout.addWidget(QLabel("Tam ifade:"), 1, 0)
        self.exact_phrase_edit = QLineEdit()
        criteria_layout.addWidget(self.exact_phrase_edit, 1, 1)
        
        # Kelimelerden biri
        criteria_layout.addWidget(QLabel("Kelimelerden biri:"), 2, 0)
        self.any_words_edit = QLineEdit()
        criteria_layout.addWidget(self.any_words_edit, 2, 1)
        
        # Hariç tutulan
        criteria_layout.addWidget(QLabel("Hariç tutulan:"), 3, 0)
        self.exclude_words_edit = QLineEdit()
        criteria_layout.addWidget(self.exclude_words_edit, 3, 1)
        
        layout.addLayout(criteria_layout)
        
        # Filtreler
        filters_group = QGroupBox("Filtreler")
        filters_layout = QVBoxLayout(filters_group)
        
        # Belge türü
        doc_type_layout = QHBoxLayout()
        doc_type_layout.addWidget(QLabel("Belge türü:"))
        self.doc_types = {}
        for doc_type in ["KANUN", "TÜZÜK", "YÖNETMELİK", "TEBLİĞ"]:
            checkbox = QCheckBox(doc_type)
            self.doc_types[doc_type] = checkbox
            doc_type_layout.addWidget(checkbox)
        doc_type_layout.addStretch()
        filters_layout.addLayout(doc_type_layout)
        
        # Tarih aralığı
        # TODO: Tarih seçiciler ekle
        
        layout.addWidget(filters_group)
        
        
        # Create layout and add widgets
        self._setup_layouts()
    
    def _setup_layouts(self):
        """BaseUIWidget abstract method - setup layouts"""
        layout = QVBoxLayout(self)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        search_btn = QPushButton("Gelişmiş Arama")
        search_btn.clicked.connect(self.perform_advanced_search)
        btn_layout.addWidget(search_btn)
        
        clear_btn = QPushButton("Temizle")
        clear_btn.clicked.connect(self.clear_form)
        btn_layout.addWidget(clear_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def _connect_signals(self):
        """BaseUIWidget abstract method - connect signals"""
        pass
    
    def perform_advanced_search(self):
        """Gelişmiş aramayı gerçekleştir"""
        search_params = self.get_search_parameters()
        self.search_requested.emit(search_params)
    
    def get_search_parameters(self) -> dict:
        """Get current search parameters"""
        return {
            'all_words': self.all_words_edit.text() if hasattr(self, 'all_words_edit') else '',
            'exact_phrase': self.exact_phrase_edit.text() if hasattr(self, 'exact_phrase_edit') else '',
            'any_words': self.any_words_edit.text() if hasattr(self, 'any_words_edit') else '',
            'exclude_words': self.exclude_words_edit.text() if hasattr(self, 'exclude_words_edit') else '',
            'document_types': [k for k, v in self.doc_types.items() if v.isChecked()] if hasattr(self, 'doc_types') else []
        }
    
    def clear_form(self):
        """Formu temizle"""
        if hasattr(self, 'all_words_edit'):
            self.all_words_edit.clear()
        if hasattr(self, 'exact_phrase_edit'):
            self.exact_phrase_edit.clear()
        if hasattr(self, 'any_words_edit'):
            self.any_words_edit.clear()
        if hasattr(self, 'exclude_words_edit'):
            self.exclude_words_edit.clear()
        
        if hasattr(self, 'doc_types'):
            for checkbox in self.doc_types.values():
                checkbox.setChecked(False)

class SearchWidget(BaseUIWidget):
    """Ana arama widget'ı"""
    
    search_requested = pyqtSignal(str, str)  # query, search_type
    
    def __init__(self, search_engine, parent=None, config=None):
        super().__init__(parent, config)
        self.search_engine = search_engine
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Son arama bilgileri
        self.last_query = ""
        self.last_search_type = "mixed"
        
        # Suggestion timer
        self.suggestion_timer = QTimer()
        self.suggestion_timer.setSingleShot(True)
        self.suggestion_timer.timeout.connect(self.load_suggestions)
        
        # Otomatik tamamlama
        self.completer_model = QStringListModel()
        
        # BaseUIWidget init_ui zaten çağrıldı, ekstra init_ui çağırmayacağız
    
    def _create_widgets(self):
        """BaseUIWidget abstract method - create UI widgets"""
        # Ana arama grubu
        self.search_group = QGroupBox("Arama")
        
        # Arama kutusu
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Arama terimini girin... (örn: vergi, mülkiyet, TCK madde 123)")
        
        # Otomatik tamamlama ayarla
        completer = QCompleter()
        completer.setModel(self.completer_model)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.search_input.setCompleter(completer)
        
        # Arama butonu
        self.search_btn = QPushButton("Ara")
        self.search_btn.setDefault(True)
        
        # Arama türü radio butonları
        self.search_type_group = QButtonGroup()
        
        self.keyword_radio = QRadioButton("Anahtar kelime")
        self.semantic_radio = QRadioButton("Semantik")
        self.mixed_radio = QRadioButton("Karma (önerilen)")
        self.mixed_radio.setChecked(True)
        
        self.search_type_group.addButton(self.keyword_radio, 0)
        self.search_type_group.addButton(self.semantic_radio, 1)
        self.search_type_group.addButton(self.mixed_radio, 2)
        
        # Benzerlik eşiği
        self.similarity_slider = QSlider(Qt.Horizontal)
        self.similarity_slider.setMinimum(1)
        self.similarity_slider.setMaximum(10)
        self.similarity_slider.setValue(6)
        
        self.similarity_label = QLabel("0.6")
        
        # Max sonuç sayısı
        self.max_results_spin = QSpinBox()
        self.max_results_spin.setRange(10, 1000)
        self.max_results_spin.setValue(50)
        
        # Gelişmiş arama toggle
        self.advanced_toggle_btn = QPushButton("🔽 Gelişmiş Arama")
        
        # Gelişmiş arama widget'ı (lazy loading)
        self.advanced_widget = None
        
        # Öneri grubu
        self.suggestions_group = QGroupBox("Öneriler")
        self.suggestions_group.setVisible(False)
        self.suggestions_layout = QVBoxLayout(self.suggestions_group)
        
        # Hızlı arama butonları
        self.quick_search_group = QGroupBox("Hızlı Arama")
        self.quick_search_layout = QHBoxLayout(self.quick_search_group)
        
        # Popüler arama terimleri
        quick_terms = ["vergi", "mülkiyet", "ceza", "ticaret", "iş hukuku", "sosyal güvenlik"]
        for term in quick_terms:
            btn = QPushButton(term)
            btn.clicked.connect(lambda checked, t=term: self.set_quick_search(t))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f0f0f0;
                    border: 1px solid #ccc;
                    border-radius: 15px;
                    padding: 5px 10px;
                    margin: 2px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
            """)
            self.quick_search_layout.addWidget(btn)
        
        self.quick_search_layout.addStretch()
        
    def _setup_layouts(self):
        """BaseUIWidget abstract method - setup layouts"""
        # Ana layout zaten main_layout olarak oluşturuldu
        
        # Arama grubu layout
        search_layout = QVBoxLayout(self.search_group)
        
        # Arama çubuğu layout
        search_bar_layout = QHBoxLayout()
        search_bar_layout.addWidget(self.search_input)
        search_bar_layout.addWidget(self.search_btn)
        search_layout.addLayout(search_bar_layout)
        
        # Arama türü layout
        search_type_layout = QHBoxLayout()
        search_type_layout.addWidget(QLabel("Arama türü:"))
        search_type_layout.addWidget(self.keyword_radio)
        search_type_layout.addWidget(self.semantic_radio)
        search_type_layout.addWidget(self.mixed_radio)
        search_type_layout.addStretch()
        search_layout.addLayout(search_type_layout)
        
        # Arama seçenekleri layout
        options_layout = QHBoxLayout()
        options_layout.addWidget(QLabel("Benzerlik eşiği:"))
        options_layout.addWidget(self.similarity_slider)
        options_layout.addWidget(self.similarity_label)
        options_layout.addStretch()
        options_layout.addWidget(QLabel("Max sonuç:"))
        options_layout.addWidget(self.max_results_spin)
        search_layout.addLayout(options_layout)
        
        # Gelişmiş arama toggle
        search_layout.addWidget(self.advanced_toggle_btn)
        
        # Ana layout'a ekle
        self.main_layout.addWidget(self.search_group)
        self.main_layout.addWidget(self.suggestions_group)
        self.main_layout.addWidget(self.quick_search_group)
        self.main_layout.addWidget(self.advanced_widget)
        self.main_layout.addStretch()
        
    def _connect_signals(self):
        """BaseUIWidget abstract method - connect signals"""
        self.search_input.returnPressed.connect(self.perform_search)
        self.search_input.textChanged.connect(self.on_text_changed)
        self.search_btn.clicked.connect(self.perform_search)
        self.similarity_slider.valueChanged.connect(self.update_similarity_label)
        self.advanced_toggle_btn.clicked.connect(self.toggle_advanced_search)
        
        if hasattr(self.advanced_widget, 'search_requested'):
            self.advanced_widget.search_requested.connect(self.on_advanced_search)
        
    def init_ui(self):
        """Legacy init_ui method - şimdi BaseUIWidget tarafından yönetiliyor"""
        pass
    
    def on_advanced_search(self, search_params):
        """Gelişmiş aramadan gelen sinyal"""
        # Gelişmiş arama parametrelerini işle
        if search_params.get('all_words'):
            self.search_input.setText(search_params['all_words'])
            self.perform_search()
    
    def perform_search(self):
        """Arama gerçekleştir"""
        query = self.search_input.text().strip()
        if not query:
            return
        
        # Arama türünü belirle
        search_type = "mixed"  # default
        if self.keyword_radio.isChecked():
            search_type = "keyword"
        elif self.semantic_radio.isChecked():
            search_type = "semantic"
        
        # Son arama bilgilerini kaydet
        self.last_query = query
        self.last_search_type = search_type
        
        # Arama sinyalini gönder
        self.search_requested.emit(query, search_type)
        
        # Arama geçmişine ekle
        self.add_to_search_history(query)
        
        self.logger.info(f"Arama yapıldı: '{query}' ({search_type})")
    
    def on_text_changed(self, text):
        """Metin değiştiğinde"""
        # Önerileri yükle (debounce ile)
        self.suggestion_timer.stop()
        if text.strip():
            self.suggestion_timer.start(500)  # 500ms bekle
        else:
            self.suggestions_group.setVisible(False)
        if len(text) > 2:
            self.suggestion_timer.start(500)  # 500ms bekle
        else:
            self.suggestions_group.setVisible(False)
    
    def load_suggestions(self):
        """Önerileri yükle"""
        query = self.search_input.text().strip()
        if len(query) < 3:
            return
        
        try:
            # Arama motorundan önerileri al
            if hasattr(self.search_engine, 'get_suggestions'):
                suggestions = self.search_engine.get_suggestions(query, limit=5)
            else:
                # Basit öneri sistemi - en çok kullanılan kelimeler
                suggestions = self._get_basic_suggestions(query)
            
            if suggestions:
                # Mevcut önerileri temizle
                for i in reversed(range(self.suggestions_layout.count())):
                    item = self.suggestions_layout.itemAt(i)
                    if item and item.widget():
                        item.widget().setParent(None)
                
                # Yeni önerileri ekle
                for suggestion in suggestions:
                    btn = QPushButton(suggestion)
                    btn.clicked.connect(lambda checked, s=suggestion: self.set_suggestion(s))
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #e6f3ff;
                            border: 1px solid #0078d4;
                            border-radius: 3px;
                            padding: 3px 8px;
                            margin: 1px;
                        }
                        QPushButton:hover {
                            background-color: #0078d4;
                            color: white;
                        }
                    """)
                    self.suggestions_layout.addWidget(btn)
                
                self.suggestions_layout.addStretch()
                self.suggestions_group.setVisible(True)
            else:
                self.suggestions_group.setVisible(False)
                
        except Exception as e:
            self.logger.error(f"Öneri yükleme hatası: {e}")
    
    def _get_basic_suggestions(self, query: str) -> List[str]:
        """Basit öneri sistemi"""
        # Sık kullanılan hukuk terimlerinden eşleşenler
        common_terms = [
            "vergi kanunu", "vergi usul kanunu", "gelir vergisi", 
            "katma değer vergisi", "kurumlar vergisi",
            "türk ceza kanunu", "ceza muhakemesi kanunu",
            "türk medeni kanunu", "borçlar kanunu",
            "iş kanunu", "işçi sağlığı", "iş güvenliği",
            "sosyal güvenlik kanunu", "emeklilik",
            "ticaret kanunu", "şirketler kanunu",
            "mülkiyet hukuku", "tapu kanunu"
        ]
        
        query_lower = query.lower()
        matches = []
        
        for term in common_terms:
            if query_lower in term.lower() or term.lower().startswith(query_lower):
                matches.append(term)
                if len(matches) >= 5:
                    break
        
        return matches
    
    def set_suggestion(self, suggestion: str):
        """Öneriyi seç"""
        self.search_input.setText(suggestion)
        self.suggestions_group.setVisible(False)
        self.perform_search()
    
    def set_quick_search(self, term: str):
        """Hızlı arama terimi seç"""
        self.search_input.setText(term)
        self.perform_search()
    
    def toggle_advanced_search(self):
        """Gelişmiş aramayı aç/kapat"""
        is_visible = self.advanced_widget.isVisible()
        self.advanced_widget.setVisible(not is_visible)
        
        if is_visible:
            self.advanced_toggle_btn.setText("🔽 Gelişmiş Arama")
        else:
            self.advanced_toggle_btn.setText("🔼 Gelişmiş Arama")
    
    def update_similarity_label(self, value):
        """Benzerlik etiketini güncelle"""
        similarity = value / 10.0
        self.similarity_label.setText(f"{similarity:.1f}")
    
    def add_to_search_history(self, query: str):
        """Arama geçmişine ekle"""
        try:
            # Otomatik tamamlama için geçmişi güncelle
            current_list = self.completer_model.stringList()
            if query not in current_list:
                current_list.insert(0, query)
                # En fazla 50 sorgu tut
                if len(current_list) > 50:
                    current_list = current_list[:50]
                self.completer_model.setStringList(current_list)
        except Exception as e:
            self.logger.error(f"Arama geçmişi ekleme hatası: {e}")
    
    def get_search_options(self) -> Dict:
        """Arama seçeneklerini al"""
        return {
            'similarity_threshold': self.similarity_slider.value() / 10.0,
            'max_results': self.max_results_spin.value()
        }
    
    def set_search_text(self, text: str):
        """Arama metnini ayarla"""
        self.search_input.setText(text)
    
    def set_query(self, query: str):
        """Arama sorgusunu ayarla"""
        self.search_input.setText(query)
        self.last_query = query
    
    def get_search_text(self) -> str:
        """Arama metnini al"""
        return self.search_input.text().strip()
    
    def focus_search_input(self):
        """Arama kutusuna odaklan"""
        self.search_input.setFocus()
        self.search_input.selectAll()

    def toggle_advanced_search(self):
        """Gelişmiş aramayı aç/kapat"""
        if self.advanced_widget is None:
            # Lazy loading - ilk açılışta oluştur
            self.advanced_widget = AdvancedSearchWidget(self, self.config)
            self.advanced_widget.search_requested.connect(self.on_advanced_search)
            # Ana layout'a ekle
            if hasattr(self, 'main_layout'):
                self.main_layout.insertWidget(3, self.advanced_widget)  # quick_search_group'tan önce
        
        is_visible = self.advanced_widget.isVisible()
        self.advanced_widget.setVisible(not is_visible)
        
        if is_visible:
            self.advanced_toggle_btn.setText("🔽 Gelişmiş Arama")
        else:
            self.advanced_toggle_btn.setText("🔼 Gelişmiş Arama")

    def set_suggestion(self, suggestion: str):
        """Öneriyi seç"""
        self.search_input.setText(suggestion)
        self.suggestions_group.setVisible(False)
        self.perform_search()
    
    def set_quick_search(self, term: str):
        """Hızlı arama terimi seç"""
        self.search_input.setText(term)
        self.perform_search()
