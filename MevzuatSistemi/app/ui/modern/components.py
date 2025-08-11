"""
Modern Components - Mevzuat Sistemi için modern UI bileşenleri
Material Design prensiplerini takip eden responsive bileşenler
"""

import logging
from typing import Dict, Any, Optional, List, Callable, Union
from enum import Enum

from PyQt5.QtWidgets import (
    QPushButton, QLineEdit, QTextEdit, QLabel, QFrame, QWidget, QVBoxLayout, 
    QHBoxLayout, QGridLayout, QScrollArea, QToolButton, QComboBox, QCheckBox,
    QProgressBar, QSlider, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit,
    QCalendarWidget, QListWidget, QTreeWidget, QTableWidget, QTabWidget,
    QSplitter, QGroupBox, QButtonGroup, QRadioButton, QDialog, QDialogButtonBox,
    QMessageBox, QFileDialog, QColorDialog, QFontDialog, QInputDialog,
    QApplication, QGraphicsDropShadowEffect, QSizePolicy, QStackedWidget
)
from PyQt5.QtCore import (
    Qt, QObject, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, 
    QParallelAnimationGroup, QSequentialAnimationGroup, QRect, QSize, QPoint,
    QEvent, QModelIndex, QAbstractListModel, QSortFilterProxyModel
)
from PyQt5.QtGui import (
    QColor, QPalette, QPainter, QPen, QBrush, QFont, QFontMetrics,
    QIcon, QPixmap, QPainterPath, QLinearGradient, QRadialGradient,
    QMouseEvent, QKeyEvent, QFocusEvent,
    QResizeEvent, QShowEvent, QHideEvent
)

from .design_system import DesignTokens
from .theme_manager import AnimationManager


class ButtonType(Enum):
    """Button türleri"""
    PRIMARY = "primary"
    SECONDARY = "secondary" 
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"
    GHOST = "ghost"
    TEXT = "text"
    ACCENT = "accent"  # Ana renk vurgusu için
    TERTIARY = "tertiary"  # Üçüncül renk


class ButtonSize(Enum):
    """Button boyutları"""
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class InputState(Enum):
    """Input durumları"""
    NORMAL = "normal"
    FOCUS = "focus"
    ERROR = "error"
    SUCCESS = "success"
    DISABLED = "disabled"


class ModernButton(QPushButton):
    """Modern button bileşeni"""
    
    def __init__(self, text: str = "", button_type: ButtonType = ButtonType.PRIMARY,
                 size: ButtonSize = ButtonSize.MEDIUM, icon: QIcon = None, 
                 parent: QWidget = None):
        super().__init__(text, parent)
        
        self.button_type = button_type
        self.size = size
        self.animation_manager = AnimationManager()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        if icon:
            self.setIcon(icon)
        
        self._setup_ui()
        self._setup_animations()
    
    def _setup_ui(self):
        """UI ayarları"""
        # Size policy
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
        # Size ayarları
        if self.size == ButtonSize.SMALL:
            self.setFixedHeight(32)
            font_size = 12
        elif self.size == ButtonSize.LARGE:
            self.setFixedHeight(48)
            font_size = 16
        else:  # MEDIUM
            self.setFixedHeight(40)
            font_size = 14
        
        # Font ayarları
        font = self.font()
        font.setPixelSize(font_size)
        font.setWeight(QFont.Medium)
        self.setFont(font)
        
        # Cursor
        self.setCursor(Qt.PointingHandCursor)
        
        # Style
        self._update_style()
    
    def _setup_animations(self):
        """Animasyon ayarları"""
        # Hover animation
        self.hover_animation = QPropertyAnimation(self, b"geometry")
        self.hover_animation.setDuration(150)
        self.hover_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # Click animation
        self.click_animation = QPropertyAnimation(self, b"geometry")
        self.click_animation.setDuration(100)
        self.click_animation.setEasingCurve(QEasingCurve.InQuad)
    
    def _update_style(self):
        """Stil güncellemesi"""
        # Base style
        style = f"""
            ModernButton {{
                border: none;
                border-radius: 8px;
                font-weight: 500;
                text-align: center;
                outline: none;
                padding: 0 16px;
            }}
        """
        
        # Type-specific styles
        if self.button_type == ButtonType.PRIMARY:
            style += """
                ModernButton {
                    background-color: #1976D2;
                    color: white;
                }
                ModernButton:hover {
                    background-color: #1565C0;
                }
                ModernButton:pressed {
                    background-color: #1565C0;
                    margin-top: 1px;
                }
            """
        elif self.button_type == ButtonType.SECONDARY:
            style += """
                ModernButton {
                    background-color: #FFFFFF;
                    color: #1976D2;
                    border: 2px solid #1976D2;
                }
                ModernButton:hover {
                    background-color: #1976D2;
                    color: white;
                }
            """
        elif self.button_type == ButtonType.SUCCESS:
            style += """
                ModernButton {
                    background-color: #388E3C;
                    color: white;
                }
                ModernButton:hover {
                    background-color: #2E7D32;
                }
            """
        elif self.button_type == ButtonType.WARNING:
            style += """
                ModernButton {
                    background-color: #F57C00;
                    color: white;
                }
                ModernButton:hover {
                    background-color: #EF6C00;
                }
            """
        elif self.button_type == ButtonType.ERROR:
            style += """
                ModernButton {
                    background-color: #D32F2F;
                    color: white;
                }
                ModernButton:hover {
                    background-color: #C62828;
                }
            """
        elif self.button_type == ButtonType.GHOST:
            style += """
                ModernButton {
                    background-color: transparent;
                    color: #1976D2;
                    border: 1px solid #BDBDBD;
                }
                ModernButton:hover {
                    background-color: #1976D2;
                    color: white;
                }
            """
        elif self.button_type == ButtonType.TEXT:
            style += """
                ModernButton {
                    background-color: transparent;
                    color: #1976D2;
                    padding: 8px 12px;
                }
                ModernButton:hover {
                    background-color: rgba(25, 118, 210, 0.1);
                }
            """
        elif self.button_type == ButtonType.ACCENT:
            style += """
                ModernButton {
                    background-color: #DC004E;
                    color: white;
                    padding: 8px 16px;
                    border: none;
                }
                ModernButton:hover {
                    background-color: #C51162;
                }
                ModernButton:pressed {
                    background-color: #A0003A;
                }
            """
        elif self.button_type == ButtonType.TERTIARY:
            style += """
                ModernButton {
                    background-color: #757575;
                    color: white;
                    padding: 8px 16px;
                    border: none;
                }
                ModernButton:hover {
                    background-color: #616161;
                }
                ModernButton:pressed {
                    background-color: #424242;
                }
            """
        
        # Disabled state
        style += """
            ModernButton:disabled {
                background-color: #BDBDBD;
                color: #9E9E9E;
                border: none;
            }
        """
        
        self.setStyleSheet(style)
    
    def set_type(self, button_type: ButtonType):
        """Button türünü değiştir"""
        self.button_type = button_type
        self._update_style()
    
    def set_size(self, size: ButtonSize):
        """Button boyutunu değiştir"""
        self.size = size
        self._setup_ui()
    
    def set_loading(self, loading: bool):
        """Loading durumunu ayarla"""
        if loading:
            self.setText("...")  # Basit loading indicator
            self.setEnabled(False)
        else:
            self.setEnabled(True)
    
    def enterEvent(self, event):
        """Mouse enter event"""
        super().enterEvent(event)
        if self.isEnabled():
            self._animate_hover(True)
    
    def leaveEvent(self, event: QEvent):
        """Mouse leave event"""
        super().leaveEvent(event)
        if self.isEnabled():
            self._animate_hover(False)
    
    def mousePressEvent(self, event: QMouseEvent):
        """Mouse press event"""
        super().mousePressEvent(event)
        if self.isEnabled():
            self._animate_click()
    
    def _animate_hover(self, hover: bool):
        """Hover animasyonu"""
        if not self.animation_manager.reduce_animations:
            # Basit hover efekti
            pass
    
    def _animate_click(self):
        """Click animasyonu"""
        if not self.animation_manager.reduce_animations:
            # Basit click efekti
            pass


class SmartInput(QLineEdit):
    """Smart input bileşeni - gelişmiş özelliklerle"""
    
    value_changed = pyqtSignal(str)
    validation_changed = pyqtSignal(bool)  # is_valid
    
    def __init__(self, placeholder: str = "", parent: QWidget = None):
        super().__init__(parent)
        
        self.state = InputState.NORMAL
        self.validation_func: Optional[Callable[[str], bool]] = None
        self.error_message = ""
        self.success_message = ""
        self.logger = logging.getLogger(self.__class__.__name__)
        
        if placeholder:
            self.setPlaceholderText(placeholder)
        
        self._setup_ui()
        self._setup_validation()
    
    def _setup_ui(self):
        """UI ayarları"""
        self.setFixedHeight(44)
        
        # Font
        font = self.font()
        font.setPixelSize(14)
        self.setFont(font)
        
        # Style
        self._update_style()
        
        # Shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(4)
        shadow.setXOffset(0)
        shadow.setYOffset(1)
        shadow.setColor(QColor(0, 0, 0, 25))
        self.setGraphicsEffect(shadow)
    
    def _setup_validation(self):
        """Validation ayarları"""
        self.textChanged.connect(self._on_text_changed)
        self.editingFinished.connect(self._on_editing_finished)
    
    def _update_style(self):
        """Stil güncellemesi"""
        if self.state == InputState.NORMAL:
            border_color = "#E0E0E0"
            background_color = "#FFFFFF"
        elif self.state == InputState.FOCUS:
            border_color = "#1976D2"
            background_color = "#FFFFFF"
        elif self.state == InputState.ERROR:
            border_color = "#D32F2F"
            background_color = "#FFFFFF"
        elif self.state == InputState.SUCCESS:
            border_color = "#388E3C"
            background_color = "#FFFFFF"
        else:  # DISABLED
            border_color = "#E0E0E0"
            background_color = "#BDBDBD"
        
        style = f"""
            SmartInput {{
                background-color: {background_color};
                border: 2px solid {border_color};
                border-radius: 8px;
                padding: 12px 16px;
                font-size: 14px;
                color: #212121;
            }}
            
            SmartInput:focus {{
                border-color: #1976D2;
                outline: none;
            }}
            
            SmartInput::placeholder {{
                color: #9E9E9E;
            }}
        """
        
        self.setStyleSheet(style)
    
    def set_validation(self, validation_func: Callable[[str], bool], 
                      error_message: str = "Geçersiz değer"):
        """Validation fonksiyonu ayarla"""
        self.validation_func = validation_func
        self.error_message = error_message
    
    def set_success_message(self, message: str):
        """Başarı mesajını ayarla"""
        self.success_message = message
    
    def _on_text_changed(self, text: str):
        """Metin değiştiğinde"""
        self.value_changed.emit(text)
        
        if self.validation_func:
            is_valid = self.validation_func(text)
            self.validation_changed.emit(is_valid)
            
            if text and not is_valid:
                self.set_state(InputState.ERROR)
            elif text and is_valid:
                self.set_state(InputState.SUCCESS)
            else:
                self.set_state(InputState.NORMAL)
    
    def _on_editing_finished(self):
        """Düzenleme bittiğinde"""
        if self.validation_func and self.text():
            is_valid = self.validation_func(self.text())
            if is_valid:
                self.set_state(InputState.SUCCESS)
            else:
                self.set_state(InputState.ERROR)
    
    def set_state(self, state: InputState):
        """Input durumunu ayarla"""
        self.state = state
        self._update_style()
    
    def get_state(self) -> InputState:
        """Mevcut durumu al"""
        return self.state
    
    def is_valid(self) -> bool:
        """Değerin geçerli olup olmadığını kontrol et"""
        if self.validation_func:
            return self.validation_func(self.text())
        return True
    
    def focusInEvent(self, event: QFocusEvent):
        """Focus in event"""
        super().focusInEvent(event)
        if self.state != InputState.ERROR:
            self.set_state(InputState.FOCUS)
    
    def focusOutEvent(self, event: QFocusEvent):
        """Focus out event"""
        super().focusOutEvent(event)
        if self.state == InputState.FOCUS:
            self.set_state(InputState.NORMAL)


class ModernCard(QFrame):
    """Modern card bileşeni"""
    
    clicked = pyqtSignal()
    
    def __init__(self, title: str = "", content: str = "", 
                 clickable: bool = False, parent: QWidget = None):
        super().__init__(parent)
        
        self.title = title
        self.content = content
        self.clickable = clickable
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self._setup_ui()
        self._setup_animations()
    
    def _setup_ui(self):
        """UI ayarları"""
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Title
        if self.title:
            title_label = QLabel(self.title)
            title_font = title_label.font()
            title_font.setPixelSize(18)
            title_font.setWeight(QFont.Medium)
            title_label.setFont(title_font)
            title_label.setStyleSheet("color: #212121;")
            layout.addWidget(title_label)
        
        # Content
        if self.content:
            content_label = QLabel(self.content)
            content_label.setWordWrap(True)
            content_label.setStyleSheet("color: #757575;")
            layout.addWidget(content_label)
        
        # Style
        self._update_style()
        
        # Clickable
        if self.clickable:
            self.setCursor(Qt.PointingHandCursor)
        
        # Shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 15))
        self.setGraphicsEffect(shadow)
    
    def _setup_animations(self):
        """Animasyon ayarları"""
        # Hover animation
        self.hover_animation = QPropertyAnimation(self, b"geometry")
        self.hover_animation.setDuration(200)
        self.hover_animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def _update_style(self):
        """Stil güncellemesi"""
        style = """
            ModernCard {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 12px;
            }
            
            ModernCard:hover {
                border-color: #BDBDBD;
            }
        """
        
        self.setStyleSheet(style)
    
    def set_title(self, title: str):
        """Başlığı ayarla"""
        self.title = title
        # UI'ı yeniden oluştur
        self._clear_layout()
        self._setup_ui()
    
    def set_content(self, content: str):
        """İçeriği ayarla"""
        self.content = content
        # UI'ı yeniden oluştur
        self._clear_layout()
        self._setup_ui()
    
    def _clear_layout(self):
        """Layout'u temizle"""
        while self.layout().count():
            item = self.layout().takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def mousePressEvent(self, event: QMouseEvent):
        """Mouse press event"""
        super().mousePressEvent(event)
        if self.clickable and event.button() == Qt.LeftButton:
            self.clicked.emit()
    
    def enterEvent(self, event):
        """Mouse enter event"""
        super().enterEvent(event)
        if self.clickable:
            self._animate_hover(True)
    
    def leaveEvent(self, event: QEvent):
        """Mouse leave event"""
        super().leaveEvent(event)
        if self.clickable:
            self._animate_hover(False)
    
    def _animate_hover(self, hover: bool):
        """Hover animasyonu"""
        # Shadow güncelleme
        shadow = self.graphicsEffect()
        if shadow:
            if hover:
                shadow.setBlurRadius(12)
                shadow.setYOffset(4)
            else:
                shadow.setBlurRadius(8)
                shadow.setYOffset(2)


class ResponsiveGrid(QWidget):
    """Responsive grid layout"""
    
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        
        self.items: List[QWidget] = []
        self.columns = 3
        self.spacing = 16
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """UI ayarları"""
        self.layout = QGridLayout(self)
        self.layout.setSpacing(self.spacing)
        self.layout.setContentsMargins(self.spacing, self.spacing, 
                                      self.spacing, self.spacing)
    
    def add_item(self, widget: QWidget):
        """Grid'e item ekle"""
        self.items.append(widget)
        self._refresh_layout()
    
    def remove_item(self, widget: QWidget):
        """Grid'den item çıkar"""
        if widget in self.items:
            self.items.remove(widget)
            widget.setParent(None)
            self._refresh_layout()
    
    def set_columns(self, columns: int):
        """Column sayısını ayarla"""
        self.columns = max(1, columns)
        self._refresh_layout()
    
    def set_spacing(self, spacing: int):
        """Spacing'i ayarla"""
        self.spacing = spacing
        self.layout.setSpacing(spacing)
        self.layout.setContentsMargins(spacing, spacing, spacing, spacing)
    
    def _refresh_layout(self):
        """Layout'u yenile"""
        # Tüm widget'ları layout'tan çıkar
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        
        # Yeniden ekle
        for i, widget in enumerate(self.items):
            row = i // self.columns
            col = i % self.columns
            self.layout.addWidget(widget, row, col)
            widget.setParent(self)
    
    def clear(self):
        """Tüm item'ları temizle"""
        self.items.clear()
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def resizeEvent(self, event: QResizeEvent):
        """Resize event - responsive davranış"""
        super().resizeEvent(event)
        
        # Responsive column calculation
        width = event.size().width()
        if width <= 480:  # Mobile
            new_columns = 1
        elif width <= 768:  # Tablet
            new_columns = 2
        else:  # Desktop
            new_columns = 3
        
        if new_columns != self.columns:
            self.set_columns(new_columns)


class ModernDialog(QDialog):
    """Modern dialog bileşeni"""
    
    def __init__(self, title: str = "Dialog", parent: QWidget = None):
        super().__init__(parent)
        
        self.title = title
        self.animation_manager = AnimationManager()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self._setup_ui()
        self._setup_animations()
    
    def _setup_ui(self):
        """UI ayarları"""
        self.setWindowTitle(self.title)
        self.setModal(True)
        self.setFixedSize(400, 300)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Title
        title_label = QLabel(self.title)
        title_font = title_label.font()
        title_font.setPixelSize(20)
        title_font.setWeight(QFont.Medium)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Content area
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        layout.addWidget(self.content_widget)
        
        # Button box
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        
        # Style
        self._update_style()
    
    def _setup_animations(self):
        """Animasyon ayarları"""
        # Show animation
        self.show_animation = QPropertyAnimation(self, b"geometry")
        self.show_animation.setDuration(300)
        self.show_animation.setEasingCurve(QEasingCurve.OutBack)
        
        # Fade animation
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(200)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def _update_style(self):
        """Stil güncellemesi"""
        style = """
            ModernDialog {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 16px;
            }
            
            QLabel {
                color: #212121;
            }
            
            QPushButton {
                background-color: #1976D2;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
                min-width: 80px;
            }
            
            QPushButton:hover {
                background-color: #1565C0;
            }
        """
        
        self.setStyleSheet(style)
    
    def add_content_widget(self, widget: QWidget):
        """Content widget ekle"""
        self.content_layout.addWidget(widget)
    
    def showEvent(self, event: QShowEvent):
        """Show event - animasyon ile"""
        super().showEvent(event)
        
        if not self.animation_manager.reduce_animations:
            # Fade in animation
            self.setWindowOpacity(0.0)
            self.fade_animation.setStartValue(0.0)
            self.fade_animation.setEndValue(1.0)
            self.fade_animation.start()
    
    def closeEvent(self, event):
        """Close event - animasyon ile"""
        if not self.animation_manager.reduce_animations:
            # Fade out animation
            self.fade_animation.setStartValue(1.0)
            self.fade_animation.setEndValue(0.0)
            self.fade_animation.finished.connect(lambda: super().closeEvent(event))
            self.fade_animation.start()
            event.ignore()
        else:
            super().closeEvent(event)


class ResponsiveGrid(QWidget):
    """Responsive grid layout widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Ana layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Grid layout
        self.grid_layout = QGridLayout()
        self.main_layout.addLayout(self.grid_layout)
        
        # Widget'ların referansı
        self.widgets: List[QWidget] = []
        self.widget_positions: List[tuple] = []  # (row, col, rowspan, colspan)
        
        self.logger.info("ResponsiveGrid initialized")
    
    def add_widget(self, widget: QWidget, row: int, col: int, rowspan: int = 1, colspan: int = 1):
        """Grid'e widget ekle"""
        self.widgets.append(widget)
        self.widget_positions.append((row, col, rowspan, colspan))
        self.grid_layout.addWidget(widget, row, col, rowspan, colspan)
        
        self.logger.debug(f"Widget added to grid: row={row}, col={col}, rowspan={rowspan}, colspan={colspan}")
    
    def stack_layout(self):
        """Mobil/tablet için stacked layout'a geç"""
        # Mevcut widget'ları grid'den temizle
        for widget in self.widgets:
            self.grid_layout.removeWidget(widget)
        
        # Tek sütunda yerleştir
        for i, widget in enumerate(self.widgets):
            self.grid_layout.addWidget(widget, i, 0, 1, 1)
        
        self.logger.info("Switched to stacked layout")
    
    def grid_layout_mode(self):
        """Desktop için grid layout'a geç"""
        # Mevcut widget'ları temizle
        for widget in self.widgets:
            self.grid_layout.removeWidget(widget)
        
        # Orijinal pozisyonlara yerleştir
        for widget, (row, col, rowspan, colspan) in zip(self.widgets, self.widget_positions):
            self.grid_layout.addWidget(widget, row, col, rowspan, colspan)
        
        self.logger.info("Switched to grid layout")
    
    def set_spacing(self, spacing: int):
        """Grid spacing ayarla"""
        self.grid_layout.setSpacing(spacing)
    
    def set_margins(self, left: int, top: int, right: int, bottom: int):
        """Grid margins ayarla"""
        self.grid_layout.setContentsMargins(left, top, right, bottom)
    
    def clear_grid(self):
        """Grid'i temizle"""
        for widget in self.widgets:
            self.grid_layout.removeWidget(widget)
        
        self.widgets.clear()
        self.widget_positions.clear()
        
        self.logger.info("Grid cleared")
