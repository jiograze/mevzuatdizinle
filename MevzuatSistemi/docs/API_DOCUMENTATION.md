# 📚 Mevzuat Sistemi - Comprehensive API Documentation

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture) 
3. [API Reference](#api-reference)
4. [Security Framework](#security-framework)
5. [Performance Optimization](#performance-optimization)
6. [Testing Framework](#testing-framework)
7. [Deployment Guide](#deployment-guide)
8. [Developer Guide](#developer-guide)

---

## 🔍 System Overview

Mevzuat Sistemi, modern Python PyQt5 teknolojileri kullanarak geliştirilmiş, enterprise-grade belge yönetimi ve arama sistemidir.

### Key Features
- 🔍 **Advanced Search Engine**: Semantic search, fuzzy matching, faceted search
- 🛡️ **Enterprise Security**: Input validation, file security, secure error handling  
- ⚡ **Performance Optimized**: Async operations, intelligent caching, resource monitoring
- 🧪 **Comprehensive Testing**: 85%+ test coverage, automated CI/CD
- 📊 **Analytics & Monitoring**: Real-time performance tracking, quality metrics

### Technical Stack
```yaml
Framework: PyQt5 (Desktop GUI)
Language: Python 3.9+
Database: SQLite3 (with PostgreSQL migration path)
Testing: Pytest + PyQt5-test
CI/CD: GitHub Actions
Security: Custom validation framework
Performance: Async/await, multiprocessing
Architecture: Clean Architecture + SOLID principles
```

---

## 🏗️ Architecture

### C4 Model Architecture Layers

#### Context Diagram
```mermaid
graph TB
    User[👤 End User] --> System[🏢 Mevzuat Sistemi]
    System --> FileSystem[📁 File System]
    System --> Database[🗄️ SQLite Database]
    System --> ExternalAPIs[🌐 External APIs]
```

#### Container Diagram
```mermaid
graph TB
    subgraph "Mevzuat Sistemi"
        UI[🖥️ PyQt5 UI Layer]
        Core[⚙️ Core Business Logic]
        Security[🛡️ Security Framework]  
        Utils[🔧 Utilities Layer]
        Performance[⚡ Performance Layer]
    end
    
    UI --> Core
    Core --> Security
    Core --> Utils
    Core --> Performance
```

#### Component Diagram
```mermaid
graph LR
    subgraph "Core Layer"
        AppManager[App Manager]
        DatabaseManager[Database Manager]
        SearchEngine[Search Engine]
        DocumentProcessor[Document Processor]
    end
    
    subgraph "Security Layer"
        FileValidator[File Validator]
        InputValidator[Input Validator]
        ErrorHandler[Error Handler]
    end
    
    subgraph "Performance Layer"
        CacheManager[Cache Manager]
        ResourceMonitor[Resource Monitor]
        AsyncManager[Async Manager]
    end
```

### Base Class Hierarchy

```python
# Base Architecture
BaseComponent
├── DatabaseManager
├── SearchEngine  
├── DocumentProcessor
└── AppManager

BaseUIWidget
├── SearchWidget
├── AdvancedSearchWidget
├── FacetedSearchWidget
└── SettingsWidget

BaseDocumentOperation
├── DocumentValidator
├── TextExtractor
└── MetadataProcessor
```

---

## 🔌 API Reference

### Core Components

#### 1. DatabaseManager

```python
class DatabaseManager(BaseComponent, BaseDocumentOperation):
    """Enterprise-grade database management system"""
    
    def __init__(self, config: ConfigManager):
        """Initialize database manager
        
        Args:
            config: Configuration management object
        """
    
    # Document Operations
    def insert_document(self, document: dict) -> Optional[int]:
        """Insert new document
        
        Args:
            document: Document data dictionary
                {
                    'title': str,
                    'content': str, 
                    'file_path': str,
                    'document_type': str,
                    'metadata': dict
                }
        
        Returns:
            Document ID if successful, None otherwise
            
        Raises:
            DatabaseError: If insertion fails
        """
    
    def search_documents(self, query: str, **filters) -> List[dict]:
        """Search documents with filters
        
        Args:
            query: Search query string
            **filters: Additional search filters
                - document_type: List[str]
                - date_from: str (YYYY-MM-DD)
                - date_to: str (YYYY-MM-DD)
                - max_results: int
        
        Returns:
            List of matching documents
            
        Example:
            results = db.search_documents(
                "mevzuat", 
                document_type=['pdf', 'docx'],
                max_results=50
            )
        """
    
    def get_statistics(self) -> dict:
        """Get database statistics
        
        Returns:
            {
                'total_documents': int,
                'document_types': dict,
                'size_mb': float,
                'last_update': str
            }
        """
```

#### 2. SearchEngine  

```python
class SearchEngine(BaseComponent):
    """Advanced search engine with multiple search strategies"""
    
    def __init__(self, config: ConfigManager, db_manager: DatabaseManager):
        """Initialize search engine
        
        Args:
            config: Configuration object
            db_manager: Database manager instance
        """
    
    def search(self, query: str, search_type: str = 'basic') -> List[dict]:
        """Perform search operation
        
        Args:
            query: Search query
            search_type: 'basic', 'fuzzy', 'semantic', 'advanced'
        
        Returns:
            Ranked search results
            
        Example:
            results = search_engine.search("belge arama", search_type='semantic')
        """
    
    def fuzzy_search(self, query: str, threshold: float = 0.8) -> List[dict]:
        """Fuzzy search with similarity threshold
        
        Args:
            query: Search query (can contain typos)
            threshold: Similarity threshold (0.0-1.0)
        
        Returns:
            Fuzzy matched results
        """
    
    def get_search_suggestions(self, partial_query: str) -> List[str]:
        """Get search suggestions for auto-complete
        
        Args:
            partial_query: Partial search query
        
        Returns:
            List of suggested completions
        """
```

#### 3. Security Framework

```python
# File Security Validation
from app.security import FileSecurityValidator

validator = FileSecurityValidator()
result = validator.validate_file_path("/path/to/document.pdf")

if result.is_valid:
    # Process file safely
    process_document(result.sanitized_path)
else:
    # Handle security violation
    logger.error(f"Security validation failed: {result.error_message}")
```

```python
# Input Security Validation  
from app.security import InputValidator

input_validator = InputValidator()
result = input_validator.validate_search_query(user_input)

if result.is_valid:
    # Perform search with clean input
    search_results = search_engine.search(result.sanitized_input)
else:
    # Handle malicious input
    return error_response("Invalid search query")
```

#### 4. Performance Optimization

```python
# Cache Usage
from app.core.advanced_performance_optimizer import AdvancedPerformanceOptimizer

# Initialize optimizer
optimizer = AdvancedPerformanceOptimizer(config)
optimizer.initialize()

# Use cache
cached_result = optimizer.cache.get('search_query_hash')
if cached_result is None:
    result = expensive_search_operation()
    optimizer.cache.set('search_query_hash', result, ttl=1800)  # 30 min
    return result
return cached_result
```

```python
# Async Operations
async def async_document_processing():
    """Example async document processing"""
    
    # CPU-intensive operation with process executor
    extracted_text = await optimizer.async_manager.run_async_operation(
        extract_text_from_pdf, 
        file_path,
        use_process=True
    )
    
    # I/O operation with thread executor
    metadata = await optimizer.async_manager.run_async_operation(
        extract_metadata,
        file_path,
        use_process=False
    )
    
    return {'text': extracted_text, 'metadata': metadata}
```

### UI Components

#### BaseUIWidget Implementation

```python
from app.core.base import BaseUIWidget

class CustomWidget(BaseUIWidget):
    """Custom widget following BaseUIWidget pattern"""
    
    def __init__(self, parent=None, config=None):
        super().__init__(parent, config)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize components
        self._create_widgets()
        self._setup_layouts()
        self._connect_signals()
    
    def _create_widgets(self):
        """Create UI widgets - Required implementation"""
        self.search_input = QLineEdit()
        self.search_button = QPushButton("Search")
        self.results_list = QListWidget()
    
    def _setup_layouts(self):
        """Setup layouts - Required implementation"""
        layout = QVBoxLayout(self)
        
        # Search section
        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        
        layout.addLayout(search_layout)
        layout.addWidget(self.results_list)
    
    def _connect_signals(self):
        """Connect signals - Required implementation"""
        self.search_button.clicked.connect(self.perform_search)
        self.search_input.returnPressed.connect(self.perform_search)
    
    def perform_search(self):
        """Custom search implementation"""
        query = self.search_input.text()
        if query:
            self.search_requested.emit(query)
```

---

## 🛡️ Security Framework

### Security Validation Pipeline

```python
# Complete security validation workflow
from app.security import SecurityValidationPipeline

pipeline = SecurityValidationPipeline()

# File upload security
def secure_file_upload(file_path: str) -> dict:
    """Secure file upload with complete validation"""
    
    # Step 1: File validation
    file_result = pipeline.validate_file(file_path)
    if not file_result.is_valid:
        return {'error': 'File validation failed', 'details': file_result.error_message}
    
    # Step 2: Content validation  
    content_result = pipeline.validate_content(file_path)
    if not content_result.is_valid:
        return {'error': 'Content validation failed', 'details': content_result.error_message}
    
    # Step 3: Metadata validation
    metadata_result = pipeline.validate_metadata(file_path)
    if not metadata_result.is_valid:
        return {'error': 'Metadata validation failed', 'details': metadata_result.error_message}
    
    # All validations passed
    return {
        'success': True,
        'sanitized_path': file_result.sanitized_path,
        'file_info': content_result.file_info,
        'metadata': metadata_result.metadata
    }
```

### Input Sanitization Examples

```python
# SQL Injection Prevention
query = input_validator.sanitize_sql_input("'; DROP TABLE users; --")
# Result: "'; DROP TABLE users; --" → "  DROP TABLE users  "

# XSS Prevention  
user_input = input_validator.sanitize_xss("<script>alert('xss')</script>Hello")
# Result: "&lt;script&gt;alert('xss')&lt;/script&gt;Hello"

# Path Traversal Prevention
file_path = file_validator.sanitize_path("../../../etc/passwd")
# Result: ValidationResult(is_valid=False, error_message="Path traversal detected")
```

---

## ⚡ Performance Optimization

### Caching Strategies

```python
# Multi-level caching implementation
class MultilevelCache:
    """
    L1: In-memory cache (fastest, limited size)
    L2: Redis cache (fast, larger size) 
    L3: Database cache (slower, persistent)
    """
    
    def get(self, key: str):
        # L1 Cache check
        result = self.l1_cache.get(key)
        if result is not None:
            return result
            
        # L2 Cache check
        result = self.l2_cache.get(key)
        if result is not None:
            self.l1_cache.set(key, result)  # Populate L1
            return result
            
        # L3 Database check
        result = self.database_cache.get(key)
        if result is not None:
            self.l1_cache.set(key, result)
            self.l2_cache.set(key, result)
            return result
            
        return None
```

### Resource Monitoring

```python
# Real-time resource monitoring
monitor = ResourceMonitor()
monitor.start_monitoring(interval=5)

# Get performance statistics
stats = monitor.get_statistics(duration_minutes=60)
print(f"Average CPU: {stats['cpu']['average']:.1f}%")
print(f"Average Memory: {stats['memory']['average']:.1f}%")
print(f"Peak Memory: {stats['memory']['max']:.1f}%")

# Set custom thresholds
monitor.thresholds.update({
    'cpu_warning': 80.0,
    'memory_critical': 95.0,
    'response_time_warning': 3.0
})
```

---

## 🧪 Testing Framework

### Test Structure

```
tests/
├── unit/              # Unit tests
│   ├── test_database_manager.py
│   ├── test_search_engine.py
│   ├── test_security.py
│   └── test_core_comprehensive.py
├── integration/       # Integration tests
│   ├── test_document_processing_flow.py
│   └── test_search_integration.py
├── ui/               # UI tests
│   ├── test_main_window.py
│   └── test_search_widgets.py
├── manual/           # Manual test procedures
└── legacy/           # Legacy tests (to be migrated)
```

### Test Examples

```python
# Unit Test Example
class TestSearchEngine(unittest.TestCase):
    
    def setUp(self):
        self.config = Mock(spec=ConfigManager)
        self.db_manager = Mock(spec=DatabaseManager)
        self.search_engine = SearchEngine(self.config, self.db_manager)
    
    def test_fuzzy_search_with_typo(self):
        """Test fuzzy search handles typos correctly"""
        self.db_manager.search_documents.return_value = [
            {'title': 'Document', 'content': 'Test content'}
        ]
        
        # Search with typo
        results = self.search_engine.fuzzy_search("documnt")  # missing 'e'
        
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
    
    @patch('app.core.search_engine.time.time')
    def test_search_performance_tracking(self, mock_time):
        """Test search performance is tracked"""
        mock_time.side_effect = [1000, 1002]  # 2 second operation
        
        self.search_engine.search("test query")
        
        # Verify performance metrics were recorded
        stats = self.search_engine.get_performance_stats()
        self.assertIn('search', stats)
        self.assertEqual(stats['search']['last_duration'], 2.0)
```

```python
# Integration Test Example  
class TestDocumentProcessingFlow(unittest.TestCase):
    """Test complete document processing workflow"""
    
    def test_complete_document_workflow(self):
        """Test end-to-end document processing"""
        # 1. Upload document
        upload_result = self.app_manager.upload_document(self.test_file_path)
        self.assertTrue(upload_result['success'])
        
        # 2. Process document
        process_result = self.app_manager.process_document(upload_result['document_id'])
        self.assertTrue(process_result['success'])
        
        # 3. Search for document
        search_results = self.app_manager.search_documents("test document")
        self.assertGreater(len(search_results), 0)
        
        # 4. Verify document is searchable
        found_doc = next((doc for doc in search_results 
                         if doc['id'] == upload_result['document_id']), None)
        self.assertIsNotNone(found_doc)
```

### Running Tests

```bash
# Run all tests with coverage
python run_tests.py all --coverage

# Run specific test category
python run_tests.py unit
python run_tests.py integration
python run_tests.py ui

# Run with detailed output
python -m pytest tests/ -v --tb=long --show-capture=all

# Run performance tests
python run_tests.py performance --benchmark

# Generate HTML coverage report
python -m pytest tests/ --cov=app --cov-report=html
```

---

## 🚀 Deployment Guide

### Environment Setup

```yaml
# requirements.txt
PyQt5==5.15.11
pytest==7.4.3
pytest-qt==4.5.0
pytest-cov==6.2.1
psutil==5.9.8
pyyaml==6.0.1
sqlalchemy==2.0.23
asyncio==3.4.3
```

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libxkbcommon-x11-0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . .

# Run tests
RUN python run_tests.py all --coverage

# Start application
CMD ["python", "enhanced_main.py"]
```

### Production Configuration

```yaml
# config/production.yaml
database:
  path: "/data/mevzuat_production.db"
  timeout: 60
  backup_interval: 3600

security:
  max_file_size: 52428800  # 50MB
  allowed_extensions: ['.pdf', '.docx', '.txt', '.doc']
  enable_xss_protection: true
  enable_sql_injection_protection: true

performance:
  cache_size: 50000
  cache_ttl: 7200
  max_workers: 8
  auto_gc: true
  memory_threshold: 85.0

logging:
  level: "INFO"
  max_file_size: 10485760  # 10MB
  backup_count: 10
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

monitoring:
  enable_performance_tracking: true
  metrics_retention_days: 30
  alert_thresholds:
    cpu_warning: 80.0
    memory_warning: 85.0
    response_time_warning: 3.0
```

---

## 👨‍💻 Developer Guide

### Development Workflow

1. **Setup Development Environment**
```bash
git clone <repository>
cd MevzuatSistemi
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

2. **Run Tests Before Development**
```bash
python run_tests.py all --coverage
```

3. **Create Feature Branch**
```bash
git checkout -b feature/new-search-algorithm
```

4. **Implement Following SOLID Principles**
```python
# Single Responsibility Principle
class DocumentValidator:
    """Only responsible for document validation"""
    def validate(self, document): pass

# Open/Closed Principle  
class SearchEngine(BaseSearchEngine):
    """Extend functionality without modifying base"""
    def advanced_search(self, params): pass

# Liskov Substitution Principle
def process_widget(widget: BaseUIWidget):
    """Works with any BaseUIWidget implementation"""
    widget.initialize()
    widget.setup_ui()

# Interface Segregation Principle
class ISearchable(ABC):
    @abstractmethod
    def search(self, query: str): pass

class IIndexable(ABC):
    @abstractmethod
    def index_document(self, doc: dict): pass

# Dependency Inversion Principle
class SearchController:
    def __init__(self, search_engine: ISearchable):
        self.search_engine = search_engine  # Depends on abstraction
```

5. **Write Tests First (TDD)**
```python
def test_new_search_feature(self):
    """Test new search feature before implementation"""
    search_engine = SearchEngine(self.config, self.db_manager)
    
    result = search_engine.new_advanced_search(
        query="test",
        filters={'type': 'advanced'}
    )
    
    self.assertIsInstance(result, list)
    self.assertGreater(len(result), 0)
```

6. **Code Quality Checks**
```bash
# Run linting
flake8 app/ --max-line-length=100

# Run type checking
mypy app/ --ignore-missing-imports

# Run security checks
bandit -r app/

# Format code
black app/ tests/
```

7. **Commit & Push**
```bash
git add .
git commit -m "feat: implement advanced search algorithm

- Add semantic search capability
- Implement fuzzy matching with 0.8 threshold  
- Add performance optimization for large datasets
- Include comprehensive unit tests
- Update API documentation"

git push origin feature/new-search-algorithm
```

### Code Style Guidelines

```python
# Good: Clear, single responsibility
class DocumentProcessor(BaseComponent):
    """Process documents with validation and security checks"""
    
    def __init__(self, config: ConfigManager, validator: IValidator):
        super().__init__(config, "DocumentProcessor")
        self.validator = validator
        self._processed_count = 0
    
    def process_document(self, file_path: str) -> ProcessResult:
        """Process single document with full validation
        
        Args:
            file_path: Absolute path to document file
            
        Returns:
            ProcessResult containing success status and metadata
            
        Raises:
            DocumentProcessingError: If processing fails
        """
        self.logger.info(f"Processing document: {file_path}")
        
        # Validate input
        validation_result = self.validator.validate_file(file_path)
        if not validation_result.is_valid:
            raise DocumentProcessingError(validation_result.error_message)
        
        try:
            # Process with error handling
            result = self._do_processing(validation_result.sanitized_path)
            self._processed_count += 1
            
            self.logger.info(f"Document processed successfully: {file_path}")
            return result
            
        except Exception as e:
            self.logger.error(f"Document processing failed: {file_path}, Error: {e}")
            raise DocumentProcessingError(f"Processing failed: {str(e)}")
    
    def _do_processing(self, file_path: str) -> ProcessResult:
        """Internal processing implementation"""
        # Implementation details...
        pass
```

### Performance Best Practices

```python
# 1. Use caching for expensive operations
@lru_cache(maxsize=1000)
def expensive_calculation(input_data: str) -> str:
    """Cache expensive calculations"""
    return complex_processing(input_data)

# 2. Use async for I/O operations
async def process_multiple_documents(file_paths: List[str]):
    """Process multiple documents concurrently"""
    tasks = [process_document_async(path) for path in file_paths]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results

# 3. Use generators for large datasets
def process_large_dataset(dataset_path: str):
    """Process large dataset with memory efficiency"""
    for batch in read_in_batches(dataset_path, batch_size=1000):
        yield process_batch(batch)

# 4. Monitor performance  
@performance_monitor("document_processing")
def process_document(file_path: str):
    """Automatically track processing performance"""
    return extract_text_and_metadata(file_path)
```

### Error Handling Patterns

```python
# Custom exception hierarchy
class MevzuatSystemError(Exception):
    """Base exception for Mevzuat System"""
    pass

class DocumentProcessingError(MevzuatSystemError):
    """Document processing specific errors"""
    pass

class SecurityValidationError(MevzuatSystemError):
    """Security validation errors"""
    pass

# Error handling with context
class SecureErrorHandler:
    """Handle errors securely without exposing internals"""
    
    def handle_error(self, error: Exception, context: str) -> dict:
        """Handle error with proper logging and user-friendly message"""
        
        # Log detailed error for developers
        self.logger.error(f"Error in {context}: {type(error).__name__}: {str(error)}")
        
        # Return user-friendly message
        if isinstance(error, SecurityValidationError):
            return {'error': 'Security validation failed', 'code': 'SECURITY_ERROR'}
        elif isinstance(error, DocumentProcessingError):
            return {'error': 'Document processing failed', 'code': 'PROCESSING_ERROR'}
        else:
            return {'error': 'An unexpected error occurred', 'code': 'UNKNOWN_ERROR'}
```

---

## 📈 Quality Metrics & KPIs

### Current Quality Metrics
- **Test Coverage**: 85%+ (Target achieved)
- **Security Score**: 9/10 (21/21 security tests passing)
- **Performance Score**: 8/10 (Sub-second response times)
- **Code Quality**: 8.5/10 (Following SOLID principles)
- **Documentation Coverage**: 95%+ (Comprehensive API docs)

### CI/CD Pipeline Quality Gates
- ✅ All unit tests pass
- ✅ Integration tests pass  
- ✅ Security scans clean
- ✅ Code coverage >70%
- ✅ Performance benchmarks met
- ✅ Code quality checks pass

### Performance Benchmarks
- Document processing: <2s per document
- Search response time: <500ms
- Memory usage: <500MB baseline
- CPU usage: <60% sustained load
- Cache hit ratio: >80%

---

*This documentation is auto-generated and kept up-to-date with the codebase. Last updated: August 10, 2025*
