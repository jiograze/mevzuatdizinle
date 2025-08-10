"""
Basit test - sadece import testleri
"""

import sys
from pathlib import Path

# Proje root'unu path'e ekle
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=== İmport Testleri ===")

# Test 1: Query Expansion
try:
    from app.utils.query_expansion import TurkishLegalQueryExpansion, LegalQueryOptimizer
    print("✅ Query Expansion modülleri başarıyla import edildi")
except Exception as e:
    print(f"❌ Query Expansion import hatası: {e}")

# Test 2: Faceted Search
try:
    from app.utils.faceted_search import LegalDocumentFacetEngine, FacetedResults
    print("✅ Faceted Search modülleri başarıyla import edildi")
except Exception as e:
    print(f"❌ Faceted Search import hatası: {e}")

# Test 3: Faceted Search Widget - PyQt5 olmayabilir
try:
    from app.ui.faceted_search_widget import FacetedSearchWidget
    print("✅ Faceted Search UI widget'ı başarıyla import edildi")
except Exception as e:
    print(f"❌ Faceted Search UI import hatası: {e}")

# Test 4: Search Engine Integration
try:
    from app.core.search_engine import SearchEngine
    print("✅ Enhanced Search Engine başarıyla import edildi")
except Exception as e:
    print(f"❌ Search Engine import hatası: {e}")

print("\n=== Temel İşlevsellik Testleri ===")

# Test 5: Query Expansion basic test
try:
    class MockConfig:
        def get(self, key, default=None):
            return default
        def get_base_folder(self):
            return Path.cwd()
    
    config = MockConfig()
    expansion_engine = TurkishLegalQueryExpansion(config)
    
    # Test query
    expanded = expansion_engine.expand_query("ceza")
    print(f"✅ Query Expansion test: 'ceza' -> {len(expanded)} terim")
    
except Exception as e:
    print(f"❌ Query Expansion test hatası: {e}")

print("\nTest tamamlandı!")
