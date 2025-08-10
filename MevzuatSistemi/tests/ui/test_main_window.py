#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Ana pencere UI testleri
"""

import pytest
from unittest.mock import Mock, MagicMock
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parents[2]))

# PyQt5 testleri için
pytest_plugins = ["pytestqt"]

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest

from app.ui.main_window import MainWindow
from app.ui.search_widget import SearchWidget
from app.ui.result_widget import ResultWidget


@pytest.mark.ui
class TestMainWindow:
    """Ana pencere UI testleri"""
    
    @pytest.fixture
    def mock_components(self):
        """Mock bileşenler"""
        components = {
            'config': MagicMock(),
            'db': MagicMock(),
            'search_engine': MagicMock(),
            'document_processor': MagicMock(),
            'file_watcher': MagicMock()
        }
        
        # Mock return değerleri
        components['config'].get.return_value = "test_value"
        components['search_engine'].search.return_value = []
        components['file_watcher'].is_running = False
        
        return components
    
    def test_main_window_creation(self, qtbot, mock_components):
        """Ana pencere oluşturma testi"""
        window = MainWindow(**mock_components)
        qtbot.addWidget(window)
        
        # Pencere oluşturuldu mu?
        assert window.isVisible() == False  # Başlangıçta gizli
        assert window.windowTitle() != ""
        
        # Temel widget'lar var mı?
        assert hasattr(window, 'search_widget')
        assert hasattr(window, 'result_widget')
        assert hasattr(window, 'status_bar')
    
    def test_window_show_hide(self, qtbot, mock_components):
        """Pencere gösterme/gizleme testi"""
        window = MainWindow(**mock_components)
        qtbot.addWidget(window)
        
        # Pencereyi göster
        window.show()
        qtbot.waitForWindowShown(window)
        assert window.isVisible()
        
        # Pencereyi gizle
        window.hide()
        qtbot.wait(100)
        assert window.isVisible() == False
    
    def test_search_widget_integration(self, qtbot, mock_components):
        """Arama widget'ı entegrasyon testi"""
        window = MainWindow(**mock_components)
        qtbot.addWidget(window)
        
        window.show()
        qtbot.waitForWindowShown(window)
        
        # Search widget'a erişim
        search_widget = window.search_widget
        assert search_widget is not None
        
        # Arama kutusuna metin gir
        search_input = search_widget.search_input
        qtbot.keyClicks(search_input, "test arama")
        
        assert search_input.text() == "test arama"
        
        # Arama butonuna tıkla
        search_button = search_widget.search_button
        qtbot.mouseClick(search_button, Qt.LeftButton)
        
        # Mock search engine'in çağrıldığını kontrol et
        mock_components['search_engine'].search.assert_called()
    
    def test_result_widget_display(self, qtbot, mock_components):
        """Sonuç widget'ı gösterim testi"""
        # Mock arama sonuçları
        mock_results = [
            Mock(
                document_id=1,
                document_title="Test Kanunu",
                document_type="KANUN",
                article_number="1",
                content="Test içeriği",
                snippet="test içeriği",
                score=0.85
            )
        ]
        
        mock_components['search_engine'].search.return_value = mock_results
        
        window = MainWindow(**mock_components)
        qtbot.addWidget(window)
        
        window.show()
        qtbot.waitForWindowShown(window)
        
        # Arama yap
        search_widget = window.search_widget
        qtbot.keyClicks(search_widget.search_input, "test")
        qtbot.mouseClick(search_widget.search_button, Qt.LeftButton)
        
        # Results widget'ta sonuçlar gösterildi mi?
        result_widget = window.result_widget
        
        # Result widget'ın içeriğini kontrol et
        # (Gerçek implementasyona göre değişebilir)
        qtbot.wait(100)  # Widget update için bekle
    
    def test_menu_actions(self, qtbot, mock_components):
        """Menü aksiyonları testi"""
        window = MainWindow(**mock_components)
        qtbot.addWidget(window)
        
        window.show()
        qtbot.waitForWindowShown(window)
        
        # Menu bar var mı?
        menu_bar = window.menuBar()
        assert menu_bar is not None
        
        # File menu var mı?
        file_menu = None
        for action in menu_bar.actions():
            if "File" in action.text() or "Dosya" in action.text():
                file_menu = action.menu()
                break
        
        if file_menu:
            # File menu'deki aksiyonları kontrol et
            actions = file_menu.actions()
            assert len(actions) > 0
    
    def test_status_bar_updates(self, qtbot, mock_components):
        """Durum çubuğu güncellemeleri testi"""
        window = MainWindow(**mock_components)
        qtbot.addWidget(window)
        
        window.show()
        qtbot.waitForWindowShown(window)
        
        # Status bar var mı?
        status_bar = window.statusBar()
        assert status_bar is not None
        
        # File watcher status widget'ı test et
        if hasattr(window, 'file_watcher_status'):
            file_watcher_status = window.file_watcher_status
            
            # Status güncelleme
            file_watcher_status.update_status(True, 5)
            qtbot.wait(50)
            
            # Status text kontrolü
            assert "Running" in file_watcher_status.status_text.text()
            assert "5" in file_watcher_status.queue_info.text()
    
    def test_window_resize(self, qtbot, mock_components):
        """Pencere boyutlandırma testi"""
        window = MainWindow(**mock_components)
        qtbot.addWidget(window)
        
        window.show()
        qtbot.waitForWindowShown(window)
        
        # Başlangıç boyutu
        initial_size = window.size()
        assert initial_size.width() > 0
        assert initial_size.height() > 0
        
        # Pencereyi yeniden boyutlandır
        new_width, new_height = 1200, 900
        window.resize(new_width, new_height)
        qtbot.wait(100)
        
        # Yeni boyut kontrolü
        new_size = window.size()
        assert abs(new_size.width() - new_width) < 50  # Approximate check
        assert abs(new_size.height() - new_height) < 50
    
    def test_keyboard_shortcuts(self, qtbot, mock_components):
        """Klavye kısayolları testi"""
        window = MainWindow(**mock_components)
        qtbot.addWidget(window)
        
        window.show()
        qtbot.waitForWindowShown(window)
        
        # Search kısayolu (Ctrl+F)
        qtbot.keySequence(window, "Ctrl+F")
        qtbot.wait(100)
        
        # Search widget'a focus geçti mi?
        if hasattr(window.search_widget, 'search_input'):
            # Focus kontrolü (implementation'a bağlı)
            pass
    
    def test_drag_drop_simulation(self, qtbot, mock_components):
        """Sürükle-bırak simülasyonu testi"""
        window = MainWindow(**mock_components)
        qtbot.addWidget(window)
        
        window.show()
        qtbot.waitForWindowShown(window)
        
        # Drag-drop event simülasyonu
        from PyQt5.QtCore import QMimeData, QUrl
        from PyQt5.QtGui import QDragEnterEvent, QDropEvent
        
        # Mime data oluştur
        mime_data = QMimeData()
        file_url = QUrl.fromLocalFile("/test/path/test.pdf")
        mime_data.setUrls([file_url])
        
        # Drag enter event
        drag_enter_event = QDragEnterEvent(
            window.rect().center(),
            Qt.CopyAction,
            mime_data,
            Qt.LeftButton,
            Qt.NoModifier
        )
        
        # Event'i window'a gönder
        window.dragEnterEvent(drag_enter_event)
        
        # Acceptance kontrolü (implementation'a bağlı)
        # assert drag_enter_event.isAccepted()


@pytest.mark.ui
class TestSearchWidget:
    """Arama widget'ı testleri"""
    
    def test_search_widget_creation(self, qtbot):
        """Arama widget'ı oluşturma testi"""
        mock_search_engine = MagicMock()
        widget = SearchWidget(mock_search_engine)
        qtbot.addWidget(widget)
        
        # Widget oluşturuldu mu?
        assert widget is not None
        assert hasattr(widget, 'search_input')
        assert hasattr(widget, 'search_button')
    
    def test_search_input_validation(self, qtbot):
        """Arama girişi validasyon testi"""
        mock_search_engine = MagicMock()
        widget = SearchWidget(mock_search_engine)
        qtbot.addWidget(widget)
        
        # Boş arama
        widget.search_input.clear()
        qtbot.keyClick(widget.search_button, Qt.LeftButton)
        
        # Boş aramada search engine çağrılmamalı
        mock_search_engine.search.assert_not_called()
        
        # Geçerli arama
        qtbot.keyClicks(widget.search_input, "geçerli arama")
        qtbot.mouseClick(widget.search_button, Qt.LeftButton)
        
        # Geçerli aramada search engine çağrılmalı
        mock_search_engine.search.assert_called()
    
    def test_search_suggestions(self, qtbot):
        """Arama önerileri testi"""
        mock_search_engine = MagicMock()
        mock_search_engine.get_suggestions.return_value = ["vergi", "vergiler", "vergilendirme"]
        
        widget = SearchWidget(mock_search_engine)
        qtbot.addWidget(widget)
        
        # Öneri tetikleme
        qtbot.keyClicks(widget.search_input, "ver")
        qtbot.wait(500)  # Öneri delay'i için bekle
        
        # Önerilerin gösterildiğini kontrol et (implementation'a bağlı)
        if hasattr(widget, 'suggestion_list'):
            assert widget.suggestion_list.count() > 0


@pytest.mark.ui 
class TestResultWidget:
    """Sonuç widget'ı testleri"""
    
    def test_result_widget_creation(self, qtbot):
        """Sonuç widget'ı oluşturma testi"""
        mock_db = MagicMock()
        widget = ResultWidget(mock_db)
        qtbot.addWidget(widget)
        
        assert widget is not None
        assert hasattr(widget, 'results_table')
    
    def test_results_display(self, qtbot):
        """Sonuçları gösterim testi"""
        mock_db = MagicMock()
        widget = ResultWidget(mock_db)
        qtbot.addWidget(widget)
        
        # Mock sonuçlar
        mock_results = [
            Mock(
                document_id=1,
                document_title="Test Kanunu",
                document_type="KANUN",
                score=0.95,
                snippet="test snippet"
            ),
            Mock(
                document_id=2,
                document_title="Test Yönetmelik",
                document_type="YÖNETMELIK",
                score=0.75,
                snippet="başka snippet"
            )
        ]
        
        # Sonuçları göster
        widget.display_results(mock_results)
        qtbot.wait(100)
        
        # Table'da sonuçlar var mı?
        if hasattr(widget, 'results_table'):
            table = widget.results_table
            assert table.rowCount() == 2
    
    def test_result_selection(self, qtbot):
        """Sonuç seçimi testi"""
        mock_db = MagicMock()
        widget = ResultWidget(mock_db)
        qtbot.addWidget(widget)
        
        mock_results = [
            Mock(document_id=1, document_title="Test", score=0.9)
        ]
        
        widget.display_results(mock_results)
        qtbot.wait(100)
        
        # İlk sonucu seç
        if hasattr(widget, 'results_table'):
            table = widget.results_table
            if table.rowCount() > 0:
                table.selectRow(0)
                qtbot.wait(50)
                
                # Selection kontrolü
                assert table.currentRow() == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "ui"])
