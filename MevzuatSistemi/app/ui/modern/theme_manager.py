"""
Modern Theme Manager - Gelişmiş tema yönetimi ve responsive design desteği
"""

import logging
import json
import os
from typing import Dict, Any, Optional, List, Callable, Tuple
from enum import Enum
from dataclasses import dataclass

from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QSlider, QColorDialog, QComboBox,
                           QCheckBox, QSpinBox, QGroupBox, QTabWidget, QScrollArea)
from PyQt5.QtCore import (QObject, pyqtSignal, QTimer, QPropertyAnimation, 
                         QEasingCurve, QRect, QSize, Qt)
from PyQt5.QtGui import QColor, QFont, QFontMetrics, QPainter, QPainterPath
from .design_system import MevzuatDesignSystem, ColorScheme, DesignTokens


class ResponsiveBreakpoint(Enum):
    """Responsive breakpoint'ler"""
    MOBILE = 480      # <= 480px
    TABLET = 768      # <= 768px  
    DESKTOP = 1024    # <= 1024px
    LARGE_DESKTOP = 1440  # > 1024px


@dataclass
class ThemePreferences:
    """Kullanıcı tema tercihleri"""
    scheme: ColorScheme = ColorScheme.LIGHT_PROFESSIONAL
    custom_accent_color: Optional[str] = None
    font_scale: float = 1.0
    compact_mode: bool = False
    high_contrast: bool = False
    reduce_animations: bool = False
    auto_dark_mode: bool = False
    auto_dark_start_hour: int = 18
    auto_dark_end_hour: int = 8
    remember_window_size: bool = True
    adaptive_colors: bool = True


class ResponsiveManager(QObject):
    """Responsive design yöneticisi"""
    
    breakpoint_changed = pyqtSignal(str)  # breakpoint_name
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.current_breakpoint = ResponsiveBreakpoint.DESKTOP
        self.breakpoint_callbacks: Dict[ResponsiveBreakpoint, List[Callable]] = {
            bp: [] for bp in ResponsiveBreakpoint
        }
    
    def update_breakpoint(self, width: int, height: int):
        """Ekran boyutuna göre breakpoint güncelle"""
        old_breakpoint = self.current_breakpoint
        
        if width <= ResponsiveBreakpoint.MOBILE.value:
            self.current_breakpoint = ResponsiveBreakpoint.MOBILE
        elif width <= ResponsiveBreakpoint.TABLET.value:
            self.current_breakpoint = ResponsiveBreakpoint.TABLET
        elif width <= ResponsiveBreakpoint.DESKTOP.value:
            self.current_breakpoint = ResponsiveBreakpoint.DESKTOP
        else:
            self.current_breakpoint = ResponsiveBreakpoint.LARGE_DESKTOP
        
        if old_breakpoint != self.current_breakpoint:
            self.logger.info(f"Breakpoint changed: {old_breakpoint.name} -> {self.current_breakpoint.name}")
            self.breakpoint_changed.emit(self.current_breakpoint.name)
            self._execute_callbacks()
    
    def register_callback(self, breakpoint: ResponsiveBreakpoint, callback: Callable):
        """Breakpoint değişikliği için callback kaydet"""
        if breakpoint not in self.breakpoint_callbacks:
            self.breakpoint_callbacks[breakpoint] = []
        self.breakpoint_callbacks[breakpoint].append(callback)
    
    def _execute_callbacks(self):
        """Mevcut breakpoint için callback'leri çalıştır"""
        for callback in self.breakpoint_callbacks.get(self.current_breakpoint, []):
            try:
                callback()
            except Exception as e:
                self.logger.error(f"Error executing responsive callback: {e}")
    
    def is_mobile(self) -> bool:
        return self.current_breakpoint == ResponsiveBreakpoint.MOBILE
    
    def is_tablet(self) -> bool:
        return self.current_breakpoint == ResponsiveBreakpoint.TABLET
    
    def is_desktop(self) -> bool:
        return self.current_breakpoint in [ResponsiveBreakpoint.DESKTOP, ResponsiveBreakpoint.LARGE_DESKTOP]
    
    def get_grid_columns(self) -> int:
        """Mevcut breakpoint için grid column sayısı"""
        if self.is_mobile():
            return 1
        elif self.is_tablet():
            return 2
        else:
            return 3
    
    def start_monitoring(self, main_window):
        """Ana pencere için responsive monitoring başlat"""
        self.main_window = main_window
        
        # İlk breakpoint'i belirle
        size = main_window.size()
        self.update_breakpoint(size.width(), size.height())
        
        # Resize event'ini dinle
        main_window.resizeEvent = self._on_main_window_resize
        
        self.logger.info("Responsive monitoring started")
    
    def _on_main_window_resize(self, event):
        """Ana pencere boyut değişikliği"""
        size = event.size()
        self.update_breakpoint(size.width(), size.height())
        
        # Orijinal resize event'ini de çağır
        if hasattr(self.main_window, '_original_resize_event'):
            self.main_window._original_resize_event(event)


class AnimationManager:
    """Animasyon yöneticisi"""
    
    def __init__(self, reduce_animations: bool = False):
        self.reduce_animations = reduce_animations
        self.active_animations: List[QPropertyAnimation] = []
    
    def create_fade_animation(self, widget: QWidget, duration: int = 300,
                            start_opacity: float = 0.0, end_opacity: float = 1.0) -> QPropertyAnimation:
        """Fade animasyonu oluştur"""
        if self.reduce_animations:
            duration = duration // 3
        
        animation = QPropertyAnimation(widget, b"windowOpacity")
        animation.setDuration(duration)
        animation.setStartValue(start_opacity)
        animation.setEndValue(end_opacity)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        
        self.active_animations.append(animation)
        animation.finished.connect(lambda: self._remove_animation(animation))
        
        return animation
    
    def create_slide_animation(self, widget: QWidget, duration: int = 300,
                             start_pos: QRect = None, end_pos: QRect = None) -> QPropertyAnimation:
        """Slide animasyonu oluştur"""
        if self.reduce_animations:
            duration = duration // 3
        
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(duration)
        
        if start_pos:
            animation.setStartValue(start_pos)
        if end_pos:
            animation.setEndValue(end_pos)
        
        animation.setEasingCurve(QEasingCurve.OutCubic)
        
        self.active_animations.append(animation)
        animation.finished.connect(lambda: self._remove_animation(animation))
        
        return animation
    
    def _remove_animation(self, animation: QPropertyAnimation):
        """Bitmiş animasyonu listeden çıkar"""
        if animation in self.active_animations:
            self.active_animations.remove(animation)
    
    def stop_all_animations(self):
        """Tüm animasyonları durdur"""
        for animation in self.active_animations:
            animation.stop()
        self.active_animations.clear()


class AdvancedThemeManager(QObject):
    """Gelişmiş tema yöneticisi"""
    
    theme_changed = pyqtSignal(str, dict)  # theme_name, theme_data
    preferences_changed = pyqtSignal(dict)  # preferences
    
    def __init__(self, design_system: MevzuatDesignSystem):
        super().__init__()
        self.design_system = design_system
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Components
        self.responsive_manager = ResponsiveManager()
        self.animation_manager = AnimationManager()
        
        # State
        self.preferences = ThemePreferences()
        self.current_tokens: Optional[DesignTokens] = None
        self.config_file = "theme_preferences.json"
        
        # Auto theme timer
        self.auto_theme_timer = QTimer()
        self.auto_theme_timer.timeout.connect(self._check_auto_theme)
        self.auto_theme_timer.start(60000)  # Her dakika kontrol et
        
        # Load preferences
        self.load_preferences()
        
        # Initial theme application
        self._apply_current_theme()
    
    def set_preferences(self, preferences: ThemePreferences):
        """Tema tercihlerini ayarla"""
        self.preferences = preferences
        
        # Animation manager'ı güncelle
        self.animation_manager.reduce_animations = preferences.reduce_animations
        
        # Auto theme timer'ını güncelle
        if preferences.auto_dark_mode:
            self.auto_theme_timer.start(60000)
        else:
            self.auto_theme_timer.stop()
        
        # Tema uygula
        self._apply_current_theme()
        
        # Signal emit et
        self.preferences_changed.emit(self.preferences.__dict__)
        
        # Preferences'ı kaydet
        self.save_preferences()
    
    def _apply_current_theme(self):
        """Mevcut tercihlere göre tema uygula"""
        try:
            # Auto dark mode kontrolü
            if self.preferences.auto_dark_mode and self._should_use_dark_theme():
                scheme = ColorScheme.DARK_MODERN
            else:
                scheme = self.preferences.scheme
            
            # High contrast override
            if self.preferences.high_contrast:
                scheme = ColorScheme.HIGH_CONTRAST
            
            # Compact mode override
            if self.preferences.compact_mode:
                scheme = ColorScheme.COMPACT
            
            # Custom tokens oluştur
            base_tokens = self.design_system.get_theme(scheme)
            custom_tokens = self._create_custom_tokens(base_tokens)
            
            self.current_tokens = custom_tokens
            
            # CSS oluştur ve uygula
            css = self.design_system.generate_css(custom_tokens)
            self._apply_css_with_responsive(css)
            
            self.theme_changed.emit(scheme.value, custom_tokens.__dict__)
            self.logger.info(f"Applied theme: {scheme.value} with customizations")
            
        except Exception as e:
            self.logger.error(f"Error applying theme: {e}")
    
    def _create_custom_tokens(self, base_tokens: DesignTokens) -> DesignTokens:
        """Kullanıcı tercihlerine göre özelleştirilmiş tokenlar oluştur"""
        custom_tokens = DesignTokens()
        
        # Base tokens'ı kopyala
        for key, value in base_tokens.__dict__.items():
            setattr(custom_tokens, key, value)
        
        # Custom accent color
        if self.preferences.custom_accent_color:
            custom_tokens.primary = self.preferences.custom_accent_color
        
        # Font scaling
        if self.preferences.font_scale != 1.0:
            scale = self.preferences.font_scale
            custom_tokens.font_size_caption = int(custom_tokens.font_size_caption * scale)
            custom_tokens.font_size_small = int(custom_tokens.font_size_small * scale)
            custom_tokens.font_size_body = int(custom_tokens.font_size_body * scale)
            custom_tokens.font_size_subtitle = int(custom_tokens.font_size_subtitle * scale)
            custom_tokens.font_size_title = int(custom_tokens.font_size_title * scale)
            custom_tokens.font_size_headline = int(custom_tokens.font_size_headline * scale)
        
        # Adaptive colors (system accent color integration)
        if self.preferences.adaptive_colors:
            try:
                system_accent = self._get_system_accent_color()
                if system_accent:
                    custom_tokens.primary = system_accent
            except Exception as e:
                self.logger.error(f"Failed to get system accent color: {e}")
                # Fallback to default primary color
        
        return custom_tokens
    
    def _apply_css_with_responsive(self, base_css: str):
        """Responsive CSS ile birlikte uygula"""
        responsive_css = self._generate_responsive_css()
        full_css = base_css + "\n\n" + responsive_css
        
        app = QApplication.instance()
        if app:
            app.setStyleSheet(full_css)
    
    def _generate_responsive_css(self) -> str:
        """Responsive CSS oluştur"""
        return """
            /* Mobile Responsive Styles */
            .mobile-hidden { display: none; }
            .mobile-full-width { width: 100%; }
            .mobile-stack { flex-direction: column; }
            
            /* Tablet Responsive Styles */
            .tablet-grid-2 { grid-template-columns: repeat(2, 1fr); }
            .tablet-compact { padding: var(--spacing-sm); }
            
            /* Desktop Responsive Styles */
            .desktop-grid-3 { grid-template-columns: repeat(3, 1fr); }
            .desktop-sidebar { min-width: 250px; }
            
            /* Animation Preferences */
            .no-animations * { 
                transition: none !important; 
                animation: none !important; 
            }
            
            /* High DPI Support */
            @media (min-resolution: 2dppx) {
                .icon { transform: scale(0.5); }
                .icon-container { zoom: 2; }
            }
        """
    
    def _should_use_dark_theme(self) -> bool:
        """Auto dark mode için dark theme kullanılıp kullanılmayacağını kontrol et"""
        from datetime import datetime
        
        current_hour = datetime.now().hour
        start_hour = self.preferences.auto_dark_start_hour
        end_hour = self.preferences.auto_dark_end_hour
        
        if start_hour > end_hour:  # Gece geçen zaman dilimi (örn: 18-8)
            return current_hour >= start_hour or current_hour < end_hour
        else:  # Normal zaman dilimi (örn: 8-18)
            return start_hour <= current_hour < end_hour
    
    def _check_auto_theme(self):
        """Auto theme kontrolü (timer callback)"""
        if self.preferences.auto_dark_mode:
            self._apply_current_theme()
    
    def _get_system_accent_color(self) -> Optional[str]:
        """Sistem accent rengini al (Windows) - Devre dışı"""
        # Windows Registry'den okuma işlemini devre dışı bırakıyoruz
        # Çünkü bazı sistemlerde sorun çıkarıyor
        return None
    
    def create_theme_selector_widget(self) -> QWidget:
        """Tema seçici widget oluştur"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Ana tema seçimi
        theme_group = QGroupBox("Tema Seçimi")
        theme_layout = QVBoxLayout(theme_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([
            "Açık Profesyonel",
            "Koyu Modern", 
            "Yüksek Kontrast",
            "Kompakt"
        ])
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        theme_layout.addWidget(self.theme_combo)
        
        # Accent color seçimi
        accent_layout = QHBoxLayout()
        accent_label = QLabel("Accent Renk:")
        self.accent_button = QPushButton("Renk Seç")
        self.accent_button.clicked.connect(self._select_accent_color)
        accent_layout.addWidget(accent_label)
        accent_layout.addWidget(self.accent_button)
        theme_layout.addLayout(accent_layout)
        
        layout.addWidget(theme_group)
        
        # Font scaling
        font_group = QGroupBox("Font Boyutu")
        font_layout = QVBoxLayout(font_group)
        
        self.font_scale_slider = QSlider(Qt.Horizontal)
        self.font_scale_slider.setMinimum(80)
        self.font_scale_slider.setMaximum(150)
        self.font_scale_slider.setValue(int(self.preferences.font_scale * 100))
        self.font_scale_slider.valueChanged.connect(self._on_font_scale_changed)
        
        self.font_scale_label = QLabel(f"{self.preferences.font_scale:.1f}x")
        
        font_layout.addWidget(self.font_scale_slider)
        font_layout.addWidget(self.font_scale_label)
        layout.addWidget(font_group)
        
        # Seçenekler
        options_group = QGroupBox("Seçenekler")
        options_layout = QVBoxLayout(options_group)
        
        self.compact_check = QCheckBox("Kompakt Mod")
        self.compact_check.setChecked(self.preferences.compact_mode)
        self.compact_check.toggled.connect(self._on_compact_changed)
        options_layout.addWidget(self.compact_check)
        
        self.high_contrast_check = QCheckBox("Yüksek Kontrast")
        self.high_contrast_check.setChecked(self.preferences.high_contrast)
        self.high_contrast_check.toggled.connect(self._on_high_contrast_changed)
        options_layout.addWidget(self.high_contrast_check)
        
        self.reduce_animations_check = QCheckBox("Animasyonları Azalt")
        self.reduce_animations_check.setChecked(self.preferences.reduce_animations)
        self.reduce_animations_check.toggled.connect(self._on_animations_changed)
        options_layout.addWidget(self.reduce_animations_check)
        
        self.auto_dark_check = QCheckBox("Otomatik Koyu Mod")
        self.auto_dark_check.setChecked(self.preferences.auto_dark_mode)
        self.auto_dark_check.toggled.connect(self._on_auto_dark_changed)
        options_layout.addWidget(self.auto_dark_check)
        
        layout.addWidget(options_group)
        
        return widget
    
    def _on_theme_changed(self, text: str):
        """Theme combo değiştiğinde"""
        theme_map = {
            "Açık Profesyonel": ColorScheme.LIGHT_PROFESSIONAL,
            "Koyu Modern": ColorScheme.DARK_MODERN,
            "Yüksek Kontrast": ColorScheme.HIGH_CONTRAST,
            "Kompakt": ColorScheme.COMPACT
        }
        
        if text in theme_map:
            self.preferences.scheme = theme_map[text]
            self._apply_current_theme()
    
    def _select_accent_color(self):
        """Accent color seçici aç"""
        color = QColorDialog.getColor()
        if color.isValid():
            self.preferences.custom_accent_color = color.name()
            self.accent_button.setStyleSheet(f"background-color: {color.name()};")
            self._apply_current_theme()
    
    def _on_font_scale_changed(self, value: int):
        """Font scale değiştiğinde"""
        scale = value / 100.0
        self.preferences.font_scale = scale
        self.font_scale_label.setText(f"{scale:.1f}x")
        self._apply_current_theme()
    
    def _on_compact_changed(self, checked: bool):
        """Compact mode değiştiğinde"""
        self.preferences.compact_mode = checked
        self._apply_current_theme()
    
    def _on_high_contrast_changed(self, checked: bool):
        """High contrast değiştiğinde"""
        self.preferences.high_contrast = checked
        self._apply_current_theme()
    
    def _on_animations_changed(self, checked: bool):
        """Animations ayarı değiştiğinde"""
        self.preferences.reduce_animations = checked
        self.animation_manager.reduce_animations = checked
        self._apply_current_theme()
    
    def _on_auto_dark_changed(self, checked: bool):
        """Auto dark mode değiştiğinde"""
        self.preferences.auto_dark_mode = checked
        if checked:
            self.auto_theme_timer.start(60000)
        else:
            self.auto_theme_timer.stop()
        self._apply_current_theme()
    
    def save_preferences(self):
        """Tercihleri kaydet"""
        try:
            config = {
                'scheme': self.preferences.scheme.value,
                'custom_accent_color': self.preferences.custom_accent_color,
                'font_scale': self.preferences.font_scale,
                'compact_mode': self.preferences.compact_mode,
                'high_contrast': self.preferences.high_contrast,
                'reduce_animations': self.preferences.reduce_animations,
                'auto_dark_mode': self.preferences.auto_dark_mode,
                'auto_dark_start_hour': self.preferences.auto_dark_start_hour,
                'auto_dark_end_hour': self.preferences.auto_dark_end_hour,
                'remember_window_size': self.preferences.remember_window_size,
                'adaptive_colors': self.preferences.adaptive_colors
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                
            self.logger.info("Theme preferences saved")
            
        except Exception as e:
            self.logger.error(f"Error saving theme preferences: {e}")
    
    def load_preferences(self):
        """Tercihleri yükle"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self.preferences.scheme = ColorScheme(config.get('scheme', ColorScheme.LIGHT_PROFESSIONAL.value))
                self.preferences.custom_accent_color = config.get('custom_accent_color')
                self.preferences.font_scale = config.get('font_scale', 1.0)
                self.preferences.compact_mode = config.get('compact_mode', False)
                self.preferences.high_contrast = config.get('high_contrast', False)
                self.preferences.reduce_animations = config.get('reduce_animations', False)
                self.preferences.auto_dark_mode = config.get('auto_dark_mode', False)
                self.preferences.auto_dark_start_hour = config.get('auto_dark_start_hour', 18)
                self.preferences.auto_dark_end_hour = config.get('auto_dark_end_hour', 8)
                self.preferences.remember_window_size = config.get('remember_window_size', True)
                self.preferences.adaptive_colors = config.get('adaptive_colors', True)
                
                self.logger.info("Theme preferences loaded")
                
        except Exception as e:
            self.logger.error(f"Error loading theme preferences: {e}")
            # Use defaults
    
    def get_main_window_styles(self) -> str:
        """Ana pencere stilleri"""
        tokens = self.design_system.get_current_tokens()
        if not tokens:
            return ""
        
        return f"""
        QMainWindow {{
            background-color: {tokens.background};
            color: {tokens.text_primary};
            font-family: {tokens.font_family_primary};
            font-size: {tokens.font_size_body}px;
        }}
        
        QMainWindow::separator {{
            background-color: {tokens.border_light};
            width: 1px;
            height: 1px;
        }}
        
        QWidget {{
            background-color: transparent;
            color: {tokens.text_primary};
        }}
        
        QScrollArea {{
            border: none;
            background-color: transparent;
        }}
        
        QScrollBar:vertical {{
            background-color: {tokens.background};
            width: 8px;
            border: none;
            border-radius: 4px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {tokens.text_disabled};
            border-radius: 4px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {tokens.text_secondary};
        }}
        
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            border: none;
            background: none;
            height: 0px;
        }}
        
        QScrollBar:horizontal {{
            background-color: {tokens.background};
            height: 8px;
            border: none;
            border-radius: 4px;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {tokens.text_disabled};
            border-radius: 4px;
            min-width: 20px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background-color: {tokens.text_secondary};
        }}
        
        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal {{
            border: none;
            background: none;
            width: 0px;
        }}
        """
    
    def get_menu_styles(self) -> str:
        """Menu bar stilleri"""
        if not self.current_tokens:
            return self.design_system.get_menu_styles()
        
        return f"""
        QMenuBar {{
            background-color: {self.current_tokens.surface};
            color: {self.current_tokens.text_primary};
            border: none;
            padding: {self.current_tokens.spacing_sm}px;
            font-family: {self.current_tokens.font_family_primary};
            font-size: {self.current_tokens.font_size_body}px;
            font-weight: {self.current_tokens.font_weight_normal};
        }}
        
        QMenuBar::item {{
            background-color: transparent;
            padding: {self.current_tokens.spacing_sm}px {self.current_tokens.spacing_md}px;
            border-radius: {self.current_tokens.border_radius_sm}px;
        }}
        
        QMenuBar::item:selected {{
            background-color: {self.current_tokens.primary}15;
            color: {self.current_tokens.primary};
        }}
        
        QMenuBar::item:pressed {{
            background-color: {self.current_tokens.primary}25;
        }}
        
        QMenu {{
            background-color: {self.current_tokens.surface};
            color: {self.current_tokens.text_primary};
            border: 1px solid {self.current_tokens.border_light};
            border-radius: {self.current_tokens.border_radius_md}px;
            padding: {self.current_tokens.spacing_sm}px;
        }}
        
        QMenu::item {{
            padding: {self.current_tokens.spacing_sm}px {self.current_tokens.spacing_md}px;
            border-radius: {self.current_tokens.border_radius_sm}px;
        }}
        
        QMenu::item:selected {{
            background-color: {self.current_tokens.primary}15;
            color: {self.current_tokens.primary};
        }}
        
        QMenu::separator {{
            height: 1px;
            background-color: {self.current_tokens.border_light};
            margin: {self.current_tokens.spacing_xs}px {self.current_tokens.spacing_sm}px;
        }}
        """
