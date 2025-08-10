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

from enhanced_main import QualityEnhancedAppManager
from app.utils.logger import setup_logger
from app.security import SecureErrorHandler

def main():
    """Ana uygulama giriş fonksiyonu - Enhanced with quality improvements"""
    error_handler = SecureErrorHandler()
    
    try:
        print("🚀 Mevzuat Sistemi v1.0.2-enhanced başlatılıyor...")
        
        # Logger'ı başlat
        logger = setup_logger("mevzuat_main")
        logger.info("Mevzuat Sistemi Enhanced başlatılıyor...")
        
        print("✅ Logger başlatıldı")
        
        # Enhanced uygulama yöneticisini oluştur ve başlat
        app_manager = QualityEnhancedAppManager()
        print("✅ Enhanced App Manager oluşturuldu")
        
        # Sistem sağlık kontrolü
        health_status = app_manager.perform_health_check()
        if health_status.get('overall_health', 0) < 0.5:
            print("⚠️  Sistem sağlık kontrolünde sorunlar tespit edildi")
            for component, status in health_status.get('component_health', {}).items():
                if not status:
                    print(f"❌ {component}: Çalışmıyor")
        else:
            print("✅ Sistem sağlık kontrolü başarılı")
        
        # Uygulamayı başlat
        app_manager.run()
        
    except ImportError as e:
        user_message = error_handler.get_user_friendly_message(e, "IMPORT_ERROR")
        print(f"❌ Modül yükleme hatası: {user_message}")
        logger.error(f"Import error: {e}")
        sys.exit(1)
        
    except PermissionError as e:
        user_message = error_handler.get_user_friendly_message(e, "FILE_PERMISSION")
        print(f"❌ Yetki hatası: {user_message}")
        logger.error(f"Permission error: {e}")
        sys.exit(1)
        
    except FileNotFoundError as e:
        user_message = error_handler.get_user_friendly_message(e, "FILE_NOT_FOUND")
        print(f"❌ Dosya bulunamadı: {user_message}")
        logger.error(f"File not found: {e}")
        sys.exit(1)
        
    except Exception as e:
        user_message = error_handler.get_user_friendly_message(e, "GENERAL_ERROR")
        print(f"❌ Uygulama başlatılırken hata oluştu: {user_message}")
        logger.error(f"Application startup error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
