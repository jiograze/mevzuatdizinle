#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SearchEngine unit testleri
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parents[2]))

from app.core.search_engine import SearchEngine, SearchResult


class TestSearchEngine:
    """SearchEngine sınıfı testleri"""
    
    def test_initialization(self, mock_config, mock_database):
        """Arama motoru başlatma testi"""
        mock_config.get.return_value = True
        
        engine = SearchEngine(mock_config, mock_database)
        
        assert engine.config == mock_config
        assert engine.db == mock_database
    
    def test_keyword_search_success(self, mock_config, mock_database):
        """Anahtar kelime arama başarılı test"""
        mock_config.get.return_value = 20
        
        # Mock veritabanı sonuçları
        mock_results = [
            Mock(
                document_id=1,
                document_title="Test Kanunu",
                document_type="KANUN",
                article_number="1",
                content="Bu bir test kanunudur.",
                snippet="test kanunudur"
            )
        ]
        
        with patch.object(mock_database, 'search_articles') as mock_search:
            mock_search.return_value = mock_results
            
            engine = SearchEngine(mock_config, mock_database)
            results = engine.search("test", search_type="keyword")
            
            assert len(results) == 1
            assert isinstance(results[0], SearchResult)
            assert results[0].document_title == "Test Kanunu"
            assert results[0].score > 0
    
    def test_empty_query_search(self, mock_config, mock_database):
        """Boş sorgu arama testi"""
        engine = SearchEngine(mock_config, mock_database)
        
        # Boş sorgu
        results = engine.search("")
        assert len(results) == 0
        
        # None sorgu
        results = engine.search(None)
        assert len(results) == 0
        
        # Sadece boşluk
        results = engine.search("   ")
        assert len(results) == 0
    
    def test_search_with_limit(self, mock_config, mock_database):
        """Limit ile arama testi"""
        mock_config.get.return_value = 20
        
        # 10 adet mock sonuç
        mock_results = []
        for i in range(10):
            mock_results.append(Mock(
                document_id=i+1,
                document_title=f"Test Kanunu {i+1}",
                document_type="KANUN",
                article_number=str(i+1),
                content=f"Bu test kanunu {i+1} içeriğidir.",
                snippet=f"test kanunu {i+1}"
            ))
        
        with patch.object(mock_database, 'search_articles') as mock_search:
            mock_search.return_value = mock_results
            
            engine = SearchEngine(mock_config, mock_database)
            
            # 5 ile sınırla
            results = engine.search("test", limit=5)
            assert len(results) == 5
            
            # Limit kontrolü
            for result in results:
                assert isinstance(result, SearchResult)
    
    def test_search_with_filters(self, mock_config, mock_database):
        """Filtre ile arama testi"""
        mock_config.get.return_value = 20
        
        mock_results = [
            Mock(
                document_id=1,
                document_title="Vergi Kanunu",
                document_type="KANUN",
                article_number="1",
                content="Vergi ile ilgili hükümler.",
                snippet="vergi hükümler"
            )
        ]
        
        with patch.object(mock_database, 'search_articles') as mock_search:
            mock_search.return_value = mock_results
            
            engine = SearchEngine(mock_config, mock_database)
            
            # Filtre ile arama
            filters = {
                "document_type": "KANUN",
                "category": "Mali"
            }
            
            results = engine.search("vergi", filters=filters)
            
            # Mock'un doğru parametrelerle çağrıldığını kontrol et
            mock_search.assert_called_once()
            args, kwargs = mock_search.call_args
            assert "document_type" in str(kwargs) or "KANUN" in str(args)
    
    def test_search_suggestions(self, mock_config, mock_database):
        """Arama önerileri testi"""
        mock_results = ["vergi", "vergiler", "vergilendirme"]
        
        with patch.object(mock_database, 'get_search_suggestions') as mock_suggestions:
            mock_suggestions.return_value = mock_results
            
            engine = SearchEngine(mock_config, mock_database)
            suggestions = engine.get_suggestions("ver", limit=3)
            
            assert len(suggestions) == 3
            assert all("ver" in suggestion.lower() for suggestion in suggestions)
    
    def test_search_error_handling(self, mock_config, mock_database):
        """Arama hata işleme testi"""
        
        with patch.object(mock_database, 'search_articles') as mock_search:
            # Veritabanı hatası simüle et
            mock_search.side_effect = Exception("Database error")
            
            engine = SearchEngine(mock_config, mock_database)
            
            # Hata durumunda boş liste dönmeli
            results = engine.search("test")
            assert results == []
    
    def test_search_result_sorting(self, mock_config, mock_database):
        """Arama sonucu sıralama testi"""
        mock_config.get.return_value = 20
        
        mock_results = [
            Mock(
                document_id=1,
                document_title="Test A",
                document_type="KANUN",
                article_number="1",
                content="Az eşleşen içerik.",
                snippet="az eşleşen",
                relevance_score=0.3
            ),
            Mock(
                document_id=2,
                document_title="Test B",
                document_type="KANUN", 
                article_number="2",
                content="Çok test kelimesi içeren test içeriği.",
                snippet="çok test kelimesi",
                relevance_score=0.8
            )
        ]
        
        with patch.object(mock_database, 'search_articles') as mock_search:
            mock_search.return_value = mock_results
            
            engine = SearchEngine(mock_config, mock_database)
            results = engine.search("test")
            
            # Sonuçlar score'a göre sıralı olmalı (büyükten küçüğe)
            assert results[0].score >= results[1].score
    
    def test_search_performance_stats(self, mock_config, mock_database):
        """Arama performans istatistikleri testi"""
        engine = SearchEngine(mock_config, mock_database)
        
        # Başlangıçta stats boş olmalı
        stats = engine.get_performance_stats()
        assert stats['total_searches'] == 0
        assert stats['average_execution_time_ms'] == 0
        
        # Mock bir arama yap
        with patch.object(mock_database, 'search_articles') as mock_search:
            mock_search.return_value = []
            
            engine.search("test")
            
            # Stats güncellenmiş olmalı
            updated_stats = engine.get_performance_stats()
            assert updated_stats['total_searches'] == 1
            assert updated_stats['average_execution_time_ms'] >= 0
    
    @patch('app.core.search_engine.SentenceTransformer')
    def test_semantic_search_initialization(self, mock_transformer, mock_config, mock_database):
        """Semantik arama başlatma testi"""
        mock_config.get.side_effect = lambda key, default=None: {
            'search.semantic_enabled': True,
            'search.model_name': 'test-model',
            'search.device': 'cpu'
        }.get(key, default)
        
        # Mock transformer
        mock_model = MagicMock()
        mock_transformer.return_value = mock_model
        
        engine = SearchEngine(mock_config, mock_database)
        
        # Semantic search aktif olmalı
        if hasattr(engine, 'semantic_enabled'):
            assert engine.semantic_enabled == True
            mock_transformer.assert_called_once_with('test-model')
    
    def test_query_expansion(self, mock_config, mock_database):
        """Sorgu genişletme testi"""
        engine = SearchEngine(mock_config, mock_database)
        
        # Temel sorgu genişletme
        expanded = engine._expand_query("vergi")
        
        assert isinstance(expanded, list)
        assert "vergi" in expanded
        
        # Çoklu kelime
        expanded_multi = engine._expand_query("vergi kanunu")
        assert len(expanded_multi) >= 2
    
    def test_search_result_highlighting(self, mock_config, mock_database):
        """Arama sonucu vurgulama testi"""
        mock_config.get.return_value = 20
        
        mock_results = [
            Mock(
                document_id=1,
                document_title="Vergi Kanunu",
                document_type="KANUN",
                article_number="1",
                content="Bu kanunda vergi oranları düzenlenmiştir. Vergi mükellefleri bu oranlara uymakla yükümlüdür.",
                snippet="vergi oranları düzenlenmiştir"
            )
        ]
        
        with patch.object(mock_database, 'search_articles') as mock_search:
            mock_search.return_value = mock_results
            
            engine = SearchEngine(mock_config, mock_database)
            results = engine.search("vergi")
            
            assert len(results) > 0
            result = results[0]
            
            # Snippet'te arama terimi olmalı
            assert "vergi" in result.snippet.lower()


class TestSearchResult:
    """SearchResult sınıfı testleri"""
    
    def test_search_result_creation(self):
        """SearchResult oluşturma testi"""
        result = SearchResult(
            document_id=1,
            document_title="Test Kanunu",
            document_type="KANUN",
            article_number="1",
            article_title="Genel Hükümler",
            content="Test içeriği",
            snippet="test içeriği",
            score=0.85
        )
        
        assert result.document_id == 1
        assert result.document_title == "Test Kanunu"
        assert result.score == 0.85
        assert isinstance(result.score, float)
    
    def test_search_result_comparison(self):
        """SearchResult karşılaştırma testi"""
        result1 = SearchResult(
            document_id=1,
            document_title="Test 1",
            document_type="KANUN",
            article_number="1",
            content="içerik",
            score=0.7
        )
        
        result2 = SearchResult(
            document_id=2,
            document_title="Test 2",
            document_type="KANUN",
            article_number="2", 
            content="içerik",
            score=0.9
        )
        
        # Yüksek score'lu result büyük olmalı
        assert result2.score > result1.score
        
        # Sıralama testi
        results = [result1, result2]
        sorted_results = sorted(results, key=lambda x: x.score, reverse=True)
        assert sorted_results[0] == result2
        assert sorted_results[1] == result1
    
    def test_search_result_string_representation(self):
        """SearchResult string temsili testi"""
        result = SearchResult(
            document_id=1,
            document_title="Test Kanunu",
            document_type="KANUN",
            article_number="1",
            content="Test içeriği",
            score=0.75
        )
        
        str_repr = str(result)
        assert "Test Kanunu" in str_repr
        assert "0.75" in str_repr or "0,75" in str_repr  # Locale farklılığı için
    
    def test_search_result_dict_conversion(self):
        """SearchResult dict dönüştürme testi"""
        result = SearchResult(
            document_id=1,
            document_title="Test Kanunu",
            document_type="KANUN",
            article_number="1",
            content="Test içeriği",
            score=0.75
        )
        
        if hasattr(result, 'to_dict'):
            result_dict = result.to_dict()
            
            assert result_dict['document_id'] == 1
            assert result_dict['document_title'] == "Test Kanunu"
            assert result_dict['score'] == 0.75


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
