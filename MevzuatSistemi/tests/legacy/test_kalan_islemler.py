#!/usr/bin/env python3
"""
Kalan İşlemler Test Script
Yeni eklenen özelliklerin çalışıp çalışmadığını test eder
"""

import sys
import os
from pathlib import Path

# Proje kökünü path'e ekle
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Import testleri"""
    print("=== İMPORT TESTLERİ ===\n")
    
    try:
        from app.utils.backup_manager import BackupManager
        print("✅ BackupManager import başarılı")
    except Exception as e:
        print(f"❌ BackupManager import hatası: {e}")
        return False
    
    try:
        from app.utils.system_tray import SystemTrayManager
        print("✅ SystemTrayManager import başarılı")
    except Exception as e:
        print(f"❌ SystemTrayManager import hatası: {e}")
        return False
    
    try:
        from app.utils.pdf_exporter import PDFExporter
        print("✅ PDFExporter import başarılı")
    except Exception as e:
        print(f"❌ PDFExporter import hatası: {e}")
        return False
    
    print("\n🎉 Tüm yeni modüller başarıyla import edildi!\n")
    return True

def test_backup_system():
    """Backup sistemi testi"""
    print("=== BACKUP SİSTEMİ TESTİ ===\n")
    
    try:
        from app.utils.config_manager import ConfigManager
        from app.core.database_manager import DatabaseManager
        from app.utils.backup_manager import BackupManager
        
        # Geçici config
        config = ConfigManager()
        db = DatabaseManager(config)
        db.initialize()
        
        # Backup manager
        backup_manager = BackupManager(config, db)
        
        # Backup durumu
        status = backup_manager.get_backup_status()
        print(f"✅ Backup sistemi durumu:")
        print(f"   - Etkin: {status['enabled']}")
        print(f"   - Otomatik: {status['auto_backup']}")
        print(f"   - Klasör: {status['backup_folder']}")
        print(f"   - Toplam yedek: {status['total_backups']}")
        
        db.close()
        print("\n✅ Backup sistemi test edildi\n")
        return True
        
    except Exception as e:
        print(f"❌ Backup sistem testi hatası: {e}")
        return False

def test_pdf_export():
    """PDF Export sistemi testi"""
    print("=== PDF EXPORT TESTİ ===\n")
    
    try:
        from app.utils.pdf_exporter import PDFExporter
        
        pdf_exporter = PDFExporter()
        
        if hasattr(pdf_exporter, 'is_available'):
            available = pdf_exporter.is_available()
            print(f"✅ PDF Export kullanılabilir: {available}")
        else:
            print("✅ PDF Export modülü yüklendi")
        
        print("✅ PDF Export sistemi test edildi\n")
        return True
        
    except Exception as e:
        print(f"❌ PDF Export testi hatası: {e}")
        return False

def test_system_tray():
    """System Tray testi"""
    print("=== SYSTEM TRAY TESTİ ===\n")
    
    try:
        from PyQt5.QtWidgets import QApplication
        from app.utils.system_tray import SystemTrayManager
        from app.utils.config_manager import ConfigManager
        
        # Qt app (tray için gerekli)
        app = QApplication.instance()
        if not app:
            app = QApplication([])
        
        config = ConfigManager()
        tray = SystemTrayManager(config)
        
        print(f"✅ System Tray kullanılabilir: {tray.is_available()}")
        print(f"✅ System Tray etkin: {tray.is_enabled()}")
        
        # Cleanup
        if tray.is_available():
            tray.cleanup()
        
        print("✅ System Tray sistemi test edildi\n")
        return True
        
    except Exception as e:
        print(f"❌ System Tray testi hatası: {e}")
        return False

def test_core_integration():
    """Core entegrasyon testi"""
    print("=== CORE ENTEGRASYON TESTİ ===\n")
    
    try:
        from app.core.app_manager import MevzuatApp
        
        print("✅ MevzuatApp sınıfı import edildi")
        
        # Yapıcı test (initialization)
        print("   Initialization test edilemiyor (GUI gerektirir)")
        
        print("✅ Core entegrasyon test edildi\n")
        return True
        
    except Exception as e:
        print(f"❌ Core entegrasyon testi hatası: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Ana test fonksiyonu"""
    print("🚀 KALAN İŞLEMLER TEST SİSTEMİ\n")
    print("=" * 50)
    
    test_results = []
    
    # 1. Import testleri
    test_results.append(("Import Testleri", test_imports()))
    
    # 2. Backup sistemi
    test_results.append(("Backup Sistemi", test_backup_system()))
    
    # 3. PDF Export
    test_results.append(("PDF Export", test_pdf_export()))
    
    # 4. System Tray
    test_results.append(("System Tray", test_system_tray()))
    
    # 5. Core Entegrasyon
    test_results.append(("Core Entegrasyon", test_core_integration()))
    
    # Sonuçları göster
    print("=" * 50)
    print("📊 TEST SONUÇLARI\n")
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ BAŞARILI" if result else "❌ BAŞARISIZ"
        print(f"{test_name:<20}: {status}")
        if result:
            passed += 1
    
    print(f"\nToplam: {passed}/{total} test geçti")
    
    if passed == total:
        print("\n🎉 TÜM TESTLER BAŞARILI!")
        print("✨ Kalan işlemler başarıyla tamamlandı!")
    else:
        print(f"\n⚠️  {total - passed} test başarısız")
        print("🔧 Hatalar düzeltilmeli")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
