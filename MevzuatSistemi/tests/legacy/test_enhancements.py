"""
Test script - Geliştirilen özellikler için basit test
"""

import sys
import os
import logging
from pathlib import Path

# Proje root'unu path'e ekle
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """İmportları test et"""
    print("=== İmport Testleri ===")
    
    try:
        from app.utils.query_expansion import TurkishLegalQueryExpansion, LegalQueryOptimizer
        print("✅ Query Expansion modülleri başarıyla import edildi")
    except Exception as e:
        print(f"❌ Query Expansion import hatası: {e}")
    
    try:
        from app.utils.faceted_search import LegalDocumentFacetEngine, FacetedResults
        print("✅ Faceted Search modülleri başarıyla import edildi")
    except Exception as e:
        print(f"❌ Faceted Search import hatası: {e}")
    
    try:
        from app.ui.faceted_search_widget import FacetedSearchWidget
        print("✅ Faceted Search UI widget'ı başarıyla import edildi")
    except Exception as e:
        print(f"❌ Faceted Search UI import hatası: {e}")

def test_query_expansion():
    """Query expansion test et"""
    print("\n=== Query Expansion Testleri ===")
    
    try:
        # Mock config manager
        class MockConfig:
            def get(self, key, default=None):
                return default
            
            def get_base_folder(self):
                return Path.cwd()
        
        config = MockConfig()
        expansion_engine = TurkishLegalQueryExpansion(config)
        
        # Test sorguları
        test_queries = [
            "ceza",
            "mülkiyet",
            "sözleşme", 
            "TCK",
            "TMK"
        ]
        
        for query in test_queries:
            expanded = expansion_engine.expand_query(query)
            print(f"'{query}' -> {expanded}")
        
        print("✅ Query Expansion test başarılı")
        
    except Exception as e:
        print(f"❌ Query Expansion test hatası: {e}")

def test_facet_definitions():
    """Facet tanımlarını test et"""
    print("\n=== Facet Tanımları Testleri ===")
    
    try:
        # Mock database ve config
        class MockDB:
            pass
        
        class MockConfig:
            def get(self, key, default=None):
                return default
        
        db = MockDB()
        config = MockConfig()
        
        facet_engine = LegalDocumentFacetEngine(db, config)
        
        # Facet tanımlarını kontrol et
        facets = facet_engine.facet_definitions
        print(f"Toplam {len(facets)} facet tanımı:")
        
        for name, definition in facets.items():
            print(f"  - {name}: {definition['label']} ({definition['type']})")
        
        print("✅ Facet tanımları test başarılı")
        
    except Exception as e:
        print(f"❌ Facet tanımları test hatası: {e}")

def test_document_type_normalization():
    """Belge türü normalizasyonu test et"""
    print("\n=== Belge Türü Normalizasyon Testleri ===")
    
    try:
        class MockDB:
            pass
        
        class MockConfig:
            def get(self, key, default=None):
                return default
        
        facet_engine = LegalDocumentFacetEngine(MockDB(), MockConfig())
        
        test_types = [
            "5237 Sayılı Türk Ceza Kanunu",
            "Vergi Usul Kanunu Genel Tebliği",
            "Bakanlar Kurulu Kararı",
            "Cumhurbaşkanı Kararnamesi",
            "İç Tüzük",
            "Genelge (2024/5)",
            "Bazı Yönetmelik"
        ]
        
        for doc_type in test_types:
            normalized = facet_engine._normalize_document_type(doc_type)
            print(f"'{doc_type}' -> '{normalized}'")
        
        print("✅ Belge türü normalizasyonu test başarılı")
        
    except Exception as e:
        print(f"❌ Belge türü normalizasyonu test hatası: {e}")

def main():
    """Ana test fonksiyonu"""
    print("Mevzuat Sistemi - Geliştirme Önerileri Test Scripti")
    print("=" * 60)
    
    # Logging ayarla
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Testleri çalıştır
    test_imports()
    test_query_expansion()
    test_facet_definitions()
    test_document_type_normalization()
    
    print("\n" + "=" * 60)
    print("Test tamamlandı!")

if __name__ == "__main__":
    main()
