# Mevzuat Sistemi - API Referans Dokümantasyonu

## İçindekiler

1. [Genel Bakış](#genel-bakış)
2. [Core API](#core-api)
3. [UI API](#ui-api)
4. [Performance API](#performance-api)
5. [Utility API](#utility-api)
6. [Exception Handling](#exception-handling)
7. [Data Models](#data-models)

## Genel Bakış

Mevzuat Belge Analiz & Sorgulama Sistemi, mevzuat belgelerinin işlenmesi ve sorgulanması için geliştirilmiş masaüstü uygulamasıdır. Sistem modüler mimari ile tasarlanmış olup, aşağıdaki ana API katmanlarına sahiptir:

- **Core API**: İş mantığı ve veri işleme
- **UI API**: Kullanıcı arayüzü bileşenleri
- **Performance API**: Performans optimizasyonu ve monitoring
- **Utility API**: Yardımcı araçlar ve servisler

## Core API

### SearchEngine

Ana arama motoru sınıfı. Hibrit arama (semantik + keyword) desteği sunar.

#### Arama Metodları

##### `search(query, search_type="mixed", document_types=None, include_repealed=False)`

Ana arama metodunu gerçekleştirir.

**Parameters:**

- `query` (str): Arama sorgusu
- `search_type` (str, optional): Arama tipi. Değerler: "semantic", "keyword", "mixed". Varsayılan: "mixed"
- `document_types` (List[str], optional): Filtrelenecek belge türleri. Örnek: ["KANUN", "TÜZÜK"]
- `include_repealed` (bool, optional): Mülga maddelerin dahil edilmesi. Varsayılan: False

**Returns:**

- `List[SearchResult]`: Arama sonuçları listesi

**Raises:**

- `SearchEngineException`: Arama işlemi başarısız olduğunda

**Example:**

```python
search_engine = SearchEngine(db, config)
results = search_engine.search(
    query="medeni hukuk", 
    search_type="mixed",
    document_types=["KANUN"],
    include_repealed=False
)
```

##### `search_with_facets(query, search_type="mixed", facet_filters=None)`

Gelişmiş filtrelemeli arama yapar.

**Parameters:**
- `query` (str): Arama sorgusu
- `search_type` (str, optional): Arama tipi. Varsayılan: "mixed"
- `facet_filters` (Dict[str, Any], optional): Çok boyutlu filtreler

**Returns:**
- `FacetedSearchResult`: Filtrelenmiş sonuçlar ve facet bilgileri

**Example:**
```python
facet_filters = {
    "date_range": {"start": "2020-01-01", "end": "2023-12-31"},
    "categories": ["civil_law", "commercial_law"],
    "status": ["active"]
}
results = search_engine.search_with_facets("şirket", facet_filters=facet_filters)
```

##### `rebuild_index()`

Semantik arama indeksini yeniden oluşturur.

**Returns:**
- `bool`: İşlem başarı durumu

**Example:**
```python
success = search_engine.rebuild_index()
if success:
    print("İndeks başarıyla yenilendi")
```

### DocumentProcessor

Belge işleme ve analiz sınıfı.

#### Methods

##### `process_file(file_path)`

Tek bir dosyayı işler ve sisteme ekler.

**Parameters:**
- `file_path` (str): İşlenecek dosyanın tam yolu

**Returns:**
- `Dict[str, Any]`: İşlem sonucu
  ```python
  {
      "success": bool,
      "document_id": int,
      "error": str,  # Hata durumunda
      "processing_time_ms": float
  }
  ```

**Raises:**
- `DocumentProcessingException`: İşlem başarısız olduğunda
- `UnsupportedFileTypeException`: Desteklenmeyen dosya türü
- `FileSizeException`: Dosya boyutu limite aşıldığında

**Example:**
```python
processor = DocumentProcessor(db, config)
result = processor.process_file("/path/to/document.pdf")
if result["success"]:
    print(f"Belge işlendi: ID {result['document_id']}")
```

##### `process_batch(file_paths, progress_callback=None, max_workers=2)`

Çoklu dosyayı toplu olarak işler.

**Parameters:**
- `file_paths` (List[str]): İşlenecek dosya yolları listesi
- `progress_callback` (Callable, optional): İlerleme callback fonksiyonu
- `max_workers` (int, optional): Paralel worker sayısı. Varsayılan: 2

**Returns:**
- `Dict[str, Any]`: Toplu işlem sonucu
  ```python
  {
      "total_files": int,
      "processed_count": int,
      "failed_count": int,
      "failed_files": List[Dict],
      "processing_time_ms": float
  }
  ```

**Example:**
```python
def progress_callback(current, total, filename):
    print(f"İşleniyor: {current}/{total} - {filename}")

files = ["/path/file1.pdf", "/path/file2.docx"]
result = processor.process_batch(files, progress_callback)
```

##### `extract_text(file_path)`

Dosyadan metin çıkarır (işleme yapmadan).

**Parameters:**
- `file_path` (str): Dosya yolu

**Returns:**
- `str`: Çıkarılan metin içeriği

**Raises:**
- `TextExtractionException`: Metin çıkarma hatası

### DatabaseManager

Veritabanı yönetim sınıfı.

#### Methods

##### `initialize_database()`

Veritabanını başlatır ve tabloları oluşturur.

**Returns:**
- `bool`: İşlem başarı durumu

##### `get_document(document_id)`

Belirli bir belgeyi ID ile getirir.

**Parameters:**
- `document_id` (int): Belge ID'si

**Returns:**
- `Document`: Belge modeli veya None

##### `search_articles(query, filters=None)`

Madde bazında arama yapar.

**Parameters:**
- `query` (str): Arama sorgusu
- `filters` (Dict, optional): Filtreler

**Returns:**
- `List[Article]`: Madde listesi

##### `get_statistics()`

Sistem istatistiklerini getirir.

**Returns:**
- `Dict[str, Any]`: İstatistik verileri
  ```python
  {
      "total_documents": int,
      "total_articles": int,
      "document_types": Dict[str, int],
      "last_update": str,
      "database_size_mb": float
  }
  ```

## UI API

### IMainWindowView Interface

Ana pencere görünüm interface'i (SOLID - Interface Segregation).

#### Methods

##### `show_message(message, duration=0)`

Durum çubuğunda mesaj gösterir.

**Parameters:**
- `message` (str): Gösterilecek mesaj
- `duration` (int, optional): Mesaj süresi (ms). 0 = kalıcı

##### `show_progress(visible, value=0, maximum=100)`

Progress bar'ı yönetir.

**Parameters:**
- `visible` (bool): Görünürlük durumu
- `value` (int, optional): Mevcut değer
- `maximum` (int, optional): Maksimum değer

##### `update_result_count(count)`

Sonuç sayısını günceller.

**Parameters:**
- `count` (int): Sonuç sayısı

### MainWindowController

SOLID principles ile tasarlanmış ana pencere kontrolcüsü.

#### Methods

##### `async perform_search(query, search_type, filters)`

Asenkron arama işlemini yönetir.

**Parameters:**
- `query` (str): Arama sorgusu
- `search_type` (str): Arama tipi
- `filters` (Dict[str, Any]): Arama filtreleri

##### `async add_documents_async(file_paths, progress_callback=None)`

Belgeleri asenkron olarak ekler.

**Parameters:**
- `file_paths` (List[str]): Dosya yolları
- `progress_callback` (Callable, optional): İlerleme callback'i

**Returns:**
- `Dict[str, Any]`: İşlem sonucu

### MenuManager

Menü yönetim sınıfı (SOLID - Single Responsibility).

#### Methods

##### `create_menu_bar()`

Ana menü çubuğunu oluşturur.

**Returns:**
- `QMenuBar`: Menü çubuğu

##### `create_toolbar()`

Ana toolbar'ı oluşturur.

## Performance API

### AsyncSearchEngine

Asenkron arama motoru wrapper'ı.

#### Methods

##### `async search_async(query, **kwargs)`

Asenkron arama yapar (cache desteği ile).

**Parameters:**
- `query` (str): Arama sorgusu  
- `**kwargs`: Diğer arama parametreleri

**Returns:**
- `List[SearchResult]`: Arama sonuçları

**Example:**
```python
async_search = AsyncSearchEngine(search_engine, max_workers=4)
results = await async_search.search_async("test query")
```

##### `clear_cache()`

Arama cache'ini temizler.

##### `get_cache_stats()`

Cache istatistiklerini getirir.

**Returns:**
- `Dict[str, Any]`: Cache istatistikleri
  ```python
  {
      "size": int,
      "hits": int,
      "misses": int,
      "hit_ratio": float
  }
  ```

### MemoryManager

Memory yönetimi ve optimizasyon.

#### Methods

##### `get_memory_usage()`

Mevcut memory kullanımını getirir.

**Returns:**
- `float`: Memory kullanımı (MB)

##### `force_gc()`

Garbage collection'ı zorlar.

**Returns:**
- `Dict[str, Any]`: GC sonucu
  ```python
  {
      "collected_objects": int,
      "memory_before_mb": float,
      "memory_after_mb": float,
      "memory_freed_mb": float,
      "gc_time_ms": float
  }
  ```

##### `optimize_memory_usage()`

Memory kullanımını optimize eder.

### PerformanceTracker

Performans izleme ve metrikleri.

#### Methods

##### `record_search_time(time_ms)`

Arama süresini kaydeder.

**Parameters:**
- `time_ms` (float): Arama süresi (milisaniye)

##### `take_memory_snapshot()`

Memory snapshot alır.

**Returns:**
- `PerformanceMetrics`: Performans metrikleri

##### `get_performance_summary()`

Performans özetini getirir.

**Returns:**
- `Dict[str, Any]`: Performans özeti

## Utility API

### ConfigManager

Konfigürasyon yönetimi.

#### Methods

##### `get(key, default=None)`

Konfigürasyon değerini getirir.

**Parameters:**
- `key` (str): Konfigürasyon anahtarı (nokta notasyonu desteklenir)
- `default` (Any, optional): Varsayılan değer

**Returns:**
- `Any`: Konfigürasyon değeri

**Example:**
```python
config = ConfigManager("config.yaml")
theme = config.get("preferences.theme", "system")
db_path = config.get("database.path")
```

##### `set(key, value)`

Konfigürasyon değerini ayarlar.

##### `save()`

Konfigürasyonu dosyaya kaydeder.

### BackupManager

Otomatik yedekleme yöneticisi.

#### Methods

##### `create_backup()`

Manuel yedekleme oluşturur.

**Returns:**
- `str`: Yedekleme dosyası yolu

##### `restore_backup(backup_path)`

Yedeklemeden geri yükleme yapar.

**Parameters:**
- `backup_path` (str): Yedekleme dosyası yolu

**Returns:**
- `bool`: İşlem başarı durumu

##### `list_backups()`

Mevcut yedeklemeleri listeler.

**Returns:**
- `List[Dict[str, Any]]`: Yedekleme listesi

### FileWatcher

Dosya izleme servisi.

#### Methods

##### `start_watching(directory)`

Dizin izlemeyi başlatır.

**Parameters:**
- `directory` (str): İzlenecek dizin yolu

##### `stop_watching()`

İzlemeyi durdurur.

##### `get_status()`

İzleme durumunu getirir.

**Returns:**
- `Dict[str, Any]`: Durum bilgisi

## Exception Handling

### Exception Hierarchy

```python
MevzuatSystemException
├── SearchEngineException
│   ├── InvalidQueryException
│   ├── IndexNotFoundException
│   └── SearchTimeoutException
├── DocumentProcessingException
│   ├── UnsupportedFileTypeException
│   ├── FileSizeException
│   ├── TextExtractionException
│   └── DuplicateDocumentException
├── DatabaseException
│   ├── ConnectionException
│   ├── QueryException
│   └── IntegrityException
└── PerformanceException
    ├── MemoryException
    └── TimeoutException
```

### Error Codes

| Code | Exception | Açıklama |
|------|-----------|----------|
| 1001 | InvalidQueryException | Geçersiz arama sorgusu |
| 1002 | IndexNotFoundException | Arama indeksi bulunamadı |
| 2001 | UnsupportedFileTypeException | Desteklenmeyen dosya türü |
| 2002 | FileSizeException | Dosya boyutu limiti aşıldı |
| 3001 | DatabaseException | Veritabanı bağlantı hatası |
| 4001 | MemoryException | Memory limiti aşıldı |

### Error Handling Example

```python
try:
    results = search_engine.search("invalid query")
except InvalidQueryException as e:
    logger.error(f"Geçersiz sorgu: {e.message}")
    show_user_message("Lütfen geçerli bir arama sorgusu girin")
except SearchEngineException as e:
    logger.error(f"Arama hatası: {e}")
    show_user_message("Arama işlemi başarısız")
except Exception as e:
    logger.error(f"Beklenmeyen hata: {e}")
    show_user_message("Sistem hatası oluştu")
```

## Data Models

### SearchResult

Arama sonucu veri modeli.

```python
@dataclass
class SearchResult:
    id: int
    document_id: int
    document_title: str
    law_number: Optional[str]
    document_type: str
    article_number: Optional[str]
    title: Optional[str]
    content: str
    score: float
    match_type: str  # "exact", "semantic", "keyword", "mixed"
    highlights: List[str] = field(default_factory=list)
    is_repealed: bool = False
    is_amended: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### Document

Belge modeli.

```python
@dataclass
class Document:
    id: int
    title: str
    file_path: str
    document_type: str
    law_number: Optional[str]
    publication_date: Optional[datetime]
    content_hash: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### Article

Madde modeli.

```python
@dataclass
class Article:
    id: int
    document_id: int
    article_number: Optional[str]
    title: Optional[str]
    content: str
    is_repealed: bool = False
    is_amended: bool = False
    created_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### PerformanceMetrics

Performans metrikleri modeli.

```python
@dataclass
class PerformanceMetrics:
    memory_usage_mb: float
    cpu_usage_percent: float
    search_time_ms: float
    document_processing_time_ms: float
    cache_hit_ratio: float
    active_threads: int
    timestamp: datetime = field(default_factory=datetime.now)
```

### FacetedSearchResult

Gelişmiş arama sonucu modeli.

```python
@dataclass
class FacetedSearchResult:
    documents: List[SearchResult]
    facets: Dict[str, List[FacetValue]]
    total_count: int
    filtered_count: int
    query_time_ms: float
```

## Rate Limiting ve Throttling

Sistem performansını korumak için çeşitli limitlendirmeler mevcuttur:

### Search Rate Limits

```python
SEARCH_LIMITS = {
    "max_concurrent_searches": 5,
    "search_timeout_seconds": 30,
    "cache_ttl_seconds": 300,
    "max_results_per_search": 1000
}
```

### Document Processing Limits

```python
PROCESSING_LIMITS = {
    "max_file_size_mb": 50,
    "max_files_per_batch": 100,
    "max_concurrent_processes": 2,
    "processing_timeout_seconds": 120
}
```

## Versioning

API versiyonlama şeması: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes (geriye uyumsuz)
- **MINOR**: Yeni özellikler (geriye uyumlu)
- **PATCH**: Bug fix'ler (geriye uyumlu)

**Mevcut Version:** `1.0.2`

## Migration Guide

Eski versiyonlardan yeni versiyona geçiş kılavuzu:

### v1.0.1 → v1.0.2

1. **SOLID Refactoring**: `main_window.py` yerine `main_window_refactored.py` kullanın
2. **Performance API**: Yeni `AsyncSearchEngine` ve `MemoryManager` sınıfları
3. **Testing**: Yeni test framework'ü entegre edildi

### Deprecated Methods

| Method | Deprecated Since | Alternative |
|--------|------------------|-------------|
| `search_engine.simple_search()` | v1.0.1 | `search_engine.search()` |
| `document_processor.sync_process()` | v1.0.2 | `document_processor.process_file()` |
