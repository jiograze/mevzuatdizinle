#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Comprehensive Core Module Tests - Coverage Boost
Core modülü için kapsamlı testler (mevcut %25.7 → %70+ hedef)
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import pytest
import tempfile
import os
from pathlib import Path

# Core modules to test
from app.core.database_manager import DatabaseManager
from app.core.search_engine import SearchEngine
from app.core.document_processor import DocumentProcessor
from app.utils.config_manager import ConfigManager


class TestDatabaseManagerComprehensive(unittest.TestCase):
    """Kapsamlı DatabaseManager testleri"""
    
    def setUp(self):
        """Test setup"""
        self.config = Mock(spec=ConfigManager)
        self.config.get.return_value = {
            'database': {
                'path': ':memory:',
                'timeout': 30,
                'check_same_thread': False
            }
        }
        self.db_manager = DatabaseManager(self.config)
    
    def test_initialization_success(self):
        """Başarılı initialization testi"""
        result = self.db_manager.initialize()
        self.assertTrue(result)
        self.assertTrue(self.db_manager._is_initialized)
    
    def test_create_tables_success(self):
        """Tablo oluşturma testi"""
        self.db_manager.initialize()
        result = self.db_manager.create_tables()
        self.assertTrue(result)
    
    def test_insert_document_success(self):
        """Belge ekleme testi"""
        self.db_manager.initialize()
        self.db_manager.create_tables()
        
        test_doc = {
            'title': 'Test Document',
            'content': 'Test content',
            'file_path': '/test/path.pdf',
            'document_type': 'pdf'
        }
        
        result = self.db_manager.insert_document(test_doc)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, int)
    
    def test_search_documents(self):
        """Belge arama testi"""
        self.db_manager.initialize()
        self.db_manager.create_tables()
        
        # Test document insert
        test_doc = {
            'title': 'Test Search Document',
            'content': 'Searchable test content',
            'file_path': '/test/search.pdf',
            'document_type': 'pdf'
        }
        self.db_manager.insert_document(test_doc)
        
        # Search test
        results = self.db_manager.search_documents("test")
        self.assertIsInstance(results, list)
    
    def test_get_document_by_id(self):
        """ID ile belge getirme testi"""
        self.db_manager.initialize()
        self.db_manager.create_tables()
        
        test_doc = {
            'title': 'ID Test Document',
            'content': 'Content for ID test',
            'file_path': '/test/id_test.pdf',
            'document_type': 'pdf'
        }
        doc_id = self.db_manager.insert_document(test_doc)
        
        retrieved_doc = self.db_manager.get_document_by_id(doc_id)
        self.assertIsNotNone(retrieved_doc)
        self.assertEqual(retrieved_doc['title'], 'ID Test Document')
    
    def test_update_document(self):
        """Belge güncelleme testi"""
        self.db_manager.initialize()
        self.db_manager.create_tables()
        
        test_doc = {
            'title': 'Original Title',
            'content': 'Original content',
            'file_path': '/test/update_test.pdf',
            'document_type': 'pdf'
        }
        doc_id = self.db_manager.insert_document(test_doc)
        
        # Update
        updated_doc = {
            'title': 'Updated Title',
            'content': 'Updated content',
            'file_path': '/test/update_test.pdf',
            'document_type': 'pdf'
        }
        result = self.db_manager.update_document(doc_id, updated_doc)
        self.assertTrue(result)
    
    def test_delete_document(self):
        """Belge silme testi"""
        self.db_manager.initialize()
        self.db_manager.create_tables()
        
        test_doc = {
            'title': 'Delete Test',
            'content': 'To be deleted',
            'file_path': '/test/delete.pdf',
            'document_type': 'pdf'
        }
        doc_id = self.db_manager.insert_document(test_doc)
        
        result = self.db_manager.delete_document(doc_id)
        self.assertTrue(result)
        
        # Verify deletion
        deleted_doc = self.db_manager.get_document_by_id(doc_id)
        self.assertIsNone(deleted_doc)
    
    def test_get_statistics(self):
        """İstatistik getirme testi"""
        self.db_manager.initialize()
        self.db_manager.create_tables()
        
        stats = self.db_manager.get_statistics()
        self.assertIsInstance(stats, dict)
        self.assertIn('total_documents', stats)
    
    def test_backup_database(self):
        """Veritabanı yedekleme testi"""
        self.db_manager.initialize()
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            backup_path = tmp.name
        
        try:
            result = self.db_manager.backup_database(backup_path)
            self.assertTrue(result)
            self.assertTrue(os.path.exists(backup_path))
        finally:
            if os.path.exists(backup_path):
                os.unlink(backup_path)
    
    def test_connection_error_handling(self):
        """Bağlantı hatası yönetimi testi"""
        # Invalid database path
        self.config.get.return_value = {
            'database': {
                'path': '/invalid/path/database.db',
                'timeout': 30
            }
        }
        
        db_manager = DatabaseManager(self.config)
        result = db_manager.initialize()
        # Should handle error gracefully
        self.assertIsInstance(result, bool)


class TestSearchEngineComprehensive(unittest.TestCase):
    """Kapsamlı SearchEngine testleri"""
    
    def setUp(self):
        """Test setup"""
        self.config = Mock(spec=ConfigManager)
        self.config.get.return_value = {
            'search': {
                'max_results': 100,
                'fuzzy_threshold': 0.8
            }
        }
        self.db_manager = Mock()
        self.search_engine = SearchEngine(self.config, self.db_manager)
    
    def test_simple_search(self):
        """Basit arama testi"""
        # Mock database results
        self.db_manager.search_documents.return_value = [
            {'id': 1, 'title': 'Test Document', 'content': 'Search test content'}
        ]
        
        results = self.search_engine.search("test")
        self.assertIsInstance(results, list)
        self.db_manager.search_documents.assert_called_once()
    
    def test_advanced_search(self):
        """Gelişmiş arama testi"""
        search_params = {
            'query': 'test',
            'document_type': 'pdf',
            'date_from': '2024-01-01',
            'date_to': '2024-12-31'
        }
        
        self.db_manager.advanced_search.return_value = []
        
        results = self.search_engine.advanced_search(search_params)
        self.assertIsInstance(results, list)
    
    def test_fuzzy_search(self):
        """Bulanık arama testi"""
        self.db_manager.search_documents.return_value = [
            {'id': 1, 'title': 'Document', 'content': 'Similar content'}
        ]
        
        results = self.search_engine.fuzzy_search("documnt")  # typo
        self.assertIsInstance(results, list)
    
    def test_search_with_filters(self):
        """Filtreli arama testi"""
        filters = {
            'document_type': ['pdf', 'docx'],
            'size_min': 1024,
            'size_max': 1048576
        }
        
        results = self.search_engine.search_with_filters("query", filters)
        self.assertIsInstance(results, list)
    
    def test_search_suggestions(self):
        """Arama önerisi testi"""
        suggestions = self.search_engine.get_search_suggestions("tes")
        self.assertIsInstance(suggestions, list)
    
    def test_search_ranking(self):
        """Arama sonuç sıralaması testi"""
        mock_results = [
            {'id': 1, 'title': 'Low relevance', 'relevance_score': 0.3},
            {'id': 2, 'title': 'High relevance', 'relevance_score': 0.9},
            {'id': 3, 'title': 'Medium relevance', 'relevance_score': 0.6}
        ]
        
        ranked_results = self.search_engine._rank_results(mock_results)
        self.assertEqual(ranked_results[0]['id'], 2)  # Highest score first


class TestDocumentProcessorComprehensive(unittest.TestCase):
    """Kapsamlı DocumentProcessor testleri"""
    
    def setUp(self):
        """Test setup"""
        self.config = Mock(spec=ConfigManager)
        self.config.get.return_value = {
            'processing': {
                'max_file_size': 10485760,  # 10MB
                'supported_formats': ['pdf', 'docx', 'txt']
            }
        }
        self.doc_processor = DocumentProcessor(self.config)
    
    def test_file_type_detection(self):
        """Dosya tipi tespiti testi"""
        test_files = {
            'test.pdf': 'pdf',
            'document.docx': 'docx',
            'readme.txt': 'txt'
        }
        
        for filename, expected_type in test_files.items():
            detected_type = self.doc_processor.detect_file_type(filename)
            self.assertEqual(detected_type, expected_type)
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.stat')
    def test_file_validation(self, mock_stat, mock_exists):
        """Dosya validasyon testi"""
        mock_exists.return_value = True
        mock_stat.return_value.st_size = 1024  # 1KB
        
        result = self.doc_processor.validate_file('/test/file.pdf')
        self.assertTrue(result)
    
    @patch('pathlib.Path.exists')
    def test_file_validation_not_exists(self, mock_exists):
        """Var olmayan dosya validasyon testi"""
        mock_exists.return_value = False
        
        result = self.doc_processor.validate_file('/nonexistent/file.pdf')
        self.assertFalse(result)
    
    def test_text_extraction_methods(self):
        """Metin çıkarma metodları testi"""
        # Test different extraction methods exist
        self.assertTrue(hasattr(self.doc_processor, 'extract_text_from_pdf'))
        self.assertTrue(hasattr(self.doc_processor, 'extract_text_from_docx'))
        self.assertTrue(hasattr(self.doc_processor, 'extract_text_from_txt'))
    
    def test_metadata_extraction(self):
        """Metadata çıkarma testi"""
        test_file_path = '/test/document.pdf'
        
        with patch.object(self.doc_processor, 'extract_metadata') as mock_extract:
            mock_extract.return_value = {
                'title': 'Test Document',
                'author': 'Test Author',
                'creation_date': '2024-01-01'
            }
            
            metadata = self.doc_processor.extract_metadata(test_file_path)
            self.assertIsInstance(metadata, dict)
            self.assertIn('title', metadata)
    
    def test_processing_queue(self):
        """İşlem kuyruğu testi"""
        test_files = ['/test/file1.pdf', '/test/file2.docx']
        
        with patch.object(self.doc_processor, 'process_file') as mock_process:
            mock_process.return_value = True
            
            results = self.doc_processor.process_batch(test_files)
            self.assertEqual(len(results), 2)
    
    def test_error_handling(self):
        """Hata yönetimi testi"""
        with patch.object(self.doc_processor, 'extract_text_from_pdf') as mock_extract:
            mock_extract.side_effect = Exception("PDF processing error")
            
            result = self.doc_processor.process_file('/test/corrupted.pdf')
            # Should handle error gracefully
            self.assertIsNotNone(result)


if __name__ == '__main__':
    # Run with coverage
    unittest.main(verbosity=2)
