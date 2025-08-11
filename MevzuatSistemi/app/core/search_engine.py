try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False


"""
Arama motoru - FTS ve semantik arama kombinasyonu
"""

import time
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.utils.query_expansion import TurkishLegalQueryExpansion, LegalQueryOptimizer
from app.utils.faceted_search import LegalDocumentFacetEngine, FacetedResults
from ..utils.logger import TimedOperation, log_performance_metric

try:
    import numpy as np
    print("numpy imported successfully")
    NUMPY_AVAILABLE = True
except ImportError as e:
    print(f"Warning: numpy not available: {e}")
    NUMPY_AVAILABLE = False

try:
    # Geçici olarak devre dışı - paket uyumluluğu sorunu
    # from sentence_transformers import SentenceTransformer
    # print("sentence_transformers imported successfully")
    # SENTENCE_TRANSFORMERS_AVAILABLE = True
    print("sentence_transformers geçici olarak devre dışı - paket uyumsuzluğu")
    SENTENCE_TRANSFORMERS_AVAILABLE = False
except ImportError as e:
    print(f"Warning: sentence_transformers not available: {e}")
    SENTENCE_TRANSFORMERS_AVAILABLE = False



# Overall embedding availability
EMBEDDING_AVAILABLE = NUMPY_AVAILABLE and SENTENCE_TRANSFORMERS_AVAILABLE and FAISS_AVAILABLE


@dataclass
class SearchResult:

    document_type: str
    is_repealed: bool
    is_amended: bool
    score: float
    match_type: str  # 'keyword', 'semantic', 'mixed'
    highlights: List[str] = None

class SearchEngine:
    """Hibrit arama motoru - FTS + Semantik arama

    Düzeltmeler / İyileştirmeler (2025-08-10):
    - Çift (override eden) rebuild_index tanımı kaldırıldı; tek güvenilir implementasyon.
    - search_history tablosu kolon adı uyumsuzluğu (query_text) -> 'query' referansı düzeltildi.
    - FAISS mapping ad tutarsızlıkları giderildi (article_id_map tek kaynak).
    - get_suggestions artık hatalı SQL kullanmıyor; eksik kolonda patlamaz.
    - İçerik uzunluğu gibi facet alanları için eklenebilir yardımcılar (faceted_search tarafında desteklendi).
    """
    
    def __init__(self, config_manager, database_manager):
        import threading
        self.config = config_manager
        self.db = database_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        # Arama ayarları
        self.semantic_enabled = config_manager.get('search.semantic_enabled', True)
        self.max_results = config_manager.get('search.max_results', 20)
        self.semantic_weight = config_manager.get('search.semantic_weight', 0.4)
        self.keyword_weight = config_manager.get('search.keyword_weight', 0.6)
        # Query expansion engine
        self.query_expansion = TurkishLegalQueryExpansion(config_manager)
        self.query_optimizer = LegalQueryOptimizer(self.query_expansion)
        # Faceted search engine
        self.facet_engine = LegalDocumentFacetEngine(database_manager, config_manager)
        # Embedding modeli ve indeks
        self.embedding_model: Optional[Any] = None  # SentenceTransformer when available
        self.faiss_index: Optional[Any] = None  # faiss.Index when available
        self.article_id_map: Dict[int, int] = {}  # FAISS index -> article_id
        # Arama önbelleği (thread-safe)
        self._cache_lock = threading.RLock()
        self.search_cache: Dict[str, List[SearchResult]] = {}
        self.cache_size = config_manager.get('search.cache_size', 100)
        # Performans ayarları
        self.use_threading = config_manager.get('performance.threading.use_process_pool', False)
        self.max_workers = config_manager.get('performance.threading.max_worker_threads', 2)
        self._initialize_embedding()
    
    def _initialize_embedding(self):
        """Embedding sistemini başlat"""
        if not self.semantic_enabled or not EMBEDDING_AVAILABLE:
            self.logger.info("Semantik arama devre dışı")
            return
        
        try:
            with TimedOperation("embedding_model_load"):
                if not SENTENCE_TRANSFORMERS_AVAILABLE:
                    raise ImportError("sentence_transformers not available")
                    
                model_name = self.config.get('embedding.model_name', 'sentence-transformers/all-MiniLM-L6-v2')
                # Import here to avoid module-level import issues
                from sentence_transformers import SentenceTransformer
                self.embedding_model = SentenceTransformer(model_name)
                self.logger.info(f"Embedding modeli yüklendi: {model_name}")
            
            # FAISS indeksini yükle
            self._load_faiss_index()
            
        except Exception as e:
            self.logger.error(f"Embedding başlatma hatası: {e}")
            self.semantic_enabled = False
    
    def _load_faiss_index(self):
        """FAISS indeksini diskten yükle"""
        try:
            index_folder = self.config.get_base_folder() / 'index'
            index_path = index_folder / 'faiss.index'
            map_path = index_folder / 'emb_map.json'
            
            if index_path.exists() and map_path.exists():
                # FAISS indeksini yükle
                if not FAISS_AVAILABLE:
                    self.logger.warning("FAISS not available, semantic search disabled")
                    return
                    
                import faiss
                self.faiss_index = faiss.read_index(str(index_path))
                
                # Article ID mapping'i yükle
                import json
                with open(map_path, 'r', encoding='utf-8') as f:
                    self.article_id_map = {int(k): v for k, v in json.load(f).items()}
                
                self.logger.info(f"FAISS indeksi yüklendi: {self.faiss_index.ntotal} vektör")
            else:
                # Yeni indeks oluştur
                self._create_empty_index()
                
        except Exception as e:
            self.logger.error(f"FAISS indeks yükleme hatası: {e}")
            self._create_empty_index()
    
    def _create_empty_index(self):
        """Boş FAISS indeksi oluştur"""
        if self.embedding_model and FAISS_AVAILABLE:
            # Model boyutunu al
            sample_embedding = self.embedding_model.encode(["test"])
            dimension = sample_embedding.shape[1]
            
            # Flat indeks oluştur (basit ama etkili)
            import faiss
            self.faiss_index = faiss.IndexFlatIP(dimension)  # Inner Product
            self.article_id_map = {}
            
            self.logger.info(f"Boş FAISS indeksi oluşturuldu: {dimension} boyut")
    
    def search(self, query: str, document_types: List[str] = None, 
              search_type: str = 'mixed', include_repealed: bool = False) -> List[SearchResult]:
        """
        Ana arama fonksiyonu - Query expansion ile gelişmiş arama
        """
        start_time = time.time()
        try:
            # Cache kontrolü (thread-safe)
            cache_key = self._generate_cache_key(query, document_types, search_type, include_repealed)
            with self._cache_lock:
                if cache_key in self.search_cache:
                    cached_results = self.search_cache[cache_key]
                    log_performance_metric("search_cache_hit", 0, {"query": query[:50]})
                    return cached_results
            # Query expansion ve optimizasyon
            optimized_params = self.query_optimizer.optimize_for_search(query, search_type)
            results = []
            # Arama türüne göre işlem
            if search_type == 'keyword':
                results = self._keyword_search_enhanced(
                    query, optimized_params.get('keyword', {}), 
                    document_types, include_repealed
                )
            elif search_type == 'semantic' and self.semantic_enabled:
                results = self._semantic_search_enhanced(
                    query, optimized_params.get('semantic', {}), 
                    document_types, include_repealed
                )
            elif search_type == 'mixed':
                results = self._mixed_search_enhanced(
                    query, optimized_params, document_types, include_repealed
                )
            else:
                # Fallback: keyword search
                results = self._keyword_search(query, document_types, include_repealed)
            # Sonuçları skoruna göre sırala
            results.sort(key=lambda x: x.score, reverse=True)
            # Limit uygula
            results = results[:self.max_results]
            # Cache'e ekle
            self._add_to_cache(cache_key, results)
            # Arama geçmişine ekle
            execution_time = (time.time() - start_time) * 1000
            self.db.add_search_to_history(query, search_type, len(results), execution_time)
            # Performance log
            log_performance_metric("search_total", execution_time, {
                "query": query[:50],
                "type": search_type,
                "results": len(results)
            })
            self.logger.info(f"Arama tamamlandı: '{query}' -> {len(results)} sonuç ({execution_time:.1f}ms)")
            return results
        except Exception as e:
            # Hata detayını logla, kullanıcıya özel bilgi gösterme
            self.logger.error(f"Arama sırasında beklenmeyen bir hata oluştu: {type(e).__name__}: {e}", exc_info=True)
            raise
    
    def _keyword_search(self, query: str, document_types: List[str] = None, 
                       include_repealed: bool = False) -> List[SearchResult]:
        """FTS ile anahtar kelime araması"""
        
        with TimedOperation("keyword_search", details={"query": query[:50]}):
            # FTS sorgusu hazırla
            fts_query = self._prepare_fts_query(query)
            
            results = self.db.search_articles(
                fts_query, 
                document_types, 
                limit=self.max_results * 2  # Daha fazla al, sonra filtrele
            )
            
            search_results = []
            for result in results:
                # Mülga filtresi
                if not include_repealed and result.get('is_repealed'):
                    continue
                
                # Highlight oluştur
                highlights = self._generate_highlights(result['content'], query)
                
                search_result = SearchResult(
                    id=result['id'],
                    document_id=result['document_id'],
                    article_number=result['article_number'] or '',
                    title=result['title'] or '',
                    content=result['content'],
                    document_title=result['document_title'],
                    law_number=result['law_number'] or '',
                    document_type=result['document_type'],
                    is_repealed=result['is_repealed'],
                    is_amended=result['is_amended'],
                    score=result.get('rank', 1.0),  # FTS rank score
                    match_type='keyword',
                    highlights=highlights
                )
                
                search_results.append(search_result)
            
            return search_results
    
    def _semantic_search(self, query: str, document_types: List[str] = None,
                        include_repealed: bool = False) -> List[SearchResult]:
        """FAISS ile semantik arama"""
        
        if not self.semantic_enabled or not self.embedding_model or not self.faiss_index:
            return []
        
        with TimedOperation("semantic_search", details={"query": query[:50]}):
            # Query embedding oluştur
            query_embedding = self.embedding_model.encode([query])
            
            # FAISS ile benzer vektörleri bul
            k = min(self.max_results * 3, self.faiss_index.ntotal)  # Daha fazla al
            if k == 0:
                return []
            
            scores, indices = self.faiss_index.search(query_embedding, k)
            
            search_results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1:  # FAISS invalid index
                    continue
                
                # Article ID'yi al
                article_id = self.article_id_map.get(idx)
                if not article_id:
                    continue
                
                # Veritabanından article bilgilerini al
                article_data = self._get_article_with_document(article_id)
                if not article_data:
                    continue
                
                # Filtreler
                if document_types and article_data['document_type'] not in document_types:
                    continue
                
                if not include_repealed and article_data.get('is_repealed'):
                    continue
                
                # Semantik highlight (basit)
                highlights = self._generate_semantic_highlights(article_data['content'], query)
                
                search_result = SearchResult(
                    id=article_data['id'],
                    document_id=article_data['document_id'],
                    article_number=article_data['article_number'] or '',
                    title=article_data['title'] or '',
                    content=article_data['content'],
                    document_title=article_data['document_title'],
                    law_number=article_data['law_number'] or '',
                    document_type=article_data['document_type'],
                    is_repealed=article_data['is_repealed'],
                    is_amended=article_data['is_amended'],
                    score=float(score),  # Cosine similarity
                    match_type='semantic',
                    highlights=highlights
                )
                
                search_results.append(search_result)
            
            return search_results
    
    def _mixed_search(self, query: str, document_types: List[str] = None,
                     include_repealed: bool = False) -> List[SearchResult]:
        """Karma arama - FTS + Semantik"""
        
        if self.use_threading:
            return self._mixed_search_threaded(query, document_types, include_repealed)
        else:
            return self._mixed_search_sequential(query, document_types, include_repealed)
    
    def _mixed_search_sequential(self, query: str, document_types: List[str] = None,
                                include_repealed: bool = False) -> List[SearchResult]:
        """Sıralı karma arama"""
        
        # Her iki arama türünü çalıştır
        keyword_results = self._keyword_search(query, document_types, include_repealed)
        semantic_results = self._semantic_search(query, document_types, include_repealed)
        
        # Sonuçları birleştir ve skorları normalize et
        return self._combine_search_results(keyword_results, semantic_results)
    
    def _mixed_search_threaded(self, query: str, document_types: List[str] = None,
                              include_repealed: bool = False) -> List[SearchResult]:
        """Threading ile karma arama"""
        
        keyword_results = []
        semantic_results = []
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Her iki arama türünü paralel başlat
            future_keyword = executor.submit(self._keyword_search, query, document_types, include_repealed)
            future_semantic = executor.submit(self._semantic_search, query, document_types, include_repealed)
            
            # Sonuçları topla
            for future in as_completed([future_keyword, future_semantic]):
                try:
                    if future == future_keyword:
                        keyword_results = future.result()
                    else:
                        semantic_results = future.result()
                except Exception as e:
                    self.logger.error(f"Threading arama hatası: {e}")
        
        return self._combine_search_results(keyword_results, semantic_results)
    
    def _combine_search_results(self, keyword_results: List[SearchResult], 
                               semantic_results: List[SearchResult]) -> List[SearchResult]:
        """Arama sonuçlarını birleştir ve skorla"""
        
        # ID bazlı mapping
        combined = {}
        
        # Keyword sonuçları
        for result in keyword_results:
            result.score = result.score * self.keyword_weight
            combined[result.id] = result
        
        # Semantic sonuçları
        for result in semantic_results:
            if result.id in combined:
                # Zaten var - skorları birleştir
                existing = combined[result.id]
                existing.score += result.score * self.semantic_weight
                existing.match_type = 'mixed'
                # Highlight'ları birleştir
                if result.highlights:
                    existing.highlights.extend(result.highlights)
            else:
                # Yeni sonuç
                result.score = result.score * self.semantic_weight
                combined[result.id] = result
        
        return list(combined.values())
    
    def _prepare_fts_query(self, query: str) -> str:
        """FTS5 için sorgu hazırla"""
        # Türkçe karakterleri normalize et
        query = query.lower()
        
        # Özel karakterleri temizle
        import re
        query = re.sub(r'[^\w\s]', ' ', query)
        
        # Kelimeler
        words = query.split()
        
        # FTS sorgu formatına çevir
        if len(words) == 1:
            return f'"{words[0]}"*'  # Prefix search
        else:
            # Multiple word search
            return ' AND '.join(f'"{word}"*' for word in words if len(word) > 2)
    
    def _generate_highlights(self, content: str, query: str, max_highlights: int = 3) -> List[str]:
        """Anahtar kelime highlight'ları oluştur"""
        import re
        
        highlights = []
        words = query.lower().split()
        
        for word in words:
            if len(word) < 3:
                continue
            
            # Word boundary ile ara
            pattern = rf'\b\w*{re.escape(word)}\w*\b'
            matches = re.finditer(pattern, content, re.IGNORECASE)
            
            for match in matches:
                start = max(0, match.start() - 50)
                end = min(len(content), match.end() + 50)
                snippet = content[start:end]
                
                # Highlight ekle
                highlighted = re.sub(
                    pattern, 
                    r'<mark>\g<0></mark>', 
                    snippet, 
                    flags=re.IGNORECASE
                )
                
                highlights.append(highlighted.strip())
                
                if len(highlights) >= max_highlights:
                    break
        
        return highlights[:max_highlights]
    
    def _generate_semantic_highlights(self, content: str, query: str, max_highlights: int = 2) -> List[str]:
        """Semantik highlight'lar (basit sentence-based)"""
        sentences = content.split('.')
        highlights = []
        
        # İlk birkaç cümleyi al (basit yaklaşım)
        for sentence in sentences[:max_highlights]:
            if len(sentence.strip()) > 20:
                highlights.append(sentence.strip() + '.')
        
        return highlights
    
    def _get_article_with_document(self, article_id: int) -> Optional[Dict]:
        """Article'ı document bilgileriyle birlikte getir"""
        cursor = self.db.connection.cursor()
        cursor.execute("""
            SELECT 
                a.id, a.document_id, a.article_number, a.title, a.content,
                a.is_repealed, a.is_amended,
                d.title as document_title, d.law_number, d.document_type
            FROM articles a
            JOIN documents d ON a.document_id = d.id
            WHERE a.id = ?
        """, (article_id,))
        
        row = cursor.fetchone()
        cursor.close()
        
        """
        Arama motoru - FTS ve semantik arama kombinasyonu
        """

        import time
        import logging
        from typing import List, Dict, Any, Optional
        from dataclasses import dataclass
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from app.utils.query_expansion import TurkishLegalQueryExpansion, LegalQueryOptimizer
        from app.utils.faceted_search import LegalDocumentFacetEngine, FacetedResults
        from ..utils.logger import TimedOperation, log_performance_metric

        try:
            import numpy as np
            NUMPY_AVAILABLE = True
        except ImportError:
            NUMPY_AVAILABLE = False

        try:
            import faiss
            FAISS_AVAILABLE = True
        except ImportError:
            FAISS_AVAILABLE = False
        """Yeni article'ı indekse ekle"""
        if not self.semantic_enabled or not self.embedding_model:
            return
        
        try:
            # Embedding oluştur
            embedding = self.embedding_model.encode([content])
            
            # FAISS'e ekle
            if self.faiss_index:
                self.faiss_index.add(embedding)
                
                # Mapping güncelle
                new_index = self.faiss_index.ntotal - 1
                self.article_id_map[new_index] = article_id
                
                self.logger.debug(f"Article {article_id} indekse eklendi")
            
        except Exception as e:
            self.logger.error(f"İndekse ekleme hatası: {e}")
    
    def rebuild_index(self):
        """Tüm indeksi yeniden oluştur"""
        if not self.semantic_enabled or not self.embedding_model:
            return False
        
        try:
            self.logger.info("FAISS indeksi yeniden oluşturuluyor...")
            
            # Tüm article'ları al
            cursor = self.db.connection.cursor()
            cursor.execute("SELECT id, content_clean FROM articles WHERE content_clean IS NOT NULL")
            articles = cursor.fetchall()
            cursor.close()
            
            if not articles:
                self.logger.warning("İndekslenecek article bulunamadı")
                return False
            
            # Embeddings oluştur
            contents = [article[1] for article in articles]
            article_ids = [article[0] for article in articles]
            
            with TimedOperation("rebuild_embeddings", details={"count": len(contents)}):
                embeddings = self.embedding_model.encode(contents)
            
            # Yeni indeks oluştur
            dimension = embeddings.shape[1]
            import faiss
            self.faiss_index = faiss.IndexFlatIP(dimension)
            
            # Embeddings'leri ekle
            self.faiss_index.add(embeddings)
            
            # Mapping oluştur
            self.article_id_map = {i: article_ids[i] for i in range(len(article_ids))}
            
            # Diske kaydet
            self._save_faiss_index()
            
            self.logger.info(f"FAISS indeksi yeniden oluşturuldu: {len(articles)} artikel")
            return True
            
        except Exception as e:
            self.logger.error(f"İndeks yeniden oluşturma hatası: {e}")
            return False
    
    def _save_faiss_index(self):
        """FAISS indeksini diske kaydet"""
        try:
            index_folder = self.config.get_base_folder() / 'index'
            index_folder.mkdir(parents=True, exist_ok=True)
            
            # FAISS indeksini kaydet
            index_path = index_folder / 'faiss.index'
            if FAISS_AVAILABLE:
                import faiss
                faiss.write_index(self.faiss_index, str(index_path))
            
            # Article mapping'i kaydet
            map_path = index_folder / 'emb_map.json'
            import json
            with open(map_path, 'w', encoding='utf-8') as f:
                json.dump(self.article_id_map, f, ensure_ascii=False, indent=2)
            
            self.logger.info("FAISS indeksi kaydedildi")
            
        except Exception as e:
            self.logger.error(f"FAISS kaydetme hatası: {e}")
    
    def get_search_suggestions(self, partial_query: str, limit: int = 5) -> List[str]:
        """Arama önerileri"""
        if len(partial_query) < 2:
            return []
        
        try:
            # Check if database connection exists
            if not self.db or not self.db.connection:
                self.logger.warning("Database connection not available for search suggestions")
                return []
            
            # Son aramalardan öneriler
            recent_searches = self.db.get_search_history(limit=50)
            
            suggestions = []
            for search in recent_searches:
                query = search['query']
                if partial_query.lower() in query.lower() and query not in suggestions:
                    suggestions.append(query)
                    
                    if len(suggestions) >= limit:
                        break
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Öneri oluşturma hatası: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Arama motoru istatistikleri"""
        return {
            'semantic_enabled': self.semantic_enabled,
            'faiss_index_size': self.faiss_index.ntotal if self.faiss_index else 0,
            'cache_size': len(self.search_cache),
            'embedding_model': self.config.get('embedding.model_name') if self.embedding_model else None
        }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Performans istatistikleri"""
        try:
            # Check if database connection exists
            if not self.db or not self.db.connection:
                self.logger.warning("Database connection not available for performance stats")
                return self._get_default_performance_stats()
            
            cursor = self.db.connection.cursor()
            
            # Check if search_history table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='search_history'
            """)
            if not cursor.fetchone():
                self.logger.warning("search_history table not found")
                cursor.close()
                return self._get_default_performance_stats()
            
            # Toplam arama sayısı
            cursor.execute("SELECT COUNT(*) FROM search_history")
            total_searches = cursor.fetchone()[0]
            
            # Ortalama arama süresi
            cursor.execute("""
                SELECT AVG(execution_time_ms), 
                       MIN(execution_time_ms), 
                       MAX(execution_time_ms)
                FROM search_history 
                WHERE execution_time_ms IS NOT NULL
            """)
            timing_stats = cursor.fetchone()
            
            # Arama türü dağılımı
            cursor.execute("""
                SELECT query_type, COUNT(*) 
                FROM search_history 
                GROUP BY query_type
            """)
            search_type_counts = dict(cursor.fetchall())
            
            cursor.close()
            
            return {
                'total_searches': total_searches,
                'average_execution_time_ms': timing_stats[0] if timing_stats[0] else 0,
                'min_execution_time_ms': timing_stats[1] if timing_stats[1] else 0,
                'max_execution_time_ms': timing_stats[2] if timing_stats[2] else 0,
                'search_type_counts': search_type_counts,
                'faiss_index_size': self.faiss_index.ntotal if self.faiss_index else 0,
                'semantic_enabled': self.semantic_enabled,
                'cache_size': len(self.search_cache) if hasattr(self, 'search_cache') else 0
            }
            
        except Exception as e:
            self.logger.error(f"Performans istatistikleri alınamadı: {e}")
            return self._get_default_performance_stats()
    
    def _get_default_performance_stats(self) -> Dict[str, Any]:
        """Default performance stats when database is unavailable"""
        return {
            'total_searches': 0,
            'average_execution_time_ms': 0,
            'min_execution_time_ms': 0,
            'max_execution_time_ms': 0,
            'search_type_counts': {},
            'faiss_index_size': self.faiss_index.ntotal if self.faiss_index else 0,
            'semantic_enabled': self.semantic_enabled,
            'cache_size': len(self.search_cache) if hasattr(self, 'search_cache') else 0
        }
    
    def get_suggestions(self, query: str, limit: int = 5) -> List[str]:
        """Son aramalar + popüler terimlerden öneriler döndür.

        Not: search_history tablosunda kolon adı 'query'. Önceki sürümde
        'query_text' aranıyordu ve hata veriyordu.
        """
        try:
            q = (query or '').strip()
            if len(q) < 2:
                return []

            # Check if database connection exists
            if not self.db or not self.db.connection:
                self.logger.warning("Database connection not available for suggestions")
                return self._get_fallback_suggestions(q, limit)

            cursor = self.db.connection.cursor()
            
            # Check if search_history table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='search_history'
            """)
            if not cursor.fetchone():
                self.logger.warning("search_history table not found for suggestions")
                cursor.close()
                return self._get_fallback_suggestions(q, limit)
            
            cursor.execute(
                """
                SELECT DISTINCT query
                FROM search_history
                WHERE query LIKE ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (f"%{q}%", limit)
            )
            suggestions = [r[0] for r in cursor.fetchall() if r and r[0]]
            cursor.close()

            if len(suggestions) < limit:
                suggestions.extend(self._get_fallback_suggestions(q, limit - len(suggestions)))
            
            return suggestions[:limit]
        except Exception as e:
            self.logger.error(f"Öneri alma hatası: {e}")
            return self._get_fallback_suggestions(q, limit)
    
    def _get_fallback_suggestions(self, query: str, limit: int) -> List[str]:
        """Fallback suggestions when database is unavailable"""
        fallback = [
            "vergi kanunu","türk ceza kanunu","medeni kanun","borçlar kanunu",
            "iş kanunu","sosyal güvenlik","ticaret kanunu","çevre kanunu","eğitim","sağlık"
        ]
        ql = query.lower()
        suggestions = []
        for term in fallback:
            if ql in term and term not in suggestions:
                suggestions.append(term)
                if len(suggestions) >= limit:
                    break
        return suggestions
    
    # ======================== ENHANCED SEARCH METHODS ========================
    
    def _keyword_search_enhanced(self, query: str, optimization_params: Dict[str, any],
                                document_types: List[str] = None, 
                                include_repealed: bool = False) -> List[SearchResult]:
        """Gelişmiş FTS araması - Query expansion ile"""
        
        with TimedOperation("enhanced_keyword_search", details={"query": query[:50]}):
            # Optimize edilmiş FTS sorgusu kullan
            fts_query = optimization_params.get('fts_query', self._prepare_fts_query(query))
            boost_terms = optimization_params.get('boost_terms', [])
            term_weights = optimization_params.get('weights', {})
            
            results = self.db.search_articles(
                fts_query, 
                document_types, 
                limit=self.max_results * 2
            )
            
            search_results = []
            for result in results:
                if not include_repealed and result.get('is_repealed'):
                    continue
                
                # Gelişmiş scoring - boost terms için ekstra puan
                base_score = result.get('rank', 1.0)
                boosted_score = self._calculate_boosted_score(
                    result['content'], boost_terms, term_weights, base_score
                )
                
                # Enhanced highlights
                highlights = self._generate_enhanced_highlights(
                    result['content'], query, boost_terms
                )
                
                search_result = SearchResult(
                    id=result['id'],
                    document_id=result['document_id'],
                    article_number=result['article_number'] or '',
                    title=result['title'] or '',
                    content=result['content'],
                    document_title=result['document_title'],
                    law_number=result['law_number'] or '',
                    document_type=result['document_type'],
                    is_repealed=result['is_repealed'],
                    is_amended=result['is_amended'],
                    score=boosted_score,
                    match_type='keyword_enhanced',
                    highlights=highlights
                )
                
                search_results.append(search_result)
            
            return search_results
    
    def _semantic_search_enhanced(self, query: str, optimization_params: Dict[str, any],
                                 document_types: List[str] = None,
                                 include_repealed: bool = False) -> List[SearchResult]:
        """Gelişmiş semantik arama"""
        
        if not self.semantic_enabled or not self.embedding_model or not self.faiss_index:
            return []
        
        with TimedOperation("enhanced_semantic_search", details={"query": query[:50]}):
            # Optimize edilmiş semantic query kullan
            semantic_query = optimization_params.get('semantic_query', query)
            context_boost = optimization_params.get('context_boost')
            similarity_threshold = optimization_params.get('similarity_threshold', 0.7)
            
            # Enhanced query embedding
            query_embedding = self.embedding_model.encode([semantic_query])
            
            # FAISS arama
            k = min(self.max_results * 3, self.faiss_index.ntotal)
            if k == 0:
                return []
            
            scores, indices = self.faiss_index.search(query_embedding, k)
            
            search_results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1 or score < similarity_threshold:
                    continue
                
                article_id = self.article_id_map.get(idx)
                if not article_id:
                    continue
                
                article_data = self._get_article_with_document(article_id)
                if not article_data:
                    continue
                
                # Filtreler
                if document_types and article_data['document_type'] not in document_types:
                    continue
                
                if not include_repealed and article_data.get('is_repealed'):
                    continue
                
                # Context-aware scoring
                final_score = self._apply_context_boost(
                    float(score), context_boost, article_data
                )
                
                # Semantic highlights
                highlights = self._generate_semantic_highlights(
                    article_data['content'], semantic_query
                )
                
                search_result = SearchResult(
                    id=article_data['id'],
                    document_id=article_data['document_id'],
                    article_number=article_data['article_number'] or '',
                    title=article_data['title'] or '',
                    content=article_data['content'],
                    document_title=article_data['document_title'],
                    law_number=article_data['law_number'] or '',
                    document_type=article_data['document_type'],
                    is_repealed=article_data['is_repealed'],
                    is_amended=article_data['is_amended'],
                    score=final_score,
                    match_type='semantic_enhanced',
                    highlights=highlights
                )
                
                search_results.append(search_result)
            
            return search_results
    
    def _mixed_search_enhanced(self, query: str, optimization_params: Dict[str, any],
                              document_types: List[str] = None,
                              include_repealed: bool = False) -> List[SearchResult]:
        """Gelişmiş karma arama"""
        
        # Enhanced search parameters
        keyword_params = optimization_params.get('keyword', {})
        semantic_params = optimization_params.get('semantic', {})
        fusion_weights = optimization_params.get('fusion_weights', {'keyword': 0.6, 'semantic': 0.4})
        
        if self.use_threading:
            # Parallel enhanced search
            keyword_results = []
            semantic_results = []
            
            with ThreadPoolExecutor(max_workers=2) as executor:
                future_keyword = executor.submit(
                    self._keyword_search_enhanced, query, keyword_params, 
                    document_types, include_repealed
                )
                future_semantic = executor.submit(
                    self._semantic_search_enhanced, query, semantic_params, 
                    document_types, include_repealed
                )
                
                for future in as_completed([future_keyword, future_semantic]):
                    try:
                        if future == future_keyword:
                            keyword_results = future.result()
                        else:
                            semantic_results = future.result()
                    except Exception as e:
                        self.logger.error(f"Enhanced threading arama hatası: {e}")
            
            return self._combine_enhanced_results(
                keyword_results, semantic_results, fusion_weights
            )
        else:
            # Sequential enhanced search
            keyword_results = self._keyword_search_enhanced(
                query, keyword_params, document_types, include_repealed
            )
            semantic_results = self._semantic_search_enhanced(
                query, semantic_params, document_types, include_repealed
            )
            
            return self._combine_enhanced_results(
                keyword_results, semantic_results, fusion_weights
            )
    
    def _calculate_boosted_score(self, content: str, boost_terms: List[str], 
                                term_weights: Dict[str, float], base_score: float) -> float:
        """Boost terms ile scoring hesaplama"""
        if not boost_terms:
            return base_score
        
        content_lower = content.lower()
        boost_score = base_score
        
        for term in boost_terms:
            term_count = content_lower.count(term.lower())
            if term_count > 0:
                weight = term_weights.get(term, 1.0)
                boost_score += term_count * weight * 0.1  # Boost factor
        
        return min(boost_score, base_score * 2.0)  # Maximum 2x boost
    
    def _generate_enhanced_highlights(self, content: str, query: str, 
                                    boost_terms: List[str], max_highlights: int = 3) -> List[str]:
        """Gelişmiş highlight oluşturma"""
        import re
        
        highlights = []
        all_terms = [query] + boost_terms
        
        for term in all_terms:
            if len(term) < 3:
                continue
            
            # Case-insensitive search
            pattern = rf'\b\w*{re.escape(term)}\w*\b'
            matches = list(re.finditer(pattern, content, re.IGNORECASE))
            
            for match in matches:
                start = max(0, match.start() - 60)
                end = min(len(content), match.end() + 60)
                snippet = content[start:end]
                
                # Multi-term highlighting
                highlighted = snippet
                for highlight_term in all_terms:
                    if len(highlight_term) >= 3:
                        highlight_pattern = rf'\b(\w*{re.escape(highlight_term)}\w*)\b'
                        highlighted = re.sub(
                            highlight_pattern, 
                            r'<mark>\1</mark>', 
                            highlighted, 
                            flags=re.IGNORECASE
                        )
                
                highlights.append(highlighted.strip())
                
                if len(highlights) >= max_highlights:
                    return highlights[:max_highlights]
        
        return highlights[:max_highlights]
    
    def _apply_context_boost(self, base_score: float, context_boost: str, 
                           article_data: Dict) -> float:
        """Yasal bağlam ile score boosting"""
        if not context_boost:
            return base_score
        
        content = article_data.get('content', '').lower()
        document_type = article_data.get('document_type', '').lower()
        
        boost_factor = 1.0
        
        # Context-based boosting
        context_mappings = {
            'ceza': ['ceza', 'suç', 'mahkumiyet'],
            'medeni': ['medeni', 'evlilik', 'miras'],
            'ticaret': ['ticaret', 'şirket', 'ortaklık'],
            'vergi': ['vergi', 'gelir', 'beyan'],
            'is': ['işçi', 'çalışma', 'sendika'],
            'idare': ['idari', 'kamu', 'devlet']
        }
        
        if context_boost in context_mappings:
            context_terms = context_mappings[context_boost]
            for term in context_terms:
                if term in content:
                    boost_factor += 0.1
        
        # Document type boosting
        if context_boost in document_type:
            boost_factor += 0.15
        
        return base_score * boost_factor
    
    def _combine_enhanced_results(self, keyword_results: List[SearchResult], 
                                 semantic_results: List[SearchResult],
                                 fusion_weights: Dict[str, float]) -> List[SearchResult]:
        """Enhanced result fusion"""
        combined = {}
        
        # Keyword results with fusion weights
        for result in keyword_results:
            result.score = result.score * fusion_weights.get('keyword', 0.6)
            combined[result.id] = result
        
        # Semantic results with fusion weights
        for result in semantic_results:
            if result.id in combined:
                # Merge scores with weighted fusion
                existing = combined[result.id]
                existing.score += result.score * fusion_weights.get('semantic', 0.4)
                existing.match_type = 'mixed_enhanced'
                
                # Merge highlights intelligently
                if result.highlights:
                    # Remove duplicates and merge
                    all_highlights = existing.highlights + result.highlights
                    unique_highlights = []
                    seen = set()
                    for highlight in all_highlights:
                        if highlight not in seen:
                            unique_highlights.append(highlight)
                            seen.add(highlight)
                    existing.highlights = unique_highlights[:5]  # Limit to 5
            else:
                # New result
                result.score = result.score * fusion_weights.get('semantic', 0.4)
                combined[result.id] = result
        
        return list(combined.values())

    def search_with_facets(self, query: str, 
                          search_type: str = 'mixed',
                          facet_filters: Dict[str, List[str]] = None) -> FacetedResults:
        """
        Faceted search - arama sonuçlarını facetlerle filtrele
        
        Args:
            query: Arama sorgusu
            search_type: Arama türü ('keyword', 'semantic', 'mixed')
            facet_filters: Seçili facet filtreleri
        
        Returns:
            Faceted search sonuçları
        """
        try:
            with TimedOperation("faceted_search"):
                # İlk olarak normal arama yap
                base_results = self.search(query, search_type=search_type)
                
                # Faceted filtering uygula
                faceted_results = self.facet_engine.search_with_facets(
                    base_results, facet_filters
                )
                
                log_performance_metric(
                    'faceted_search_completed',
                    {
                        'query': query,
                        'base_count': len(base_results),
                        'filtered_count': faceted_results.filtered_count,
                        'facet_count': len(faceted_results.facets),
                        'applied_filters': len(facet_filters) if facet_filters else 0
                    }
                )
                
                return faceted_results
                
        except Exception as e:
            self.logger.error(f"Faceted search hatası: {e}")
            
            # Fallback - sadece temel sonuçları döndür
            base_results = self.search(query, search_type=search_type)
            return FacetedResults(
                documents=base_results,
                facets=[],
                total_count=len(base_results),
                filtered_count=len(base_results),
                applied_filters=facet_filters or {}
            )
    
    def get_facet_suggestions(self, facet_name: str, partial_value: str, 
                             limit: int = 10) -> List[Any]:
        """
        Facet değeri için önerileri al
        
        Args:
            facet_name: Facet adı
            partial_value: Kısmi değer
            limit: Maksimum öneri sayısı
            
        Returns:
            Facet önerileri
        """
        try:
            return self.facet_engine.get_facet_suggestions(
                facet_name, partial_value, limit
            )
        except Exception as e:
            self.logger.error(f"Facet öneri hatası: {e}")
            return []
    
    def export_search_state(self, faceted_results: FacetedResults) -> Dict[str, Any]:
        """
        Arama durumunu export et (URL paylaşımı için)
        
        Args:
            faceted_results: Faceted search sonuçları
            
        Returns:
            Export edilen arama durumu
        """
        return self.facet_engine.export_facet_state(faceted_results)
    
    def import_search_state(self, export_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Export edilen arama durumunu import et
        
        Args:
            export_data: Export edilen veri
            
        Returns:
            Import edilen facet filtreleri
        """
        return self.facet_engine.import_facet_state(export_data)


class HybridSearchEngine(SearchEngine):
    """
    Hibrit arama motoru - FTS ve semantik arama kombinasyonu
    SearchEngine sınıfının alias'ı olarak çalışır
    """
    
    def __init__(self, db_manager, config_manager=None):
        """
        Hibrit arama motoru başlatıcı
        
        Args:
            db_manager: Veritabanı yöneticisi
            config_manager: Konfigürasyon yöneticisi
        """
        super().__init__(db_manager, config_manager)
        self.logger.info("HybridSearchEngine initialized")
    
    def hybrid_search(self, query: str, search_type: str = "all", 
                     limit: int = 50, **kwargs) -> List[SearchResult]:
        """
        Hibrit arama fonksiyonu - hem FTS hem semantik arama
        
        Args:
            query: Arama sorgusu
            search_type: Arama tipi
            limit: Sonuç limiti
            **kwargs: Ek parametreler
            
        Returns:
            Hibrit arama sonuçları
        """
        # Ana search metodunu kullan
        return self.search(query, search_type=search_type, limit=limit)
    
    def get_semantic_similarity(self, query: str, document_text: str) -> float:
        """
        İki metin arasındaki semantik benzerliği hesapla
        
        Args:
            query: Sorgu metni
            document_text: Doküman metni
            
        Returns:
            Benzerlik skoru (0.0-1.0 arası)
        """
        try:
            if EMBEDDING_AVAILABLE:
                # Gelecekteki implementasyon için placeholder
                return 0.5
            else:
                # Basit kelime tabanlı benzerlik
                query_words = set(query.lower().split())
                doc_words = set(document_text.lower().split())
                
                if not query_words or not doc_words:
                    return 0.0
                    
                intersection = query_words.intersection(doc_words)
                union = query_words.union(doc_words)
                
                return len(intersection) / len(union) if union else 0.0
                
        except Exception as e:
            self.logger.error(f"Semantic similarity error: {e}")
            return 0.0
