"""
Performance Optimization modülü
Async/await, memory management, caching, threading optimizasyonları
"""

import asyncio
import logging
import gc
import os
import psutil
import time
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache, wraps
import weakref

from PyQt5.QtCore import QThread, pyqtSignal, QTimer, QMutex, QWaitCondition
from PyQt5.QtWidgets import QApplication

from ..core.search_engine import SearchResult


@dataclass
class PerformanceMetrics:
    """Performans metrikleri"""
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    search_time_ms: float = 0.0
    document_processing_time_ms: float = 0.0
    cache_hit_ratio: float = 0.0
    active_threads: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


class MemoryManager:
    """Memory yönetimi ve optimizasyon"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._memory_threshold_mb = 1024  # 1GB limit
        self._gc_interval = 60  # 60 saniye
        self._last_gc_time = time.time()
        
        # Memory usage tracking
        self._memory_history = []
        self._max_history_size = 100
    
    def get_memory_usage(self) -> float:
        """Mevcut memory kullanımını MB cinsinden döndür"""
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            # History'ye ekle
            self._memory_history.append((datetime.now(), memory_mb))
            if len(self._memory_history) > self._max_history_size:
                self._memory_history.pop(0)
            
            return memory_mb
        except Exception as e:
            self.logger.error(f"Memory usage check error: {e}")
            return 0.0
    
    def should_trigger_gc(self) -> bool:
        """Garbage collection gerekli mi kontrol et"""
        current_time = time.time()
        memory_usage = self.get_memory_usage()
        
        # Zaman bazlı kontrol
        if current_time - self._last_gc_time > self._gc_interval:
            return True
        
        # Memory threshold kontrolü
        if memory_usage > self._memory_threshold_mb:
            return True
        
        return False
    
    def force_gc(self) -> Dict[str, Any]:
        """Garbage collection zorla"""
        start_memory = self.get_memory_usage()
        start_time = time.time()
        
        # Python garbage collection
        collected = gc.collect()
        
        end_time = time.time()
        end_memory = self.get_memory_usage()
        self._last_gc_time = end_time
        
        result = {
            'collected_objects': collected,
            'memory_before_mb': start_memory,
            'memory_after_mb': end_memory,
            'memory_freed_mb': start_memory - end_memory,
            'gc_time_ms': (end_time - start_time) * 1000
        }
        
        self.logger.info(f"GC completed: {result}")
        return result
    
    def optimize_memory_usage(self):
        """Memory kullanımını optimize et"""
        if self.should_trigger_gc():
            self.force_gc()
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Memory istatistiklerini getir"""
        if not self._memory_history:
            return {}
        
        recent_memory = [m[1] for m in self._memory_history[-10:]]
        
        return {
            'current_mb': self.get_memory_usage(),
            'average_mb': sum(recent_memory) / len(recent_memory),
            'peak_mb': max(recent_memory),
            'threshold_mb': self._memory_threshold_mb,
            'history_count': len(self._memory_history)
        }


class AsyncSearchEngine:
    """Asenkron arama motoru"""
    
    def __init__(self, search_engine, max_workers: int = 4):
        self.search_engine = search_engine
        self.max_workers = max_workers
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Thread pool for CPU-intensive operations
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        
        # Cache for search results
        self.search_cache = LRUCache(maxsize=1000)
        
        # Performance metrics
        self.performance_tracker = PerformanceTracker()
    
    async def search_async(self, query: str, search_type: str = "mixed", 
                          document_types: List[str] = None, 
                          include_repealed: bool = False) -> List[SearchResult]:
        """Asenkron arama gerçekleştir"""
        
        # Cache key oluştur
        cache_key = self._create_cache_key(query, search_type, document_types, include_repealed)
        
        # Cache kontrol et
        cached_result = self.search_cache.get(cache_key)
        if cached_result:
            self.logger.debug(f"Cache hit for query: {query}")
            return cached_result
        
        start_time = time.time()
        
        try:
            # Async olarak arama yap
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                self.thread_pool,
                self._sync_search,
                query, search_type, document_types, include_repealed
            )
            
            # Cache'e kaydet
            self.search_cache.set(cache_key, results)
            
            # Performance metrikleri
            search_time = (time.time() - start_time) * 1000
            self.performance_tracker.record_search_time(search_time)
            
            self.logger.info(f"Async search completed: {len(results)} results in {search_time:.2f}ms")
            return results
            
        except Exception as e:
            self.logger.error(f"Async search error: {e}")
            raise
    
    def _sync_search(self, query: str, search_type: str, 
                     document_types: List[str], include_repealed: bool) -> List[SearchResult]:
        """Senkron arama (thread pool'da çalışacak)"""
        return self.search_engine.search(
            query=query,
            document_types=document_types or [],
            search_type=search_type,
            include_repealed=include_repealed
        )
    
    def _create_cache_key(self, query: str, search_type: str, 
                         document_types: List[str], include_repealed: bool) -> str:
        """Cache key oluştur"""
        doc_types_str = ",".join(sorted(document_types or []))
        return f"{query}|{search_type}|{doc_types_str}|{include_repealed}"
    
    def clear_cache(self):
        """Cache'i temizle"""
        self.search_cache.clear()
        self.logger.info("Search cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Cache istatistikleri"""
        return self.search_cache.get_stats()


class LRUCache:
    """LRU (Least Recently Used) Cache implementation"""
    
    def __init__(self, maxsize: int = 1000):
        self.maxsize = maxsize
        self.cache = OrderedDict()
        self.hits = 0
        self.misses = 0
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Any:
        """Cache'den veri al"""
        with self._lock:
            if key in self.cache:
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                self.hits += 1
                return self.cache[key]
            else:
                self.misses += 1
                return None
    
    def set(self, key: str, value: Any):
        """Cache'e veri koy"""
        with self._lock:
            if key in self.cache:
                # Update existing
                self.cache.move_to_end(key)
                self.cache[key] = value
            else:
                # Add new
                self.cache[key] = value
                if len(self.cache) > self.maxsize:
                    # Remove oldest
                    self.cache.popitem(last=False)
    
    def clear(self):
        """Cache'i temizle"""
        with self._lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Cache istatistikleri"""
        with self._lock:
            total_requests = self.hits + self.misses
            hit_ratio = self.hits / total_requests if total_requests > 0 else 0
            
            return {
                'size': len(self.cache),
                'maxsize': self.maxsize,
                'hits': self.hits,
                'misses': self.misses,
                'hit_ratio': hit_ratio
            }


class AsyncDocumentProcessor:
    """Asenkron belge işleyici"""
    
    def __init__(self, document_processor, max_workers: int = 2):
        self.document_processor = document_processor
        self.max_workers = max_workers
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Thread pool for file I/O operations
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        
        # Progress tracking
        self._progress_callbacks = {}
        self._processing_queue = asyncio.Queue()
        
    async def process_files_async(self, file_paths: List[str], 
                                 progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Dosyaları asenkron olarak işle"""
        
        start_time = time.time()
        total_files = len(file_paths)
        
        if progress_callback:
            progress_callback(0, total_files, "İşleme başlıyor...")
        
        # Batch processing için dosyaları gruplara böl
        batch_size = min(self.max_workers, len(file_paths))
        batches = [file_paths[i:i + batch_size] for i in range(0, len(file_paths), batch_size)]
        
        results = {
            'processed_count': 0,
            'failed_files': [],
            'total_files': total_files,
            'processing_time_ms': 0
        }
        
        processed_count = 0
        
        try:
            for batch in batches:
                # Her batch'i paralel olarak işle
                batch_futures = []
                
                for file_path in batch:
                    future = asyncio.get_event_loop().run_in_executor(
                        self.thread_pool,
                        self._process_single_file,
                        file_path
                    )
                    batch_futures.append((file_path, future))
                
                # Batch sonuçlarını bekle
                for file_path, future in batch_futures:
                    try:
                        result = await future
                        
                        if result['success']:
                            results['processed_count'] += 1
                        else:
                            results['failed_files'].append({
                                'file': Path(file_path).name,
                                'error': result.get('error', 'Unknown error')
                            })
                        
                        processed_count += 1
                        
                        # Progress güncelle
                        if progress_callback:
                            progress_callback(processed_count, total_files, 
                                            f"İşlendi: {Path(file_path).name}")
                        
                    except Exception as e:
                        results['failed_files'].append({
                            'file': Path(file_path).name,
                            'error': str(e)
                        })
                        processed_count += 1
                        
                        if progress_callback:
                            progress_callback(processed_count, total_files, 
                                            f"Hata: {Path(file_path).name}")
        
        finally:
            processing_time = (time.time() - start_time) * 1000
            results['processing_time_ms'] = processing_time
            
            if progress_callback:
                progress_callback(total_files, total_files, "İşlem tamamlandı")
        
        self.logger.info(f"Batch processing completed: {results}")
        return results
    
    def _process_single_file(self, file_path: str) -> Dict[str, Any]:
        """Tek dosyayı işle"""
        try:
            return self.document_processor.process_file(file_path)
        except Exception as e:
            return {'success': False, 'error': str(e)}


class PerformanceTracker:
    """Performans izleme ve metrikleri"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Metrics storage
        self.search_times = []
        self.processing_times = []
        self.memory_snapshots = []
        
        # Limits
        self.max_history_size = 1000
        
        # Memory manager
        self.memory_manager = MemoryManager()
    
    def record_search_time(self, time_ms: float):
        """Arama süresini kaydet"""
        self.search_times.append((datetime.now(), time_ms))
        if len(self.search_times) > self.max_history_size:
            self.search_times.pop(0)
    
    def record_processing_time(self, time_ms: float):
        """İşleme süresini kaydet"""
        self.processing_times.append((datetime.now(), time_ms))
        if len(self.processing_times) > self.max_history_size:
            self.processing_times.pop(0)
    
    def take_memory_snapshot(self) -> PerformanceMetrics:
        """Memory snapshot al"""
        try:
            process = psutil.Process()
            
            metrics = PerformanceMetrics(
                memory_usage_mb=process.memory_info().rss / 1024 / 1024,
                cpu_usage_percent=process.cpu_percent(),
                active_threads=process.num_threads()
            )
            
            # Son arama süresi
            if self.search_times:
                metrics.search_time_ms = self.search_times[-1][1]
            
            # Son işleme süresi
            if self.processing_times:
                metrics.document_processing_time_ms = self.processing_times[-1][1]
            
            self.memory_snapshots.append(metrics)
            if len(self.memory_snapshots) > self.max_history_size:
                self.memory_snapshots.pop(0)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Memory snapshot error: {e}")
            return PerformanceMetrics()
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Performans özetini getir"""
        summary = {
            'memory_stats': self.memory_manager.get_memory_stats(),
            'search_stats': self._get_time_stats(self.search_times),
            'processing_stats': self._get_time_stats(self.processing_times),
            'system_info': self._get_system_info()
        }
        
        return summary
    
    def _get_time_stats(self, time_data: List[tuple]) -> Dict[str, float]:
        """Zaman istatistiklerini hesapla"""
        if not time_data:
            return {}
        
        times = [t[1] for t in time_data]
        
        return {
            'count': len(times),
            'average_ms': sum(times) / len(times),
            'min_ms': min(times),
            'max_ms': max(times),
            'recent_average_ms': sum(times[-10:]) / min(len(times), 10)
        }
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Sistem bilgilerini getir"""
        try:
            return {
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': psutil.virtual_memory().total / 1024 / 1024 / 1024,
                'memory_available_gb': psutil.virtual_memory().available / 1024 / 1024 / 1024,
                'disk_usage_percent': psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:\\').percent
            }
        except Exception as e:
            self.logger.error(f"System info error: {e}")
            return {}


class BackgroundTaskManager:
    """Background görev yöneticisi"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.tasks = {}
        self.task_counter = 0
        self._lock = threading.Lock()
    
    def schedule_task(self, task_func: Callable, *args, **kwargs) -> str:
        """Görev planla"""
        with self._lock:
            task_id = f"task_{self.task_counter}"
            self.task_counter += 1
            
            # Asyncio task oluştur
            task = asyncio.create_task(self._run_task(task_id, task_func, *args, **kwargs))
            self.tasks[task_id] = {
                'task': task,
                'created_at': datetime.now(),
                'status': 'running'
            }
            
            self.logger.info(f"Task scheduled: {task_id}")
            return task_id
    
    async def _run_task(self, task_id: str, task_func: Callable, *args, **kwargs):
        """Görev çalıştır"""
        try:
            if asyncio.iscoroutinefunction(task_func):
                result = await task_func(*args, **kwargs)
            else:
                # Sync function'ı async olarak çalıştır
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, task_func, *args, **kwargs)
            
            with self._lock:
                if task_id in self.tasks:
                    self.tasks[task_id]['status'] = 'completed'
                    self.tasks[task_id]['result'] = result
                    
            self.logger.info(f"Task completed: {task_id}")
            
        except Exception as e:
            with self._lock:
                if task_id in self.tasks:
                    self.tasks[task_id]['status'] = 'failed'
                    self.tasks[task_id]['error'] = str(e)
                    
            self.logger.error(f"Task failed: {task_id} - {e}")
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Görev durumunu getir"""
        with self._lock:
            return self.tasks.get(task_id)
    
    def cancel_task(self, task_id: str) -> bool:
        """Görevi iptal et"""
        with self._lock:
            if task_id in self.tasks:
                task_info = self.tasks[task_id]
                if task_info['status'] == 'running':
                    task_info['task'].cancel()
                    task_info['status'] = 'cancelled'
                    return True
        return False
    
    def cleanup_completed_tasks(self):
        """Tamamlanan görevleri temizle"""
        with self._lock:
            completed_tasks = [
                task_id for task_id, task_info in self.tasks.items()
                if task_info['status'] in ['completed', 'failed', 'cancelled']
            ]
            
            for task_id in completed_tasks:
                del self.tasks[task_id]
            
            self.logger.info(f"Cleaned up {len(completed_tasks)} tasks")


# Decorator for caching expensive function calls
def async_cache(maxsize: int = 128, ttl_seconds: int = 300):
    """Async function caching decorator"""
    def decorator(func):
        cache = {}
        cache_times = {}
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Cache key oluştur
            key = str(args) + str(sorted(kwargs.items()))
            current_time = time.time()
            
            # Cache kontrol et
            if key in cache:
                cache_time = cache_times.get(key, 0)
                if current_time - cache_time < ttl_seconds:
                    return cache[key]
            
            # Function çalıştır
            result = await func(*args, **kwargs)
            
            # Cache'e kaydet
            cache[key] = result
            cache_times[key] = current_time
            
            # Cache boyut kontrolü
            if len(cache) > maxsize:
                # En eski entry'leri sil
                oldest_keys = sorted(cache_times.keys(), key=lambda k: cache_times[k])
                for old_key in oldest_keys[:len(cache) - maxsize + 1]:
                    cache.pop(old_key, None)
                    cache_times.pop(old_key, None)
            
            return result
        
        return wrapper
    return decorator


class PerformanceOptimizedMainWindow:
    """Performans optimize edilmiş MainWindow mixin"""
    
    def __init__(self):
        # Performance components
        self.memory_manager = MemoryManager()
        self.performance_tracker = PerformanceTracker()
        self.background_tasks = BackgroundTaskManager()
        
        # Async search engine
        if hasattr(self, 'search_engine'):
            self.async_search = AsyncSearchEngine(self.search_engine)
        
        # Async document processor
        if hasattr(self, 'document_processor'):
            self.async_document_processor = AsyncDocumentProcessor(self.document_processor)
        
        # Performance monitoring timer
        self.performance_timer = QTimer()
        self.performance_timer.timeout.connect(self._monitor_performance)
        self.performance_timer.start(10000)  # 10 saniye
        
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Performance optimization initialized")
    
    def _monitor_performance(self):
        """Performans izleme"""
        try:
            # Memory optimization
            self.memory_manager.optimize_memory_usage()
            
            # Performance snapshot
            metrics = self.performance_tracker.take_memory_snapshot()
            
            # Log kritik durumlar
            if metrics.memory_usage_mb > 1024:  # 1GB
                self.logger.warning(f"High memory usage: {metrics.memory_usage_mb:.1f}MB")
            
            # Background task cleanup
            self.background_tasks.cleanup_completed_tasks()
            
        except Exception as e:
            self.logger.error(f"Performance monitoring error: {e}")
    
    async def optimized_search(self, query: str, **kwargs) -> List[SearchResult]:
        """Optimize edilmiş arama"""
        if hasattr(self, 'async_search'):
            return await self.async_search.search_async(query, **kwargs)
        else:
            # Fallback to sync search
            return self.search_engine.search(query, **kwargs)
    
    async def optimized_document_processing(self, file_paths: List[str], 
                                          progress_callback=None) -> Dict[str, Any]:
        """Optimize edilmiş belge işleme"""
        if hasattr(self, 'async_document_processor'):
            return await self.async_document_processor.process_files_async(
                file_paths, progress_callback
            )
        else:
            # Fallback to sync processing
            return {'processed_count': 0, 'failed_files': [], 'total_files': len(file_paths)}
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Performans istatistiklerini getir"""
        stats = self.performance_tracker.get_performance_summary()
        
        # Cache stats ekleme
        if hasattr(self, 'async_search'):
            stats['cache_stats'] = self.async_search.get_cache_stats()
        
        return stats
    
    def clear_all_caches(self):
        """Tüm cache'leri temizle"""
        if hasattr(self, 'async_search'):
            self.async_search.clear_cache()
        
        # Force GC
        gc_result = self.memory_manager.force_gc()
        self.logger.info(f"Caches cleared, GC result: {gc_result}")
