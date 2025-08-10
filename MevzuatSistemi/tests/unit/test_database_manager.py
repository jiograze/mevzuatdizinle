#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DatabaseManager unit testleri
"""

import pytest
import sqlite3
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import sys
sys.path.append(str(Path(__file__).parents[2]))

from app.core.database_manager import DatabaseManager


class TestDatabaseManager:
    """DatabaseManager sınıfı testleri"""
    
    def test_initialization(self, mock_config, temp_db):
        """Veritabanı başlatma testi"""
        mock_config.get_db_path.return_value = temp_db
        mock_config.get.return_value = "WAL"
        
        db = DatabaseManager(mock_config)
        db.initialize()
        
        # Bağlantı kurulduğunu kontrol et
        assert db.connection is not None
        assert db.db_path == temp_db
        
        # Tabloların oluşturulduğunu kontrol et
        cursor = db.connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        
        expected_tables = ['documents', 'articles', 'article_vectors']
        for table in expected_tables:
            assert table in tables
        
        db.close()
    
    def test_add_document_success(self, mock_config, temp_db, sample_document_data):
        """Belge ekleme başarılı test"""
        mock_config.get_db_path.return_value = temp_db
        mock_config.get.return_value = "WAL"
        
        db = DatabaseManager(mock_config)
        db.initialize()
        
        doc_id = db.add_document(sample_document_data)
        
        # Belgenin eklendiğini kontrol et
        assert doc_id is not None
        assert doc_id > 0
        
        # Veritabanından belgeyi getir
        document = db.get_document(doc_id)
        assert document is not None
        assert document.title == sample_document_data['title']
        assert document.law_number == sample_document_data['law_number']
        
        db.close()
    
    def test_add_document_duplicate_hash(self, mock_config, temp_db, sample_document_data):
        """Aynı hash'e sahip belge ekleme testi"""
        mock_config.get_db_path.return_value = temp_db
        mock_config.get.return_value = "WAL"
        
        db = DatabaseManager(mock_config)
        db.initialize()
        
        # İlk belgeyi ekle
        doc_id1 = db.add_document(sample_document_data)
        assert doc_id1 is not None
        
        # Aynı hash'e sahip ikinci belgeyi ekle (hata bekleniyor)
        with pytest.raises((sqlite3.IntegrityError, Exception)):
            db.add_document(sample_document_data)
        
        db.close()
    
    def test_get_document_not_found(self, mock_config, temp_db):
        """Var olmayan belge getirme testi"""
        mock_config.get_db_path.return_value = temp_db
        mock_config.get.return_value = "WAL"
        
        db = DatabaseManager(mock_config)
        db.initialize()
        
        document = db.get_document(999)
        assert document is None
        
        db.close()
    
    def test_update_document(self, mock_config, temp_db, sample_document_data):
        """Belge güncelleme testi"""
        mock_config.get_db_path.return_value = temp_db
        mock_config.get.return_value = "WAL"
        
        db = DatabaseManager(mock_config)
        db.initialize()
        
        # Belge ekle
        doc_id = db.add_document(sample_document_data)
        
        # Güncelleme verisi
        update_data = {
            "title": "Güncellenmiş Test Kanunu",
            "category": "Mali"
        }
        
        result = db.update_document(doc_id, update_data)
        assert result is True
        
        # Güncellenmiş belgeyi kontrol et
        document = db.get_document(doc_id)
        assert document.title == update_data['title']
        assert document.category == update_data['category']
        
        db.close()
    
    def test_delete_document(self, mock_config, temp_db, sample_document_data):
        """Belge silme testi"""
        mock_config.get_db_path.return_value = temp_db
        mock_config.get.return_value = "WAL"
        
        db = DatabaseManager(mock_config)
        db.initialize()
        
        # Belge ekle
        doc_id = db.add_document(sample_document_data)
        
        # Belgenin var olduğunu kontrol et
        document = db.get_document(doc_id)
        assert document is not None
        
        # Belgeyi sil
        result = db.delete_document(doc_id)
        assert result is True
        
        # Belgenin silindiğini kontrol et
        document = db.get_document(doc_id)
        assert document is None
        
        db.close()
    
    def test_add_article(self, mock_config, temp_db, sample_document_data, sample_article_data):
        """Makale ekleme testi"""
        mock_config.get_db_path.return_value = temp_db
        mock_config.get.return_value = "WAL"
        
        db = DatabaseManager(mock_config)
        db.initialize()
        
        # Önce belge ekle
        doc_id = db.add_document(sample_document_data)
        sample_article_data['document_id'] = doc_id
        
        # Makale ekle
        article_id = db.add_article(sample_article_data)
        
        assert article_id is not None
        assert article_id > 0
        
        # Makaleyi kontrol et
        cursor = db.connection.cursor()
        cursor.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
        article = cursor.fetchone()
        cursor.close()
        
        assert article is not None
        assert article[1] == doc_id  # document_id
        assert article[2] == sample_article_data['article_number']
        
        db.close()
    
    def test_search_documents_by_title(self, mock_config, temp_db, sample_document_data):
        """Başlığa göre belge arama testi"""
        mock_config.get_db_path.return_value = temp_db
        mock_config.get.return_value = "WAL"
        
        db = DatabaseManager(mock_config)
        db.initialize()
        
        # Test belgeleri ekle
        doc1_data = sample_document_data.copy()
        doc1_data['title'] = "Vergi Kanunu"
        doc1_data['file_hash'] = "hash1"
        
        doc2_data = sample_document_data.copy()
        doc2_data['title'] = "Ceza Kanunu"
        doc2_data['file_hash'] = "hash2"
        
        db.add_document(doc1_data)
        db.add_document(doc2_data)
        
        # Arama yap
        results = db.search_documents_by_title("Vergi")
        
        assert len(results) >= 1
        assert any("Vergi" in doc.title for doc in results)
        
        db.close()
    
    def test_get_document_statistics(self, mock_config, temp_db, sample_document_data):
        """Belge istatistikleri testi"""
        mock_config.get_db_path.return_value = temp_db
        mock_config.get.return_value = "WAL"
        
        db = DatabaseManager(mock_config)
        db.initialize()
        
        # Test belgeleri ekle
        doc1_data = sample_document_data.copy()
        doc1_data['document_type'] = "KANUN"
        doc1_data['file_hash'] = "hash1"
        
        doc2_data = sample_document_data.copy()
        doc2_data['document_type'] = "YÖNETMELIK"
        doc2_data['file_hash'] = "hash2"
        
        db.add_document(doc1_data)
        db.add_document(doc2_data)
        
        # İstatistikleri al
        stats = db.get_document_statistics()
        
        assert stats is not None
        assert stats['total_documents'] >= 2
        assert 'document_types' in stats
        assert stats['document_types']['KANUN'] >= 1
        assert stats['document_types']['YÖNETMELIK'] >= 1
        
        db.close()
    
    def test_database_connection_error(self, mock_config):
        """Veritabanı bağlantı hatası testi"""
        # Geçersiz yol
        mock_config.get_db_path.return_value = Path("/invalid/path/db.sqlite")
        mock_config.get.return_value = "WAL"
        
        db = DatabaseManager(mock_config)
        
        # Hata bekleniyor
        with pytest.raises(Exception):
            db.initialize()
    
    def test_database_configuration(self, mock_config, temp_db):
        """Veritabanı konfigürasyon testi"""
        mock_config.get_db_path.return_value = temp_db
        mock_config.get.return_value = "MEMORY"  # Farklı journal mode
        
        db = DatabaseManager(mock_config)
        db.initialize()
        
        # Konfigürasyon ayarlarını kontrol et
        cursor = db.connection.cursor()
        cursor.execute("PRAGMA journal_mode")
        journal_mode = cursor.fetchone()[0]
        
        cursor.execute("PRAGMA foreign_keys")
        foreign_keys = cursor.fetchone()[0]
        
        cursor.close()
        
        assert journal_mode == "memory"
        assert foreign_keys == 1
        
        db.close()
    
    @pytest.mark.slow
    def test_large_batch_operations(self, mock_config, temp_db):
        """Büyük toplu işlemler testi"""
        mock_config.get_db_path.return_value = temp_db
        mock_config.get.return_value = "WAL"
        
        db = DatabaseManager(mock_config)
        db.initialize()
        
        # Çok sayıda belge oluştur
        documents = []
        for i in range(100):
            doc_data = {
                "title": f"Test Kanunu {i}",
                "law_number": f"TEST-{i:03d}",
                "document_type": "KANUN",
                "category": "Test",
                "file_path": f"/test/path/test_{i}.pdf",
                "file_hash": f"test_hash_{i}"
            }
            documents.append(doc_data)
        
        # Toplu ekleme
        start_time = time.time()
        for doc_data in documents:
            db.add_document(doc_data)
        end_time = time.time()
        
        # Performans kontrolü (100 belge 5 saniyeden az sürmeli)
        elapsed = end_time - start_time
        assert elapsed < 5.0
        
        # Toplam belge sayısını kontrol et
        stats = db.get_document_statistics()
        assert stats['total_documents'] >= 100
        
        db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
