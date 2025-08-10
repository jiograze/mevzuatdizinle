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
        health_status = app_manager.health_check()
        if health_status.get('overall_status') != 'healthy':
            print("⚠️  Sistem sağlık kontrolünde sorunlar tespit edildi")
            for issue in health_status.get('issues', []):
                print(f"❌ {issue}")
        else:
            print("✅ Sistem sağlık kontrolü başarılı")
        
        # Uygulamayı başlat
        result = app_manager.run()
        sys.exit(result if result is not None else 0)
        
    except ImportError as e:
        user_message = error_handler.handle_error(e, "IMPORT_ERROR")
        print(f"❌ Modül yükleme hatası: {user_message}")
        logger.error(f"Import error: {e}")
        sys.exit(1)
        
    except PermissionError as e:
        user_message = error_handler.handle_error(e, "FILE_PERMISSION")
        print(f"❌ Yetki hatası: {user_message}")
        logger.error(f"Permission error: {e}")
        sys.exit(1)
        
    except FileNotFoundError as e:
        user_message = error_handler.handle_error(e, "FILE_NOT_FOUND")
        print(f"❌ Dosya bulunamadı: {user_message}")
        logger.error(f"File not found: {e}")
        sys.exit(1)
        
    except Exception as e:
        user_message = error_handler.handle_error(e, "GENERAL_ERROR")
        print(f"❌ Uygulama başlatılırken hata oluştu: {user_message}")
        print(f"ERROR: {e}")
        logger.error(f"Application startup error: {e}")
        import traceback
        print("Full traceback:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
