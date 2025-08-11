"""
Mevzuat Belge Analiz & Sorgulama Sistemi
Ana uygulama giriş noktası - Enhanced Version with Quality Improvements
"""

import sys
import os
from pathlib import Path

# Proje kökünü path'e ekle
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Windows terminal encoding düzeltmesi
if sys.platform.startswith('win'):
    try:
        # Terminal'i UTF-8 moduna geçir
        os.system('chcp 65001 > nul 2>&1')  # UTF-8
        # stdout encoding'i UTF-8 yap
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        elif hasattr(sys.stdout, 'buffer'):
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except:
        # Encoding değiştirilemezse, güvenli mod kullan
        pass

def safe_print(text: str, fallback_icons: dict = None):
    """
    Unicode karakterleri güvenli şekilde yazdır
    
    Args:
        text: Yazdırılacak metin
        fallback_icons: Emoji -> ASCII karşılıkları
    """
    if fallback_icons is None:
        fallback_icons = {
            '🚀': '[START]',
            '✅': '[OK]',
            '❌': '[ERROR]',
            '⚠️': '[WARNING]',
            '📂': '[FOLDER]',
            '🔧': '[CONFIG]',
            '💾': '[SAVE]',
            '🎯': '[TARGET]'
        }
    
    try:
        print(text)
    except UnicodeEncodeError:
        # Unicode karakterleri ASCII karşılıklarıyla değiştir
        safe_text = text
        for emoji, ascii_replacement in fallback_icons.items():
            safe_text = safe_text.replace(emoji, ascii_replacement)
        print(safe_text)

from enhanced_main import QualityEnhancedAppManager
from app.utils.logger import setup_logger
from app.security import SecureErrorHandler

def main():
    """Ana uygulama giriş fonksiyonu - Enhanced with quality improvements"""
    error_handler = SecureErrorHandler()
    
    try:
        safe_print("🚀 Mevzuat Sistemi v1.0.2-enhanced başlatılıyor...")
        
        # Logger'ı başlat
        logger = setup_logger("mevzuat_main")
        logger.info("Mevzuat Sistemi Enhanced başlatılıyor...")
        
        safe_print("✅ Logger başlatıldı")
        
        # Enhanced uygulama yöneticisini oluştur ve başlat
        app_manager = QualityEnhancedAppManager()
        safe_print("✅ Enhanced App Manager oluşturuldu")
        
        # Sistem sağlık kontrolü
        health_status = app_manager.health_check()
        if health_status.get('overall_status') != 'healthy':
            safe_print("⚠️  Sistem sağlık kontrolünde sorunlar tespit edildi")
            for issue in health_status.get('issues', []):
                safe_print(f"❌ {issue}")
        else:
            safe_print("✅ Sistem sağlık kontrolü başarılı")
        
        # Uygulamayı başlat
        result = app_manager.run()
        sys.exit(result if result is not None else 0)
        
    except ImportError as e:
        user_message = error_handler.handle_error(e, "IMPORT_ERROR")
        safe_print(f"❌ Modül yükleme hatası: {user_message}")
        logger.error(f"Import error: {e}")
        sys.exit(1)
        
    except PermissionError as e:
        user_message = error_handler.handle_error(e, "FILE_PERMISSION")
        safe_print(f"❌ Yetki hatası: {user_message}")
        logger.error(f"Permission error: {e}")
        sys.exit(1)
        
    except FileNotFoundError as e:
        user_message = error_handler.handle_error(e, "FILE_NOT_FOUND")
        safe_print(f"❌ Dosya bulunamadı: {user_message}")
        logger.error(f"File not found: {e}")
        sys.exit(1)
        
    except Exception as e:
        user_message = error_handler.handle_error(e, "GENERAL_ERROR")
        safe_print(f"❌ Uygulama başlatılırken hata oluştu: {user_message}")
        safe_print(f"ERROR: {e}")
        logger.error(f"Application startup error: {e}")
        import traceback
        safe_print("Full traceback:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
