#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Belge işleme entegrasyon testleri - Database + DocumentProcessor + SearchEngine
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

import sys
sys.path.append(str(Path(__file__).parents[2]))

from app.core.database_manager import DatabaseManager
from app.core.document_processor import DocumentProcessor
from app.core.search_engine import SearchEngine
from app.utils.config_manager import ConfigManager


@pytest.mark.integration
class TestDocumentProcessingFlow:
    """Belge işleme akışı entegrasyon testleri"""
    
    @pytest.fixture
    def temp_folder(self):
        """Geçici test klasörü"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def integration_config(self, temp_folder):
        """Entegrasyon testi için config"""
        config_data = {
            'base_folder': str(temp_folder),
            'database': {'name': 'test_integration.db'},
            'search': {
                'max_results': 20,
                'semantic_enabled': False  # Integration testlerde basit tutuyoruz
            },
            'document_processing': {
                'supported_formats': ['.txt', '.pdf'],
                'max_file_size_mb': 50
            }
        }
        
        config_file = temp_folder / 'config.yaml'
        import yaml
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f)
        
        config = ConfigManager(str(config_file))
        return config
    
    def test_complete_document_lifecycle(self, integration_config, temp_folder):
        """Tam belge yaşam döngüsü testi"""
        
        # 1. Bileşenleri başlat
        db = DatabaseManager(integration_config)
        db.initialize()
        
        processor = DocumentProcessor(integration_config, db)
        search_engine = SearchEngine(integration_config, db)
        
        try:
            # 2. Test belge dosyası oluştur
            test_doc = temp_folder / "test_kanunu.txt"
            test_content = """
            TEST KANUNU
            Kanun No: 2025/001
            
            MADDE 1 - (Amaç)
            Bu Kanunun amacı, test işlemlerinin düzenlenmesidir.
            
            MADDE 2 - (Kapsam)  
            Bu Kanun, tüm test uygulamalarını kapsar.
            """
            
            with open(test_doc, 'w', encoding='utf-8') as f:
                f.write(test_content)
            
            # 3. Belgeyi işle
            result = processor.process_file(str(test_doc))
            assert result is True
            
            # 4. Database'de belgenin olduğunu kontrol et
            docs = db.search_documents_by_title("TEST KANUNU")
            assert len(docs) > 0
            
            document = docs[0]
            assert "TEST KANUNU" in document.title
            assert document.document_type in ["KANUN", "TXT"]
            
            # 5. Arama testleri
            # Başlık araması
            search_results = search_engine.search("TEST KANUNU")
            assert len(search_results) > 0
            assert any("TEST KANUNU" in result.document_title for result in search_results)
            
            # İçerik araması
            content_results = search_engine.search("test işlemleri")
            assert len(content_results) > 0
            
            # Madde araması
            article_results = search_engine.search("MADDE 1")
            assert len(article_results) > 0
            
            # 6. Belge güncelleme
            update_data = {
                'title': 'Güncellenmiş Test Kanunu',
                'category': 'Test Kategorisi'
            }
            
            update_result = db.update_document(document.id, update_data)
            assert update_result is True
            
            # Güncellenmiş verilerle arama
            updated_results = search_engine.search("Güncellenmiş")
            assert len(updated_results) > 0
            
            # 7. Belge silme
            delete_result = db.delete_document(document.id)
            assert delete_result is True
            
            # Silinen belgenin aranamaması
            deleted_search = search_engine.search("TEST KANUNU")
            assert len(deleted_search) == 0
            
        finally:
            db.close()
    
    def test_multiple_documents_processing(self, integration_config, temp_folder):
        """Çoklu belge işleme testi"""
        
        db = DatabaseManager(integration_config)
        db.initialize()
        
        processor = DocumentProcessor(integration_config, db)
        search_engine = SearchEngine(integration_config, db)
        
        try:
            # Çoklu test belgeleri oluştur
            test_docs = []
            
            for i in range(3):
                doc_path = temp_folder / f"test_doc_{i}.txt"
                doc_content = f"""
                Test Belgesi {i+1}
                
                MADDE 1 - Bu belge {i+1}. test belgesidir.
                MADDE 2 - İçerik numarası: {i+1}
                """
                
                with open(doc_path, 'w', encoding='utf-8') as f:
                    f.write(doc_content)
                
                test_docs.append(str(doc_path))
            
            # Tüm belgeleri işle
            processed_count = 0
            for doc_path in test_docs:
                if processor.process_file(doc_path):
                    processed_count += 1
            
            assert processed_count == 3
            
            # Database'de 3 belgenin olduğunu kontrol et
            all_docs = db.search_documents_by_title("")  # Boş arama = tüm belgeler
            assert len(all_docs) >= 3
            
            # Her belgeyi ayrı ayrı ara
            for i in range(3):
                results = search_engine.search(f"Test Belgesi {i+1}")
                assert len(results) > 0
                assert any(f"Test Belgesi {i+1}" in result.document_title for result in results)
            
            # Ortak terimle arama
            common_results = search_engine.search("MADDE 1")
            assert len(common_results) >= 3  # Üç belgede de MADDE 1 var
            
        finally:
            db.close()
    
    def test_search_performance_with_data(self, integration_config, temp_folder):
        """Veri ile arama performansı testi"""
        
        db = DatabaseManager(integration_config) 
        db.initialize()
        
        processor = DocumentProcessor(integration_config, db)
        search_engine = SearchEngine(integration_config, db)
        
        try:
            # Performance test için daha fazla belge oluştur
            import time
            
            doc_count = 10
            terms = ["vergi", "ceza", "idare", "mülkiyet", "borç"]
            
            # Belgeleri oluştur ve işle
            start_time = time.time()
            
            for i in range(doc_count):
                term = terms[i % len(terms)]
                doc_path = temp_folder / f"perf_test_{i}.txt"
                
                doc_content = f"""
                {term.upper()} KANUNU {i+1}
                
                MADDE 1 - {term} ile ilgili düzenlemeler
                MADDE 2 - {term} kapsamındaki işlemler  
                MADDE 3 - Bu kanun {term} alanında uygulanır
                """
                
                with open(doc_path, 'w', encoding='utf-8') as f:
                    f.write(doc_content)
                
                processor.process_file(str(doc_path))
            
            processing_time = time.time() - start_time
            
            # Performance: 10 belge 5 saniyeden az sürmeli
            assert processing_time < 5.0
            
            # Arama performance testi
            search_start = time.time()
            
            for term in terms:
                results = search_engine.search(term)
                assert len(results) >= 2  # Her term en az 2 belgede var
            
            search_time = time.time() - search_start
            
            # 5 arama 1 saniyeden az sürmeli
            assert search_time < 1.0
            
            # Stats kontrolü
            stats = search_engine.get_performance_stats()
            assert stats['total_searches'] >= 5
            assert stats['average_execution_time_ms'] < 200  # 200ms'den az
            
        finally:
            db.close()
    
    def test_error_recovery_integration(self, integration_config, temp_folder):
        """Hata kurtarma entegrasyon testi"""
        
        db = DatabaseManager(integration_config)
        db.initialize()
        
        processor = DocumentProcessor(integration_config, db)
        search_engine = SearchEngine(integration_config, db)
        
        try:
            # 1. Geçerli belge işle
            valid_doc = temp_folder / "valid.txt"
            with open(valid_doc, 'w', encoding='utf-8') as f:
                f.write("Geçerli belge içeriği")
            
            result = processor.process_file(str(valid_doc))
            assert result is True
            
            # 2. Geçersiz belge ile hata durumunu test et
            invalid_doc = temp_folder / "invalid.txt"
            with open(invalid_doc, 'wb') as f:
                f.write(b'\x00\x01\x02\x03')  # Binary garbage
            
            # Hata durumunda sistem çökmemeli
            invalid_result = processor.process_file(str(invalid_doc))
            # Hata durumunda False dönmeli veya exception handle etmeli
            
            # 3. Geçerli belgenin hala aranabildiğini kontrol et
            results = search_engine.search("Geçerli")
            assert len(results) > 0
            
            # 4. Database bütünlüğü kontrolü
            docs = db.search_documents_by_title("")
            assert len(docs) >= 1  # En az geçerli belge olmalı
            
        finally:
            db.close()
    
    @pytest.mark.slow
    def test_large_document_processing(self, integration_config, temp_folder):
        """Büyük belge işleme testi"""
        
        db = DatabaseManager(integration_config)
        db.initialize()
        
        processor = DocumentProcessor(integration_config, db)
        search_engine = SearchEngine(integration_config, db)
        
        try:
            # Büyük test belge oluştur (~100KB)
            large_doc = temp_folder / "large_doc.txt"
            
            content_parts = []
            content_parts.append("BÜYÜK TEST KANUNU\n\n")
            
            # 1000 madde ekle
            for i in range(1, 1001):
                article = f"MADDE {i} - Bu {i}. maddedir. "
                article += f"Bu madde büyük belge testi için oluşturulmuştur. " * 5
                article += "\n\n"
                content_parts.append(article)
            
            large_content = "".join(content_parts)
            
            with open(large_doc, 'w', encoding='utf-8') as f:
                f.write(large_content)
            
            # Dosya boyutunu kontrol et
            file_size = large_doc.stat().st_size
            assert file_size > 50000  # En az 50KB
            
            # Büyük belgeyi işle
            import time
            start_time = time.time()
            
            result = processor.process_file(str(large_doc))
            
            processing_time = time.time() - start_time
            
            assert result is True
            
            # Performance: büyük belge 10 saniyeden az sürmeli
            assert processing_time < 10.0
            
            # Database'de belgenin işlendiğini kontrol et
            docs = db.search_documents_by_title("BÜYÜK TEST")
            assert len(docs) > 0
            
            # Büyük belgede arama
            search_results = search_engine.search("MADDE 500")
            assert len(search_results) > 0
            
            # Memory kontrolü (eğer psutil varsa)
            try:
                import psutil
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                
                # 500MB'dan az memory kullanmalı
                assert memory_mb < 500
            except ImportError:
                pass  # psutil yoksa skip
            
        finally:
            db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
