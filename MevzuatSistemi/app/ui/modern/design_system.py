"""
Modern Design System - Mevzuat Sistemi için tasarım sistemi
Material Design ve modern UI prensiplerini temel alır
"""

import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QColor, QPalette, QFont


class ColorScheme(Enum):
    """Renk şemaları"""
    LIGHT_PROFESSIONAL = "light_professional"
    DARK_MODERN = "dark_modern"
    HIGH_CONTRAST = "high_contrast"
    COMPACT = "compact"
    CUSTOM = "custom"


@dataclass  
class SpacingTokens:
    """Spacing tokenları için namespace"""
    xs: int = 4
    sm: int = 8 
    md: int = 16
    lg: int = 24
    xl: int = 32
    xxl: int = 48

@dataclass
class BorderRadiusTokens:
    """Border radius tokenları için namespace"""
    sm: int = 4
    md: int = 8
    lg: int = 12
    xl: int = 16

@dataclass
class DesignTokens:
    """Design tokens - tasarım sabitleri"""
    
    def __post_init__(self):
        # Nested objects
        self.spacing = SpacingTokens()
        self.border_radius = BorderRadiusTokens()
    
    # Colors
    primary: str = "#1976D2"          # Ana renk - Mavi
    primary_variant: str = "#1565C0"  # Ana renk varyantı
    secondary: str = "#DC004E"        # İkincil renk - Kırmızı
    secondary_variant: str = "#C51162" # İkincil renk varyantı
    
    # Semantic colors
    success: str = "#388E3C"          # Başarı - Yeşil
    warning: str = "#F57C00"          # Uyarı - Turuncu
    error: str = "#D32F2F"            # Hata - Kırmızı
    info: str = "#1976D2"             # Bilgi - Mavi
    
    # Surface colors
    surface: str = "#FFFFFF"          # Yüzey
    background: str = "#FAFAFA"       # Arka plan
    card_background: str = "#FFFFFF"  # Kart arka planı
    
    # Text colors
    text_primary: str = "#212121"     # Ana metin
    text_secondary: str = "#757575"   # İkincil metin
    text_disabled: str = "#BDBDBD"    # Devre dışı metin
    text_hint: str = "#9E9E9E"        # İpucu metni
    
    # Border colors
    border_light: str = "#E0E0E0"     # Açık border
    border_medium: str = "#BDBDBD"    # Orta border
    border_dark: str = "#757575"      # Koyu border
    
    # Spacing (8dp grid system)
    spacing_xs: int = 4    # Extra small
    spacing_sm: int = 8    # Small  
    spacing_md: int = 16   # Medium
    spacing_lg: int = 24   # Large
    spacing_xl: int = 32   # Extra large
    spacing_xxl: int = 48  # Extra extra large
    
    # Legacy spacing support
    spacing: int = 16      # Default spacing for backward compatibility
    
    # Border radius
    border_radius_sm: int = 4   # Small radius
    border_radius_md: int = 8   # Medium radius
    border_radius_lg: int = 12  # Large radius
    border_radius_xl: int = 16  # Extra large radius
    
    # Elevation/Shadow levels
    elevation_1: str = "0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)"
    elevation_2: str = "0 3px 6px rgba(0,0,0,0.16), 0 3px 6px rgba(0,0,0,0.23)"
    elevation_3: str = "0 10px 20px rgba(0,0,0,0.19), 0 6px 6px rgba(0,0,0,0.23)"
    elevation_4: str = "0 14px 28px rgba(0,0,0,0.25), 0 10px 10px rgba(0,0,0,0.22)"
    
    # Typography
    font_family_primary: str = "Segoe UI"
    font_family_secondary: str = "Roboto"
    font_family_monospace: str = "Consolas"
    
    # Font sizes
    font_size_caption: int = 10    # Caption
    font_size_small: int = 12      # Small text
    font_size_body: int = 14       # Body text
    font_size_subtitle: int = 16   # Subtitle
    font_size_title: int = 20      # Title
    font_size_headline: int = 24   # Headline
    
    # Font weights
    font_weight_light: str = "300"
    font_weight_normal: str = "400"
    font_weight_medium: str = "500"
    font_weight_semibold: str = "600"
    font_weight_bold: str = "700"
    
    # Animation timings
    animation_fast: int = 150      # Fast animation
    animation_normal: int = 300    # Normal animation
    animation_slow: int = 500      # Slow animation
    
    # Z-index layers
    z_dropdown: int = 1000
    z_modal: int = 1500
    z_tooltip: int = 2000


class MevzuatDesignSystem:
    """Mevzuat Sistemi Design System"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.themes: Dict[ColorScheme, DesignTokens] = {}
        self.current_theme = ColorScheme.LIGHT_PROFESSIONAL
        self._setup_default_themes()
        # tokens property for compatibility
        self.tokens = self.current_tokens
    
    def apply_theme(self, theme: ColorScheme):
        """Temayı uygula"""
        self.current_theme = theme
        return True
    
    @property
    def current_tokens(self) -> DesignTokens:
        """Mevcut tema token'larını döndür"""
        return self.themes.get(self.current_theme, self.themes[ColorScheme.LIGHT_PROFESSIONAL])
    
    def _setup_default_themes(self):
        """Varsayılan temaları ayarla"""
        
        # Light Professional Theme
        self.themes[ColorScheme.LIGHT_PROFESSIONAL] = DesignTokens()
        
        # Dark Modern Theme
        dark_tokens = DesignTokens()
        dark_tokens.primary = "#2196F3"
        dark_tokens.primary_variant = "#1976D2"
        dark_tokens.surface = "#1E1E1E"
        dark_tokens.background = "#121212"
        dark_tokens.card_background = "#1E1E1E"
        dark_tokens.text_primary = "#FFFFFF"
        dark_tokens.text_secondary = "#B0BEC5"
        dark_tokens.text_disabled = "#555555"
        dark_tokens.border_light = "#333333"
        dark_tokens.border_medium = "#555555"
        dark_tokens.border_dark = "#777777"
        self.themes[ColorScheme.DARK_MODERN] = dark_tokens
        
        # High Contrast Theme
        hc_tokens = DesignTokens()
        hc_tokens.primary = "#000000"
        hc_tokens.primary_variant = "#333333"
        hc_tokens.secondary = "#FF0000"
        hc_tokens.surface = "#FFFFFF"
        hc_tokens.background = "#FFFFFF"
        hc_tokens.text_primary = "#000000"
        hc_tokens.text_secondary = "#000000"
        hc_tokens.border_light = "#000000"
        hc_tokens.border_medium = "#000000"
        hc_tokens.border_dark = "#000000"
        self.themes[ColorScheme.HIGH_CONTRAST] = hc_tokens
        
        # Compact Theme (smaller spacing)
        compact_tokens = DesignTokens()
        compact_tokens.spacing_xs = 2
        compact_tokens.spacing_sm = 4
        compact_tokens.spacing_md = 8
        compact_tokens.spacing_lg = 12
        compact_tokens.spacing_xl = 16
        compact_tokens.spacing_xxl = 24
        compact_tokens.font_size_caption = 9
        compact_tokens.font_size_small = 11
        compact_tokens.font_size_body = 12
        compact_tokens.font_size_subtitle = 14
        compact_tokens.font_size_title = 16
        compact_tokens.font_size_headline = 18
        self.themes[ColorScheme.COMPACT] = compact_tokens
    
    def get_theme(self, scheme: ColorScheme) -> DesignTokens:
        """Tema tokenlarını al"""
        return self.themes.get(scheme, self.themes[ColorScheme.LIGHT_PROFESSIONAL])
    
    def create_custom_theme(self, base_scheme: ColorScheme, 
                           custom_tokens: Dict[str, Any]) -> DesignTokens:
        """Özel tema oluştur"""
        base_tokens = self.get_theme(base_scheme)
        custom_theme = DesignTokens()
        
        # Base tokens'ı kopyala
        for key, value in base_tokens.__dict__.items():
            setattr(custom_theme, key, value)
        
        # Custom tokens'ı uygula
        for key, value in custom_tokens.items():
            if hasattr(custom_theme, key):
                setattr(custom_theme, key, value)
        
        return custom_theme
    
    def get_menu_styles(self) -> str:
        """Menu stilleri - Basit implementasyon"""
        tokens = self.current_tokens
        if not tokens:
            return ""
        
        return f"""
        QMenuBar {{
            background-color: {tokens.surface};
            color: {tokens.text_primary};
            border: none;
            padding: {tokens.spacing_sm}px;
            font-family: {tokens.font_family_primary};
            font-size: {tokens.font_size_body}px;
        }}
        
        QMenuBar::item {{
            background-color: transparent;
            padding: {tokens.spacing_sm}px {tokens.spacing_md}px;
            border-radius: {tokens.border_radius_sm}px;
        }}
        
        QMenuBar::item:selected {{
            background-color: {tokens.primary}15;
            color: {tokens.primary};
        }}
        """
    
    def get_toolbar_styles(self) -> str:
        """Toolbar stilleri - Basit implementasyon"""
        tokens = self.current_tokens
        if not tokens:
            return ""
        
        return f"""
        QToolBar {{
            background-color: {tokens.surface};
            color: {tokens.text_primary};
            border: none;
            spacing: {tokens.spacing_sm}px;
            padding: {tokens.spacing_sm}px;
        }}
        
        QToolBar::separator {{
            background-color: {tokens.border_light};
            width: 1px;
            margin: {tokens.spacing_xs}px {tokens.spacing_sm}px;
        }}
        """
    
    def get_input_styles(self) -> str:
        """Input stilleri - Basit implementasyon"""
        tokens = self.current_tokens
        if not tokens:
            return ""
        
        return f"""
        QComboBox, QLineEdit, QSpinBox {{
            background-color: {tokens.surface};
            color: {tokens.text_primary};
            border: 1px solid {tokens.border_light};
            border-radius: {tokens.border_radius_sm}px;
            padding: {tokens.spacing_sm}px;
            font-family: {tokens.font_family_primary};
            font-size: {tokens.font_size_body}px;
        }}
        
        QComboBox:focus, QLineEdit:focus, QSpinBox:focus {{
            border-color: {tokens.primary};
            outline: none;
        }}
        """
    
    def get_checkbox_styles(self) -> str:
        """Checkbox stilleri - Basit implementasyon"""
        tokens = self.current_tokens
        if not tokens:
            return ""
        
        return f"""
        QCheckBox {{
            color: {tokens.text_primary};
            font-family: {tokens.font_family_primary};
            font-size: {tokens.font_size_body}px;
            spacing: {tokens.spacing_sm}px;
        }}
        
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid {tokens.border_light};
            border-radius: {tokens.border_radius_sm}px;
            background-color: {tokens.surface};
        }}
        
        QCheckBox::indicator:checked {{
            background-color: {tokens.primary};
            border-color: {tokens.primary};
        }}
        """
    
    def get_status_bar_styles(self) -> str:
        """Status bar stilleri - Basit implementasyon"""
        tokens = self.current_tokens
        if not tokens:
            return ""
        
        return f"""
        QStatusBar {{
            background-color: {tokens.surface};
            color: {tokens.text_secondary};
            border-top: 1px solid {tokens.border_light};
            padding: {tokens.spacing_xs}px {tokens.spacing_sm}px;
            font-family: {tokens.font_family_primary};
            font-size: {tokens.font_size_small}px;
        }}
        """
    
    def get_progress_bar_styles(self) -> str:
        """Progress bar stilleri - Basit implementasyon"""
        tokens = self.current_tokens
        if not tokens:
            return ""
        
        return f"""
        QProgressBar {{
            background-color: {tokens.background};
            border: 1px solid {tokens.border_light};
            border-radius: {tokens.border_radius_sm}px;
            text-align: center;
            color: {tokens.text_primary};
            height: 20px;
        }}
        
        QProgressBar::chunk {{
            background-color: {tokens.primary};
            border-radius: {tokens.border_radius_sm}px;
        }}
        """
    
    def get_current_tokens(self) -> DesignTokens:
        """Mevcut tema tokenlarını döndür"""
        return self.current_tokens
    
    def generate_css(self, tokens: DesignTokens) -> str:
        """Design tokens'tan PyQt5 uyumlu CSS oluştur"""
        return f"""
            /* Mevzuat Design System CSS - PyQt5 Uyumlu */
            
            /* Base Widget Styles */
            QWidget {{
                background-color: {tokens.background};
                color: {tokens.text_primary};
                font-family: "{tokens.font_family_primary}";
                font-size: {tokens.font_size_body}px;
            }}
            
            /* Button Styles */
            QPushButton {{
                background-color: {tokens.primary};
                color: white;
                border: none;
                border-radius: {tokens.border_radius_md}px;
                padding: {tokens.spacing_sm}px {tokens.spacing_md}px;
                font-weight: 500;
                font-size: {tokens.font_size_body}px;
                min-height: 36px;
            }}
            
            QPushButton:hover {{
                background-color: {tokens.primary_variant};
            }}
            
            QPushButton:pressed {{
                background-color: {tokens.primary_variant};
            }}
            
            QPushButton:disabled {{
                background-color: {tokens.text_disabled};
                color: {tokens.text_hint};
            }}
            
            /* Input Styles */
            QLineEdit, QTextEdit, QSpinBox, QComboBox {{
                background-color: {tokens.surface};
                border: 2px solid {tokens.border_light};
                border-radius: {tokens.border_radius_md}px;
                padding: {tokens.spacing_sm}px {tokens.spacing_md}px;
                font-size: {tokens.font_size_body}px;
                min-height: 24px;
            }}
            
            QLineEdit:focus, QTextEdit:focus {{
                border-color: {tokens.primary};
            }}
            
            QLineEdit:hover, QTextEdit:hover {{
                border-color: {tokens.border_medium};
            }}
            
            /* Card Style Frames */
            QFrame {{
                background-color: {tokens.surface};
                border: 1px solid {tokens.border_light};
                border-radius: {tokens.border_radius_lg}px;
                padding: {tokens.spacing_md}px;
                margin: {tokens.spacing_sm}px;
            }}
            
            /* List Widget */
            QListWidget {{
                background-color: {tokens.surface};
                border: 1px solid {tokens.border_light};
                border-radius: {tokens.border_radius_md}px;
                padding: {tokens.spacing_xs}px;
            }}
            
            QListWidget::item {{
                padding: {tokens.spacing_sm}px;
                border-radius: {tokens.border_radius_sm}px;
                margin: 2px;
            }}
            
            QListWidget::item:selected {{
                background-color: {tokens.primary};
                color: white;
            }}
            
            QListWidget::item:hover {{
                background-color: {tokens.border_light};
            }}
            
            /* Tab Widget */
            QTabWidget::pane {{
                border: 1px solid {tokens.border_light};
                background-color: {tokens.surface};
                border-radius: {tokens.border_radius_md}px;
            }}
            
            QTabBar::tab {{
                background-color: {tokens.background};
                color: {tokens.text_secondary};
                border: 1px solid {tokens.border_light};
                padding: {tokens.spacing_sm}px {tokens.spacing_md}px;
                margin: 2px;
                border-radius: {tokens.border_radius_sm}px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {tokens.primary};
                color: white;
            }}
            
            QTabBar::tab:hover {{
                background-color: {tokens.border_medium};
            }}
            
            /* Menu Styles */
            QMenuBar {{
                background-color: {tokens.surface};
                color: {tokens.text_primary};
                border-bottom: 1px solid {tokens.border_light};
            }}
            
            QMenuBar::item {{
                padding: {tokens.spacing_sm}px {tokens.spacing_md}px;
                background-color: transparent;
            }}
            
            QMenuBar::item:selected {{
                background-color: {tokens.primary};
                color: white;
            }}
            
            QMenu {{
                background-color: {tokens.surface};
                color: {tokens.text_primary};
                border: 1px solid {tokens.border_light};
                border-radius: {tokens.border_radius_sm}px;
                padding: {tokens.spacing_xs}px;
            }}
            
            QMenu::item {{
                padding: {tokens.spacing_sm}px {tokens.spacing_md}px;
                border-radius: {tokens.border_radius_sm}px;
                margin: 1px;
            }}
            
            QMenu::item:selected {{
                background-color: {tokens.primary};
                color: white;
            }}
            
            /* Progress Bar */
            QProgressBar {{
                background-color: {tokens.border_light};
                border: none;
                border-radius: {tokens.border_radius_sm}px;
                text-align: center;
                height: 24px;
            }}
            
            QProgressBar::chunk {{
                background-color: {tokens.primary};
                border-radius: {tokens.border_radius_sm}px;
            }}
            
            /* Scroll Bar */
            QScrollBar:vertical {{
                background-color: {tokens.background};
                width: 12px;
                border-radius: 6px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {tokens.border_medium};
                border-radius: 6px;
                min-height: 20px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {tokens.border_dark};
            }}
            
            /* Status Bar */
            QStatusBar {{
                background-color: {tokens.surface};
                color: {tokens.text_secondary};
                border-top: 1px solid {tokens.border_light};
                padding: {tokens.spacing_xs}px;
            }}
        """
    
    def get_text_styles(self, variant: str = 'body') -> str:
        """Basit metin stilleri"""
        tokens = self.current_tokens
        
        style_map = {
            'headline': f"font-size: {tokens.font_size_headline}px; font-weight: 700; color: {tokens.text_primary};",
            'title': f"font-size: {tokens.font_size_title}px; font-weight: 600; color: {tokens.text_primary};",
            'subtitle': f"font-size: {tokens.font_size_subtitle}px; font-weight: 500; color: {tokens.text_primary};",
            'body': f"font-size: {tokens.font_size_body}px; font-weight: 400; color: {tokens.text_primary};",
            'body1': f"font-size: {tokens.font_size_body}px; font-weight: 400; color: {tokens.text_primary};",
            'body2': f"font-size: {tokens.font_size_small}px; font-weight: 400; color: {tokens.text_secondary};",
            'caption': f"font-size: {tokens.font_size_caption}px; font-weight: 400; color: {tokens.text_secondary};",
            'button': f"font-size: {tokens.font_size_body}px; font-weight: 500; color: {tokens.text_primary};"
        }
        
        return style_map.get(variant, style_map['body'])

    def create_custom_theme(self, base_scheme: ColorScheme, overrides: Dict[str, str]) -> DesignTokens:
        """Özel tema oluştur"""
        base_tokens = self.themes.get(base_scheme, self.themes[ColorScheme.LIGHT_PROFESSIONAL])
        custom_tokens = DesignTokens()
        
        # Base tokens'ı kopyala
        for field_name in base_tokens.__dataclass_fields__:
            if hasattr(base_tokens, field_name):
                setattr(custom_tokens, field_name, getattr(base_tokens, field_name))
        
        # Override'ları uygula
        for key, value in overrides.items():
            if hasattr(custom_tokens, key):
                setattr(custom_tokens, key, value)
        
        return custom_tokens


class ThemeManager(QObject):
    """Tema yöneticisi"""
    
    theme_changed = pyqtSignal(str)  # theme_name
    
    def __init__(self, design_system: MevzuatDesignSystem):
        super().__init__()
        self.design_system = design_system
        self.logger = logging.getLogger(self.__class__.__name__)
        self.current_scheme = ColorScheme.LIGHT_PROFESSIONAL
        self.current_tokens: Optional[DesignTokens] = None
        self._custom_accent_color: Optional[str] = None
    
    def apply_theme(self, scheme: ColorScheme, accent_color: Optional[str] = None):
        """Tema uygula"""
        try:
            self.logger.info(f"Applying theme: {scheme.value}")
            
            # Accent color desteği
            if accent_color:
                self._custom_accent_color = accent_color
                tokens = self.design_system.create_custom_theme(
                    scheme, 
                    {"primary": accent_color}
                )
            else:
                tokens = self.design_system.get_theme(scheme)
            
            self.current_scheme = scheme
            self.current_tokens = tokens
            
            # CSS oluştur ve uygula
            css = self.design_system.generate_css(tokens)
            self._apply_css_to_application(css)
            
            # QPalette güncelle
            self._update_application_palette(tokens)
            
            self.theme_changed.emit(scheme.value)
            self.logger.info(f"Theme {scheme.value} applied successfully")
            
        except Exception as e:
            self.logger.error(f"Error applying theme {scheme.value}: {e}")
    
    def _apply_css_to_application(self, css: str):
        """CSS'i uygulamaya uygula"""
        app = QApplication.instance()
        if app:
            app.setStyleSheet(css)
    
    def _update_application_palette(self, tokens: DesignTokens):
        """Uygulama palette'ini güncelle"""
        app = QApplication.instance()
        if not app:
            return
        
        palette = QPalette()
        
        # Ana renkler
        palette.setColor(QPalette.Window, QColor(tokens.background))
        palette.setColor(QPalette.WindowText, QColor(tokens.text_primary))
        palette.setColor(QPalette.Base, QColor(tokens.surface))
        palette.setColor(QPalette.Text, QColor(tokens.text_primary))
        palette.setColor(QPalette.Button, QColor(tokens.primary))
        palette.setColor(QPalette.ButtonText, QColor("#FFFFFF"))
        palette.setColor(QPalette.Highlight, QColor(tokens.primary))
        palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
        
        # Devre dışı durumlar
        palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(tokens.text_disabled))
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor(tokens.text_disabled))
        palette.setColor(QPalette.Disabled, QPalette.Button, QColor(tokens.text_disabled))
        
        app.setPalette(palette)
    
    def get_current_tokens(self) -> Optional[DesignTokens]:
        """Mevcut tema tokenlarını al"""
        return self.current_tokens
    
    def get_current_scheme(self) -> ColorScheme:
        """Mevcut renk şemasını al"""
        return self.current_scheme
    
    def get_available_themes(self) -> list:
        """Mevcut temaları listele"""
        return [scheme.value for scheme in ColorScheme if scheme != ColorScheme.CUSTOM]
    
    def export_theme_config(self) -> Dict[str, Any]:
        """Tema konfigürasyonunu export et"""
        if not self.current_tokens:
            return {}
        
        return {
            'scheme': self.current_scheme.value,
            'custom_accent_color': self._custom_accent_color,
            'tokens': self.current_tokens.__dict__
        }
    
    def import_theme_config(self, config: Dict[str, Any]):
        """Tema konfigürasyonunu import et"""
        try:
            scheme_name = config.get('scheme', ColorScheme.LIGHT_PROFESSIONAL.value)
            scheme = ColorScheme(scheme_name)
            accent_color = config.get('custom_accent_color')
            
            self.apply_theme(scheme, accent_color)
            
        except (ValueError, KeyError) as e:
            self.logger.error(f"Error importing theme config: {e}")
            # Fallback to default theme
            self.apply_theme(ColorScheme.LIGHT_PROFESSIONAL)
    
    def get_menu_styles(self) -> str:
        """Menu bar stilleri"""
        if not self.current_tokens:
            return ""
        
        return f"""
        QMenuBar {{
            background-color: {self.current_tokens.surface};
            color: {self.current_tokens.text_primary};
            border: none;
            padding: {self.current_tokens.spacing.sm}px;
            font-family: {self.current_tokens.typography.body1.family};
            font-size: {self.current_tokens.typography.body1.size}px;
            font-weight: {self.current_tokens.typography.body1.weight};
        }}
        
        QMenuBar::item {{
            background-color: transparent;
            padding: {self.current_tokens.spacing.sm}px {self.current_tokens.spacing.md}px;
            border-radius: {self.current_tokens.border_radius.sm}px;
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
            border: 1px solid {self.current_tokens.divider};
            border-radius: {self.current_tokens.border_radius.md}px;
            padding: {self.current_tokens.spacing.sm}px;
        }}
        
        QMenu::item {{
            padding: {self.current_tokens.spacing.sm}px {self.current_tokens.spacing.md}px;
            border-radius: {self.current_tokens.border_radius.sm}px;
        }}
        
        QMenu::item:selected {{
            background-color: {self.current_tokens.primary}15;
            color: {self.current_tokens.primary};
        }}
        
        QMenu::separator {{
            height: 1px;
            background-color: {self.current_tokens.divider};
            margin: {self.current_tokens.spacing.xs}px {self.current_tokens.spacing.sm}px;
        }}
        """
    
    def get_toolbar_styles(self) -> str:
        """Toolbar stilleri"""
        if not self.current_tokens:
            return ""
        
        return f"""
        QToolBar {{
            background-color: {self.current_tokens.surface};
            color: {self.current_tokens.text_primary};
            border: none;
            spacing: {self.current_tokens.spacing.sm}px;
            padding: {self.current_tokens.spacing.sm}px;
        }}
        
        QToolBar::separator {{
            background-color: {self.current_tokens.divider};
            width: 1px;
            margin: {self.current_tokens.spacing.xs}px {self.current_tokens.spacing.sm}px;
        }}
        """
    
    def get_status_bar_styles(self) -> str:
        """Status bar stilleri"""
        if not self.current_tokens:
            return ""
        
        return f"""
        QStatusBar {{
            background-color: {self.current_tokens.surface};
            color: {self.current_tokens.text_secondary};
            border-top: 1px solid {self.current_tokens.divider};
            padding: {self.current_tokens.spacing.xs}px {self.current_tokens.spacing.sm}px;
            font-family: {self.current_tokens.typography.caption.family};
            font-size: {self.current_tokens.typography.caption.size}px;
        }}
        
        QStatusBar::item {{
            border: none;
        }}
        """
    
    def get_progress_bar_styles(self) -> str:
        """Progress bar stilleri"""
        if not self.current_tokens:
            return ""
        
        return f"""
        QProgressBar {{
            background-color: {self.current_tokens.background};
            border: 1px solid {self.current_tokens.divider};
            border-radius: {self.current_tokens.border_radius.sm}px;
            text-align: center;
            color: {self.current_tokens.text_primary};
            height: 20px;
        }}
        
        QProgressBar::chunk {{
            background-color: {self.current_tokens.primary};
            border-radius: {self.current_tokens.border_radius.sm}px;
        }}
        """
    
    def get_input_styles(self) -> str:
        """Input stilleri"""
        if not self.current_tokens:
            return ""
        
        return f"""
        QComboBox, QLineEdit, QSpinBox {{
            background-color: {self.current_tokens.surface};
            color: {self.current_tokens.text_primary};
            border: 1px solid {self.current_tokens.divider};
            border-radius: {self.current_tokens.border_radius.sm}px;
            padding: {self.current_tokens.spacing.sm}px;
            font-family: {self.current_tokens.typography.body1.family};
            font-size: {self.current_tokens.typography.body1.size}px;
        }}
        
        QComboBox:focus, QLineEdit:focus, QSpinBox:focus {{
            border-color: {self.current_tokens.primary};
            outline: none;
        }}
        
        QComboBox:disabled, QLineEdit:disabled, QSpinBox:disabled {{
            background-color: {self.current_tokens.background};
            color: {self.current_tokens.text_disabled};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 30px;
        }}
        
        QComboBox::down-arrow {{
            image: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M7 10l5 5 5-5z" fill="{self.current_tokens.text_secondary}"/></svg>');
            width: 12px;
            height: 12px;
        }}
        """
    
    def get_checkbox_styles(self) -> str:
        """Checkbox stilleri"""
        if not self.current_tokens:
            return ""
        
        return f"""
        QCheckBox {{
            color: {self.current_tokens.text_primary};
            font-family: {self.current_tokens.typography.body1.family};
            font-size: {self.current_tokens.typography.body1.size}px;
            spacing: {self.current_tokens.spacing.sm}px;
        }}
        
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid {self.current_tokens.divider};
            border-radius: {self.current_tokens.border_radius.xs}px;
            background-color: {self.current_tokens.surface};
        }}
        
        QCheckBox::indicator:checked {{
            background-color: {self.current_tokens.primary};
            border-color: {self.current_tokens.primary};
            image: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" fill="white"/></svg>');
        }}
        
        QCheckBox::indicator:hover {{
            border-color: {self.current_tokens.primary};
        }}
        
        QCheckBox:disabled {{
            color: {self.current_tokens.text_disabled};
        }}
        
        QCheckBox::indicator:disabled {{
            background-color: {self.current_tokens.background};
            border-color: {self.current_tokens.text_disabled};
        }}
        """
    
    def get_text_styles(self, variant: str = 'body1') -> str:
        """Metin stilleri"""
        if not self.current_tokens:
            return ""
        
        typography_map = {
            'h1': self.current_tokens.typography.h1,
            'h2': self.current_tokens.typography.h2,
            'h3': self.current_tokens.typography.h3,
            'body1': self.current_tokens.typography.body1,
            'body2': self.current_tokens.typography.body2,
            'caption': self.current_tokens.typography.caption,
            'button': self.current_tokens.typography.button
        }
        
        typo = typography_map.get(variant, self.current_tokens.typography.body1)
        
        return f"""
        font-family: {typo.family};
        font-size: {typo.size}px;
        font-weight: {typo.weight};
        color: {self.current_tokens.text_primary};
        """
