#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Pytest konfigürasyon ve fixture'lar
"""

import pytest
import sqlite3
import tempfile
import shutil
import logging
from pathlib import Path
from unittest.mock import Mock, MagicMock

# PyQt5 için pytest-qt setup
pytest_plugins = ["pytestqt"]

# Test için logging seviyesini ayarla
logging.basicConfig(level=logging.DEBUG)

@pytest.fixture(scope="session")
def test_data_dir():
    """Test veri klasörü"""
    return Path(__file__).parent / "test_data"

@pytest.fixture(scope="function")
def temp_db():
    """Her test için geçici veritabanı"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)
    
    yield db_path
    
    # Cleanup
    if db_path.exists():
        db_path.unlink()

@pytest.fixture(scope="function") 
def mock_config():
    """Mock konfigürasyon yöneticisi"""
    config = MagicMock()
    config.get.return_value = "test_value"
    config.get_db_path.return_value = Path("test.db")
    config.get_base_folder.return_value = Path("test_folder")
    return config

@pytest.fixture(scope="function")
def sample_document_data():
    """Örnek belge verisi"""
    return {
        "title": "Test Kanunu",
        "law_number": "TEST-001",
        "document_type": "KANUN",
        "category": "İdari",
        "content": "Bu bir test kanunudur. Madde 1: Test hükümleri.",
        "file_path": "/test/path/test.pdf",
        "file_hash": "test_hash_123"
    }

@pytest.fixture(scope="function")
def sample_article_data():
    """Örnek makale verisi"""
    return {
        "document_id": 1,
        "article_number": "1",
        "title": "Test Maddesi",
        "content": "Bu bir test maddesidir.",
        "article_type": "MADDE"
    }

@pytest.fixture(scope="function")
def mock_search_engine():
    """Mock arama motoru"""
    engine = MagicMock()
    engine.search.return_value = []
    engine.get_suggestions.return_value = ["test", "örnek"]
    return engine

@pytest.fixture(scope="function")
def mock_document_processor():
    """Mock belge işleyici"""
    processor = MagicMock()
    processor.process_file.return_value = True
    processor.extract_text.return_value = "Test içeriği"
    return processor

@pytest.fixture(scope="function")
def mock_file_watcher():
    """Mock dosya izleyici"""
    watcher = MagicMock()
    watcher.is_running = False
    watcher.queue_size = 0
    return watcher

class MockDatabase:
    """Test için veritabanı mock'u"""
    
    def __init__(self, db_path=None):
        self.db_path = db_path or Path("mock.db")
        self.connection = None
        self.documents = []
        self.articles = []
        
    def initialize(self):
        """Mock initialize"""
        self.connection = sqlite3.connect(":memory:")
        return True
        
    def add_document(self, doc_data):
        """Mock belge ekleme"""
        doc_id = len(self.documents) + 1
        doc_data['id'] = doc_id
        self.documents.append(doc_data)
        return doc_id
        
    def get_document(self, doc_id):
        """Mock belge getirme"""
        for doc in self.documents:
            if doc.get('id') == doc_id:
                return Mock(**doc)
        return None
        
    def close(self):
        """Mock kapatma"""
        if self.connection:
            self.connection.close()

@pytest.fixture(scope="function")
def mock_database():
    """Mock veritabanı"""
    return MockDatabase()

def pytest_configure(config):
    """Pytest konfigürasyonu"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "ui: marks tests as UI tests"
    )

def pytest_collection_modifyitems(config, items):
    """Test toplama modifikasyonu"""
    # Slow testleri işaretle
    for item in items:
        if "slow" in item.nodeid:
            item.add_marker(pytest.mark.slow)
            
        # Integration testleri işaretle
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
            
        # UI testleri işaretle
        if "ui" in item.nodeid:
            item.add_marker(pytest.mark.ui)
