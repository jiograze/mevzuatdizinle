#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Advanced Performance Optimization Suite - Production Ready
Comprehensive performance monitoring, optimization, and analytics
"""

import asyncio
import time
import psutil
import threading
import queue
import logging
from typing import Dict, List, Optional, Any, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import wraps, lru_cache
import json
import pickle
import sqlite3
from pathlib import Path

from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QThread, QMutex
from PyQt5.QtWidgets import QApplication

from ..utils.logger import get_logger
from ..utils.config_manager import ConfigManager
from ..core.base import BaseComponent


@dataclass
class PerformanceMetrics:
    """Performance metrikleri veri sınıfı"""
    timestamp: datetime = field(default_factory=datetime.now)
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    memory_percent: float = 0.0
    disk_io_read: int = 0
    disk_io_write: int = 0
    network_sent: int = 0
    network_recv: int = 0
    active_threads: int = 0
    response_time: float = 0.0
    operation_name: str = ""
    
    def to_dict(self) -> dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'memory_percent': self.memory_percent,
            'disk_io_read': self.disk_io_read,
            'disk_io_write': self.disk_io_write,
            'network_sent': self.network_sent,
            'network_recv': self.network_recv,
            'active_threads': self.active_threads,
            'response_time': self.response_time,
            'operation_name': self.operation_name
        }


class AdvancedCache:
    """Gelişmiş cache sistemi - LRU, TTL ve smart eviction desteği"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache = {}
        self.access_times = {}
        self.insert_times = {}
        self.access_count = defaultdict(int)
        self.mutex = threading.RLock()
        self.logger = get_logger(self.__class__.__name__)
        
        # Background cleanup timer
        self.cleanup_timer = threading.Timer(300, self._cleanup_expired)  # 5 dakikada bir
        self.cleanup_timer.daemon = True
        self.cleanup_timer.start()
    
    def get(self, key: str, default=None):
        """Cache'den değer getir"""
        with self.mutex:
            if key not in self.cache:
                return default
                
            # TTL kontrolü
            if self._is_expired(key):
                self._remove_key(key)
                return default
                
            # Access statistics güncelle
            self.access_times[key] = time.time()
            self.access_count[key] += 1
            
            return self.cache[key]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Cache'e değer ekle"""
        with self.mutex:
            current_time = time.time()
            
            # Eviction kontrolü
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict_least_used()
            
            self.cache[key] = value
            self.insert_times[key] = current_time
            self.access_times[key] = current_time
            self.access_count[key] = 1
    
    def _is_expired(self, key: str) -> bool:
        """TTL kontrolü"""
        if key not in self.insert_times:
            return True
        return time.time() - self.insert_times[key] > self.ttl_seconds
    
    def _evict_least_used(self):
        """En az kullanılan elemanı çıkar (LFU + LRU hybrid)"""
        if not self.cache:
            return
            
        # En az kullanılan ve en eski erişilen elemanı bul
        min_count = min(self.access_count.values())
        candidates = [k for k, v in self.access_count.items() if v == min_count]
        
        # Aynı access count'a sahip olanlar arasından en eskisini seç
        oldest_key = min(candidates, key=lambda k: self.access_times[k])
        self._remove_key(oldest_key)
    
    def _remove_key(self, key: str):
        """Key'i cache'den kaldır"""
        self.cache.pop(key, None)
        self.access_times.pop(key, None)
        self.insert_times.pop(key, None)
        self.access_count.pop(key, None)
    
    def _cleanup_expired(self):
        """Süresi dolan elemanları temizle"""
        with self.mutex:
            expired_keys = [k for k in self.cache.keys() if self._is_expired(k)]
            for key in expired_keys:
                self._remove_key(key)
                
        # Timer'ı yeniden başlat
        self.cleanup_timer = threading.Timer(300, self._cleanup_expired)
        self.cleanup_timer.daemon = True
        self.cleanup_timer.start()
    
    def get_stats(self) -> dict:
        """Cache istatistikleri"""
        with self.mutex:
            total_access = sum(self.access_count.values())
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'utilization': len(self.cache) / self.max_size * 100,
                'total_accesses': total_access,
                'average_access_per_item': total_access / max(len(self.cache), 1),
                'ttl_seconds': self.ttl_seconds
            }


class ResourceMonitor(QObject):
    """Sistem kaynak izleme"""
    
    metrics_updated = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger(self.__class__.__name__)
        self.monitoring = False
        self.interval = 5  # 5 saniye
        self.metrics_history = deque(maxlen=1000)  # Son 1000 ölçüm
        self.process = psutil.Process()
        
        # Performance thresholds
        self.thresholds = {
            'cpu_warning': 70.0,
            'cpu_critical': 90.0,
            'memory_warning': 75.0,
            'memory_critical': 90.0,
            'response_time_warning': 2.0,
            'response_time_critical': 5.0
        }
        
        # Timer setup
        self.timer = QTimer()
        self.timer.timeout.connect(self._collect_metrics)
    
    def start_monitoring(self, interval: int = 5):
        """Monitoring başlat"""
        self.interval = interval
        self.monitoring = True
        self.timer.start(interval * 1000)
        self.logger.info(f"Resource monitoring started (interval: {interval}s)")
    
    def stop_monitoring(self):
        """Monitoring durdur"""
        self.monitoring = False
        self.timer.stop()
        self.logger.info("Resource monitoring stopped")
    
    def _collect_metrics(self):
        """Metrikleri topla"""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()
            disk_io = psutil.disk_io_counters()
            net_io = psutil.net_io_counters()
            
            # Process specific metrics
            process_memory = self.process.memory_info()
            process_threads = self.process.num_threads()
            
            metrics = PerformanceMetrics(
                cpu_usage=cpu_percent,
                memory_usage=process_memory.rss,
                memory_percent=self.process.memory_percent(),
                disk_io_read=disk_io.read_bytes if disk_io else 0,
                disk_io_write=disk_io.write_bytes if disk_io else 0,
                network_sent=net_io.bytes_sent if net_io else 0,
                network_recv=net_io.bytes_recv if net_io else 0,
                active_threads=process_threads
            )
            
            self.metrics_history.append(metrics)
            self._check_thresholds(metrics)
            self.metrics_updated.emit(metrics.to_dict())
            
        except Exception as e:
            self.logger.error(f"Metrics collection error: {e}")
    
    def _check_thresholds(self, metrics: PerformanceMetrics):
        """Eşik değer kontrolü"""
        if metrics.cpu_usage > self.thresholds['cpu_critical']:
            self.logger.critical(f"Critical CPU usage: {metrics.cpu_usage:.1f}%")
        elif metrics.cpu_usage > self.thresholds['cpu_warning']:
            self.logger.warning(f"High CPU usage: {metrics.cpu_usage:.1f}%")
            
        if metrics.memory_percent > self.thresholds['memory_critical']:
            self.logger.critical(f"Critical memory usage: {metrics.memory_percent:.1f}%")
        elif metrics.memory_percent > self.thresholds['memory_warning']:
            self.logger.warning(f"High memory usage: {metrics.memory_percent:.1f}%")
    
    def get_statistics(self, duration_minutes: int = 60) -> dict:
        """Belirli süre için istatistik"""
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {}
        
        cpu_values = [m.cpu_usage for m in recent_metrics]
        memory_values = [m.memory_percent for m in recent_metrics]
        
        return {
            'duration_minutes': duration_minutes,
            'sample_count': len(recent_metrics),
            'cpu': {
                'average': sum(cpu_values) / len(cpu_values),
                'max': max(cpu_values),
                'min': min(cpu_values)
            },
            'memory': {
                'average': sum(memory_values) / len(memory_values),
                'max': max(memory_values),
                'min': min(memory_values)
            },
            'threads_average': sum(m.active_threads for m in recent_metrics) / len(recent_metrics)
        }


class AsyncOperationManager:
    """Asenkron işlem yöneticisi"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.thread_executor = ThreadPoolExecutor(max_workers=max_workers)
        self.process_executor = ProcessPoolExecutor(max_workers=max_workers)
        self.logger = get_logger(self.__class__.__name__)
        self.active_tasks = set()
        self.task_results = {}
        
        # Performance tracking
        self.operation_times = defaultdict(list)
        self.operation_counts = defaultdict(int)
    
    async def run_async_operation(self, operation: Callable, *args, use_process: bool = False, **kwargs) -> Any:
        """Asenkron işlem çalıştır"""
        start_time = time.time()
        operation_name = operation.__name__
        
        try:
            if use_process:
                # CPU-intensive operations için process executor
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(self.process_executor, operation, *args)
            else:
                # I/O operations için thread executor  
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(self.thread_executor, operation, *args)
            
            # Performance tracking
            duration = time.time() - start_time
            self.operation_times[operation_name].append(duration)
            self.operation_counts[operation_name] += 1
            
            self.logger.debug(f"Async operation '{operation_name}' completed in {duration:.3f}s")
            return result
            
        except Exception as e:
            self.logger.error(f"Async operation '{operation_name}' failed: {e}")
            raise
    
    def get_operation_statistics(self) -> dict:
        """İşlem istatistikleri"""
        stats = {}
        for operation, times in self.operation_times.items():
            stats[operation] = {
                'count': self.operation_counts[operation],
                'average_time': sum(times) / len(times),
                'min_time': min(times),
                'max_time': max(times),
                'total_time': sum(times)
            }
        return stats
    
    def shutdown(self):
        """Executor'ları kapat"""
        self.thread_executor.shutdown(wait=True)
        self.process_executor.shutdown(wait=True)
        self.logger.info("Async operation manager shutdown completed")


def performance_monitor(operation_name: str = None):
    """Performance monitoring decorator"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            name = operation_name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_time = time.time()
                end_memory = psutil.Process().memory_info().rss
                duration = end_time - start_time
                memory_diff = end_memory - start_memory
                
                logger = get_logger('PerformanceMonitor')
                logger.info(f"Operation '{name}': {duration:.3f}s, Memory: {memory_diff:+,} bytes")
                
        return wrapper
    return decorator


class AdvancedPerformanceOptimizer(BaseComponent):
    """Gelişmiş performans optimizasyon sistemi"""
    
    def __init__(self, config: ConfigManager):
        super().__init__(config, "AdvancedPerformanceOptimizer")
        
        # Components
        self.cache = AdvancedCache(
            max_size=config.get('performance.cache_size', 10000),
            ttl_seconds=config.get('performance.cache_ttl', 3600)
        )
        self.resource_monitor = ResourceMonitor()
        self.async_manager = AsyncOperationManager(
            max_workers=config.get('performance.max_workers', 4)
        )
        
        # Performance database
        self.perf_db_path = config.get('performance.database_path', 'performance.db')
        self._init_performance_database()
        
        # Optimization settings
        self.auto_gc_enabled = config.get('performance.auto_gc', True)
        self.memory_threshold = config.get('performance.memory_threshold', 80.0)
        
    def _do_initialize(self) -> bool:
        """Initialization implementation"""
        try:
            self.resource_monitor.start_monitoring()
            self.resource_monitor.metrics_updated.connect(self._on_metrics_updated)
            
            self.logger.info("Advanced Performance Optimizer initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            return False
    
    def _init_performance_database(self):
        """Performance database initialize"""
        try:
            with sqlite3.connect(self.perf_db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        operation_name TEXT,
                        duration_ms REAL,
                        cpu_usage REAL,
                        memory_usage INTEGER,
                        memory_percent REAL,
                        success BOOLEAN
                    )
                ''')
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_timestamp 
                    ON performance_metrics(timestamp)
                ''')
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_operation 
                    ON performance_metrics(operation_name)
                ''')
        except Exception as e:
            self.logger.error(f"Performance database initialization failed: {e}")
    
    def _on_metrics_updated(self, metrics: dict):
        """Metrics güncelleme callback"""
        try:
            # Auto garbage collection
            if self.auto_gc_enabled and metrics.get('memory_percent', 0) > self.memory_threshold:
                self._trigger_garbage_collection()
            
            # Database'e kaydet
            self._save_metrics_to_db(metrics)
            
        except Exception as e:
            self.logger.error(f"Metrics processing error: {e}")
    
    def _trigger_garbage_collection(self):
        """Garbage collection tetikle"""
        import gc
        before = psutil.Process().memory_info().rss
        collected = gc.collect()
        after = psutil.Process().memory_info().rss
        freed = before - after
        
        self.logger.info(f"GC triggered: {collected} objects collected, {freed:,} bytes freed")
    
    def _save_metrics_to_db(self, metrics: dict):
        """Metrikleri database'e kaydet"""
        try:
            with sqlite3.connect(self.perf_db_path) as conn:
                conn.execute('''
                    INSERT INTO performance_metrics 
                    (operation_name, duration_ms, cpu_usage, memory_usage, memory_percent, success)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    metrics.get('operation_name', 'system'),
                    metrics.get('response_time', 0) * 1000,  # ms'ye çevir
                    metrics.get('cpu_usage', 0),
                    metrics.get('memory_usage', 0),
                    metrics.get('memory_percent', 0),
                    True
                ))
        except Exception as e:
            self.logger.error(f"Database save error: {e}")
    
    @performance_monitor("cache_optimization")
    def optimize_cache_performance(self):
        """Cache performansını optimize et"""
        stats = self.cache.get_stats()
        
        if stats['utilization'] > 90:
            self.logger.warning(f"Cache utilization high: {stats['utilization']:.1f}%")
            # Cache size'ı artır
            self.cache.max_size = int(self.cache.max_size * 1.2)
            self.logger.info(f"Cache size increased to {self.cache.max_size}")
        
        return stats
    
    def get_performance_report(self, days: int = 7) -> dict:
        """Performans raporu oluştur"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with sqlite3.connect(self.perf_db_path) as conn:
                cursor = conn.execute('''
                    SELECT 
                        operation_name,
                        COUNT(*) as operation_count,
                        AVG(duration_ms) as avg_duration,
                        MIN(duration_ms) as min_duration,
                        MAX(duration_ms) as max_duration,
                        AVG(cpu_usage) as avg_cpu,
                        AVG(memory_percent) as avg_memory,
                        SUM(CASE WHEN success THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate
                    FROM performance_metrics 
                    WHERE timestamp >= ?
                    GROUP BY operation_name
                    ORDER BY operation_count DESC
                ''', (cutoff_date,))
                
                operations = []
                for row in cursor.fetchall():
                    operations.append({
                        'operation': row[0],
                        'count': row[1],
                        'avg_duration_ms': round(row[2], 2),
                        'min_duration_ms': round(row[3], 2),
                        'max_duration_ms': round(row[4], 2),
                        'avg_cpu_usage': round(row[5], 2),
                        'avg_memory_usage': round(row[6], 2),
                        'success_rate': round(row[7], 2)
                    })
                
                # System resource statistics
                resource_stats = self.resource_monitor.get_statistics(duration_minutes=days*24*60)
                
                # Cache statistics
                cache_stats = self.cache.get_stats()
                
                # Async operation statistics
                async_stats = self.async_manager.get_operation_statistics()
                
                return {
                    'report_period_days': days,
                    'generated_at': datetime.now().isoformat(),
                    'operations': operations,
                    'system_resources': resource_stats,
                    'cache_performance': cache_stats,
                    'async_operations': async_stats,
                    'recommendations': self._generate_recommendations(operations, resource_stats)
                }
                
        except Exception as e:
            self.logger.error(f"Performance report generation failed: {e}")
            return {'error': str(e)}
    
    def _generate_recommendations(self, operations: list, resource_stats: dict) -> list:
        """Performans önerileri oluştur"""
        recommendations = []
        
        # Slow operations
        slow_ops = [op for op in operations if op['avg_duration_ms'] > 1000]
        if slow_ops:
            recommendations.append({
                'type': 'performance',
                'severity': 'warning',
                'message': f"{len(slow_ops)} operation(s) are taking >1s on average",
                'details': [f"{op['operation']}: {op['avg_duration_ms']}ms" for op in slow_ops[:3]]
            })
        
        # High CPU usage
        if resource_stats and resource_stats.get('cpu', {}).get('average', 0) > 70:
            recommendations.append({
                'type': 'resource',
                'severity': 'warning', 
                'message': f"High average CPU usage: {resource_stats['cpu']['average']:.1f}%",
                'suggestion': 'Consider optimizing CPU-intensive operations or scaling horizontally'
            })
        
        # High memory usage
        if resource_stats and resource_stats.get('memory', {}).get('average', 0) > 75:
            recommendations.append({
                'type': 'resource',
                'severity': 'warning',
                'message': f"High average memory usage: {resource_stats['memory']['average']:.1f}%", 
                'suggestion': 'Consider implementing memory optimization or garbage collection tuning'
            })
        
        return recommendations
    
    def cleanup(self):
        """Temizlik işlemleri"""
        self.resource_monitor.stop_monitoring()
        self.async_manager.shutdown()
        self.logger.info("Advanced Performance Optimizer cleanup completed")
