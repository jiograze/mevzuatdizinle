"""
Veritabanı yöneticisi - SQLite tabloları ve işlemleri
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager
from datetime import datetime, timedelta

class DatabaseManager:
    """SQLite veritabanı yönetim sınıfı"""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        self.db_path = config_manager.get_db_path()
        self.connection: Optional[sqlite3.Connection] = None
        
        # Performans ayarları
        self.journal_mode = config_manager.get('performance.sqlite_journal_mode', 'WAL')
        self.cache_size_mb = config_manager.get('performance.sqlite_cache_size_mb', 64)
    
    def initialize(self):
        """Veritabanını başlat ve tabloları oluştur"""
        try:
            # DB klasörünü oluştur
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Bağlantıyı kur
            self.connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                timeout=30.0
            )
            
            # Performans ayarları
            self._configure_database()
            
            # Tabloları oluştur
            self._create_tables()
            
            # İndeksleri oluştur
            self._create_indexes()
            
            self.logger.info(f"Veritabanı başlatıldı: {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"Veritabanı başlatma hatası: {e}")
            raise
    
    def _configure_database(self):
        """Veritabanı performans ayarları"""
        cursor = self.connection.cursor()
        
        # Journal modu
        cursor.execute(f"PRAGMA journal_mode={self.journal_mode}")
        
        # Cache boyutu (sayfa sayısı olarak, her sayfa ~1KB)
        cache_pages = self.cache_size_mb * 1024
        cursor.execute(f"PRAGMA cache_size={cache_pages}")
        
        # Foreign key kontrolü
        cursor.execute("PRAGMA foreign_keys=ON")
        
        # Temp store bellek kullanımı
        cursor.execute("PRAGMA temp_store=MEMORY")
        
        # Synchronous mod (performans için)
        cursor.execute("PRAGMA synchronous=NORMAL")
        
        cursor.close()
        self.connection.commit()
    
    def _create_tables(self):
        """Tüm tabloları oluştur"""
        
        # Belgeler tablosu
        documents_table = """
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            law_number TEXT,
            document_type TEXT NOT NULL,
            category TEXT,
            subcategory TEXT,
            original_filename TEXT,
            stored_filename TEXT,
            file_path TEXT NOT NULL,
            file_hash TEXT UNIQUE,  -- Unique constraint eklendi
            file_size INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            effective_date TEXT,
            publication_date TEXT,
            status TEXT DEFAULT 'ACTIVE',
            version_number INTEGER DEFAULT 1,
            parent_document_id INTEGER REFERENCES documents(id),
            metadata TEXT -- JSON formatında ek bilgiler
        )
        """
        
        # Maddeler tablosu
        articles_table = """
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            article_number TEXT,
            title TEXT,
            content TEXT NOT NULL,
            content_clean TEXT, -- Temizlenmiş metin (arama için)
            seq_index INTEGER, -- Belgede sıralama
            is_repealed BOOLEAN DEFAULT FALSE,
            is_amended BOOLEAN DEFAULT FALSE,
            amendment_info TEXT, -- Değişiklik bilgisi
            article_type TEXT DEFAULT 'MADDE', -- MADDE, FIKRA, BEND, vb.
            parent_article_id INTEGER REFERENCES articles(id),
            created_at TEXT NOT NULL,
            updated_at TEXT
        )
        """
        
        # Kullanıcı kategorileri
        user_categories_table = """
        CREATE TABLE IF NOT EXISTS user_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            color TEXT DEFAULT '#808080',
            description TEXT,
            parent_id INTEGER REFERENCES user_categories(id),
            created_at TEXT NOT NULL,
            updated_at TEXT
        )
        """
        
        # Kullanıcı notları
        user_notes_table = """
        CREATE TABLE IF NOT EXISTS user_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER REFERENCES articles(id) ON DELETE CASCADE,
            document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
            title TEXT,
            content TEXT NOT NULL,
            note_type TEXT DEFAULT 'USER', -- USER, SYSTEM, AUTO
            created_at TEXT NOT NULL,
            updated_at TEXT
        )
        """
        
        # Madde-kategori ilişkileri
        article_categories_table = """
        CREATE TABLE IF NOT EXISTS article_categories (
            article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
            category_id INTEGER NOT NULL REFERENCES user_categories(id) ON DELETE CASCADE,
            created_at TEXT NOT NULL,
            PRIMARY KEY (article_id, category_id)
        )
        """
        
        # Madde ilişkileri
        article_relations_table = """
        CREATE TABLE IF NOT EXISTS article_relations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
            target_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
            relation_type TEXT NOT NULL, -- REFERENCE, AMENDMENT, REPEAL, RELATED
            confidence REAL DEFAULT 1.0,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            UNIQUE(source_id, target_id, relation_type)
        )
        """
        
        # Arama geçmişi
        search_history_table = """
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            query_type TEXT DEFAULT 'MIXED', -- KEYWORD, SEMANTIC, MIXED
            results_count INTEGER DEFAULT 0,
            execution_time_ms REAL,
            created_at TEXT NOT NULL
        )
        """
        
        # Favoriler
        favorites_table = """
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER REFERENCES articles(id) ON DELETE CASCADE,
            document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
            title TEXT,
            notes TEXT,
            created_at TEXT NOT NULL
        )
        """
        
        # İşlem geçmişi (undo için)
        operations_table = """
        CREATE TABLE IF NOT EXISTS operations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operation_type TEXT NOT NULL, -- INSERT, UPDATE, DELETE, MOVE
            table_name TEXT NOT NULL,
            record_id INTEGER,
            old_values TEXT, -- JSON formatında eski değerler
            new_values TEXT, -- JSON formatında yeni değerler
            description TEXT,
            can_undo BOOLEAN DEFAULT TRUE,
            created_at TEXT NOT NULL
        )
        """
        
        # FTS tablosu (Full Text Search)
        fts_table = """
        CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
            title, 
            content, 
            content_clean, 
            article_number,
            content=articles,
            content_rowid=id
        )
        """
        
        # Tablolar listesi
        tables = [
            documents_table,
            articles_table,
            user_categories_table,
            user_notes_table,
            article_categories_table,
            article_relations_table,
            search_history_table,
            favorites_table,
            operations_table,
            fts_table
        ]
        
        cursor = self.connection.cursor()
        
        for table in tables:
            cursor.execute(table)
            
        cursor.close()
        self.connection.commit()
        
        self.logger.info("Tüm tablolar oluşturuldu")
    
    def _create_indexes(self):
        """Performans indekslerini oluştur"""
        indexes = [
            # Belgeler indeksleri
            "CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(document_type)",
            "CREATE INDEX IF NOT EXISTS idx_documents_law_number ON documents(law_number)",
            "CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status)",
            "CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_documents_hash ON documents(file_hash)",
            
            # Maddeler indeksleri
            "CREATE INDEX IF NOT EXISTS idx_articles_document_id ON articles(document_id)",
            "CREATE INDEX IF NOT EXISTS idx_articles_number ON articles(article_number)",
            "CREATE INDEX IF NOT EXISTS idx_articles_seq_index ON articles(seq_index)",
            "CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(is_repealed, is_amended)",
            "CREATE INDEX IF NOT EXISTS idx_articles_type ON articles(article_type)",
            
            # İlişkiler indeksleri
            "CREATE INDEX IF NOT EXISTS idx_article_relations_source ON article_relations(source_id)",
            "CREATE INDEX IF NOT EXISTS idx_article_relations_target ON article_relations(target_id)",
            "CREATE INDEX IF NOT EXISTS idx_article_relations_type ON article_relations(relation_type)",
            
            # Notlar indeksleri
            "CREATE INDEX IF NOT EXISTS idx_user_notes_article ON user_notes(article_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_notes_document ON user_notes(document_id)",
            
            # Arama geçmişi indeksi
            "CREATE INDEX IF NOT EXISTS idx_search_history_created ON search_history(created_at)",
            
            # Operasyonlar indeksi
            "CREATE INDEX IF NOT EXISTS idx_operations_created ON operations(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_operations_table_record ON operations(table_name, record_id)"
        ]
        
        cursor = self.connection.cursor()
        
        for index in indexes:
            cursor.execute(index)
        
        cursor.close()
        self.connection.commit()
        
        self.logger.info("Tüm indeksler oluşturuldu")
    
    @contextmanager
    def transaction(self):
        """Transaction context manager"""
        cursor = self.connection.cursor()
        try:
            yield cursor
            self.connection.commit()
        except sqlite3.Error:
            self.connection.rollback()
            raise
        finally:
            cursor.close()
    
    def insert_document(self, document_data: Dict[str, Any]) -> int:
        """Yeni belge ekle"""
        required_fields = ['title', 'document_type', 'file_path']
        for field in required_fields:
            if field not in document_data:
                raise ValueError(f"Gerekli alan eksik: {field}")
        
        # Varsayılan değerler
        document_data.setdefault('created_at', datetime.now().isoformat())
        document_data.setdefault('status', 'ACTIVE')
        document_data.setdefault('version_number', 1)
        
        with self.transaction() as cursor:
            # Validate column names to prevent SQL injection
            valid_columns = ['title', 'law_number', 'document_type', 'category', 'subcategory', 
                           'original_filename', 'stored_filename', 'file_path', 'file_hash', 
                           'file_size', 'created_at', 'updated_at', 'effective_date', 
                           'publication_date', 'status', 'version_number', 'parent_document_id', 'metadata']
            
            # Filter to only allow valid columns
            safe_document_data = {k: v for k, v in document_data.items() if k in valid_columns}
            
            if not safe_document_data:
                raise ValueError("No valid columns found in document data")
            
            placeholders = ', '.join(['?' for _ in safe_document_data])
            columns = ', '.join(safe_document_data.keys())
            
            query = f"INSERT INTO documents ({columns}) VALUES ({placeholders})"
            cursor.execute(query, list(safe_document_data.values()))
            
            doc_id = cursor.lastrowid
            self.logger.info(f"Belge eklendi: {doc_id}")
            return doc_id
    
    def insert_article(self, article_data: Dict[str, Any]) -> int:
        """Yeni madde ekle"""
        if 'document_id' not in article_data or 'content' not in article_data:
            raise ValueError("document_id ve content alanları gerekli")
        
        article_data.setdefault('created_at', datetime.now().isoformat())
        
        with self.transaction() as cursor:
            # Validate column names to prevent SQL injection
            valid_columns = ['document_id', 'article_number', 'title', 'content', 'content_clean', 
                           'seq_index', 'article_type', 'is_repealed', 'is_amended', 'created_at']
            
            # Filter to only allow valid columns
            safe_article_data = {k: v for k, v in article_data.items() if k in valid_columns}
            
            if not safe_article_data:
                raise ValueError("No valid columns found in article data")
            
            placeholders = ', '.join(['?' for _ in safe_article_data])
            columns = ', '.join(safe_article_data.keys())
            
            query = f"INSERT INTO articles ({columns}) VALUES ({placeholders})"
            cursor.execute(query, list(safe_article_data.values()))
            
            article_id = cursor.lastrowid
            
            # FTS tablosuna da ekle
            if 'title' in article_data and 'content' in article_data:
                cursor.execute("""
                    INSERT INTO articles_fts (rowid, title, content, content_clean, article_number)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    article_id,
                    article_data.get('title', ''),
                    article_data.get('content', ''),
                    article_data.get('content_clean', ''),
                    article_data.get('article_number', '')
                ))
                return cursor.lastrowid
        
        def get_recent_operations(self, limit: int = 20) -> List[Dict[str, Any]]:
            """Son işlemleri getir"""
        
        row = cursor.fetchone()
        cursor.close()
        
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None
    
    def get_articles_by_document(self, doc_id: int) -> List[Dict[str, Any]]:
        """Belgeye ait maddeleri getir"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT * FROM articles 
            WHERE document_id = ? 
            ORDER BY seq_index, article_number
        """, (doc_id,))
        
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        cursor.close()
        return results
    
    def add_search_to_history(self, query: str, query_type: str, 
                            results_count: int, execution_time_ms: float):
        """Arama geçmişine ekle"""
        with self.transaction() as cursor:
            cursor.execute("""
                INSERT INTO search_history 
                (query, query_type, results_count, execution_time_ms, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (query, query_type, results_count, execution_time_ms, datetime.now().isoformat()))
    
    def get_search_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Arama geçmişini getir"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT * FROM search_history 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,))
        
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        cursor.close()
        return results
    
    def close(self):
        """Veritabanı bağlantısını kapat"""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.logger.info("Veritabanı bağlantısı kapatıldı")
    
    def vacuum(self):
        """Veritabanı bakımı (VACUUM)"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("VACUUM")
            cursor.close()
            self.logger.info("Veritabanı VACUUM tamamlandı")
        except Exception as e:
            self.logger.error(f"VACUUM hatası: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Veritabanı istatistikleri"""
        cursor = self.connection.cursor()
        
        stats = {}
        
        # Tablo sayıları
        tables = ['documents', 'articles', 'user_notes', 'search_history', 'favorites']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[f"{table}_count"] = cursor.fetchone()[0]
        
        # Dosya boyutu
        if self.db_path.exists():
            stats['file_size_mb'] = self.db_path.stat().st_size / (1024 * 1024)
        
        cursor.close()
        return stats
    
    # === OPERATIONS (UNDO) METHODS ===
    
    def log_operation(self, operation_type: str, table_name: str, 
                     record_id: int = None, old_values: Dict = None, 
                     new_values: Dict = None, description: str = None):
        """İşlemi log'la (undo için)"""
        import json
        
        with self.transaction() as cursor:
            cursor.execute("""
                INSERT INTO operations 
                (operation_type, table_name, record_id, old_values, 
                 new_values, description, can_undo, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                operation_type,
                table_name, 
                record_id,
                json.dumps(old_values) if old_values else None,
                json.dumps(new_values) if new_values else None,
                description,
                True,  # can_undo
                datetime.now().isoformat()
            ))
            return cursor.lastrowid
    
    def get_recent_operations(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Son işlemleri getir"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT * FROM operations 
            WHERE can_undo = TRUE
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,))
        
        columns = [desc[0] for desc in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            operation = dict(zip(columns, row))
            
            # JSON verilerini parse et
            import json
            if operation.get('old_values'):
                try:
                    operation['old_values'] = json.loads(operation['old_values'])
                except:
                    operation['old_values'] = None
                    
            if operation.get('new_values'):
                try:
                    operation['new_values'] = json.loads(operation['new_values'])
                except:
                    operation['new_values'] = None
            
            results.append(operation)
        
        cursor.close()
        return results
    
    def undo_operation(self, operation_id: int) -> bool:
        """Bir işlemi geri al"""
        import json
        
        cursor = self.connection.cursor()
        
        # Operation'u getir
        cursor.execute("""
            SELECT * FROM operations 
            WHERE id = ? AND can_undo = TRUE
        """, (operation_id,))
        
        operation = cursor.fetchone()
        if not operation:
            self.logger.warning(f"Geri alınacak işlem bulunamadı: {operation_id}")
            return False
        
        columns = [desc[0] for desc in cursor.description]
        op_dict = dict(zip(columns, operation))
        
        try:
            # Operation tipine göre geri alma işlemi yap
            operation_type = op_dict['operation_type']
            table_name = op_dict['table_name']
            record_id = op_dict['record_id']
            
            if operation_type == 'INSERT':
                # INSERT'i geri al = DELETE
                cursor.execute(f"DELETE FROM {table_name} WHERE id = ?", (record_id,))
                
            elif operation_type == 'DELETE':
                # DELETE'i geri al = INSERT
                if op_dict['old_values']:
                    old_values = json.loads(op_dict['old_values'])
                    columns_str = ', '.join(old_values.keys())
                    placeholders = ', '.join(['?' for _ in old_values])
                    
                    cursor.execute(f"""
                        INSERT INTO {table_name} ({columns_str}) 
                        VALUES ({placeholders})
                    """, list(old_values.values()))
                    
            elif operation_type == 'UPDATE':
                # UPDATE'i geri al = eski değerlerle UPDATE
                if op_dict['old_values']:
                    old_values = json.loads(op_dict['old_values'])
                    set_clause = ', '.join([f"{k} = ?" for k in old_values.keys()])
                    
                    cursor.execute(f"""
                        UPDATE {table_name} 
                        SET {set_clause} 
                        WHERE id = ?
                    """, list(old_values.values()) + [record_id])
            
            # Operation'u can_undo = FALSE yap
            cursor.execute("""
                UPDATE operations 
                SET can_undo = FALSE 
                WHERE id = ?
            """, (operation_id,))
            
            self.connection.commit()
            cursor.close()
            
            self.logger.info(f"İşlem geri alındı: {operation_type} on {table_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"İşlem geri alma hatası: {e}")
            self.connection.rollback()
            cursor.close()
            return False
    
    def clear_old_operations(self, older_than_days: int = 7):
        """Eski işlemleri temizle"""
        with self.transaction() as cursor:
            cutoff_date = (datetime.now() - timedelta(days=older_than_days)).isoformat()
            cursor.execute("""
                DELETE FROM operations 
                WHERE created_at < ?
            """, (cutoff_date,))
            return cursor.rowcount
    
    # === DOCUMENT & ARTICLE OPERATIONS ===
    
    def add_document(self, title: str, content: str, file_path: str,
                    document_type: str = "KANUN", law_number: str = None,
                    publication_date: str = None, file_hash: str = None) -> int:
        """Belge ekle"""
        with self.transaction() as cursor:
            cursor.execute("""
                INSERT INTO documents 
                (title, content, file_path, document_type, law_number, 
                 publication_date, file_hash, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?)
            """, (title, content, file_path, document_type, law_number,
                  publication_date, file_hash, datetime.now().isoformat()))
            
            document_id = cursor.lastrowid
            
            # Log operation for undo
            self.log_operation(
                'INSERT', 'documents', document_id,
                description=f"Belge eklendi: {title}"
            )
            
            return document_id
    
    def add_article(self, document_id: int, article_number: str, title: str,
                   content: str, content_clean: str, seq_index: int = 0,
                   article_type: str = "MADDE") -> int:
        """Madde ekle"""
        with self.transaction() as cursor:
            cursor.execute("""
                INSERT INTO articles 
                (document_id, article_number, title, content, content_clean,
                 seq_index, article_type, is_repealed, is_amended, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, FALSE, FALSE, ?)
            """, (document_id, article_number, title, content, content_clean,
                  seq_index, article_type, datetime.now().isoformat()))
            
            article_id = cursor.lastrowid
            
            # FTS'e ekle
            cursor.execute("""
                INSERT INTO articles_fts 
                (rowid, title, content, content_clean, article_number)
                VALUES (?, ?, ?, ?, ?)
            """, (article_id, title, content, content_clean, article_number))
            
            # Log operation for undo
            self.log_operation(
                'INSERT', 'articles', article_id,
                description=f"Madde eklendi: {article_number}"
            )
            
            return article_id
    
    def add_articles_batch(self, articles_data: List[Dict]) -> List[int]:
        """Toplu madde ekleme (performans için)"""
        article_ids = []
        
        with self.transaction() as cursor:
            for article in articles_data:
                cursor.execute("""
                    INSERT INTO articles 
                    (document_id, article_number, title, content, content_clean,
                     seq_index, article_type, is_repealed, is_amended, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, FALSE, FALSE, ?)
                """, (
                    article['document_id'],
                    article['article_number'], 
                    article['title'],
                    article['content'],
                    article['content_clean'],
                    article.get('seq_index', 0),
                    article.get('article_type', 'MADDE'),
                    datetime.now().isoformat()
                ))
                
                article_id = cursor.lastrowid
                article_ids.append(article_id)
                
                # FTS'e ekle
                cursor.execute("""
                    INSERT INTO articles_fts 
                    (rowid, title, content, content_clean, article_number)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    article_id,
                    article['title'], 
                    article['content'],
                    article['content_clean'],
                    article['article_number']
                ))
        
        self.logger.info(f"Toplu ekleme tamamlandı: {len(article_ids)} madde")
        return article_ids
    
    def delete_document(self, document_id: int, delete_physical_file: bool = False) -> bool:
        """
        Belgeyi sistemden sil
        
        Args:
            document_id: Silinecek belge ID'si
            delete_physical_file: Fiziksel dosyayı da sil
        
        Returns:
            Silme işlemi başarılı mı
        """
        try:
            # Önce belge bilgilerini al (undo için)
            document_info = self.get_document(document_id)
            if not document_info:
                self.logger.error(f"Belge bulunamadı: {document_id}")
                return False
            
            # Fiziksel dosyayı sil (eğer istenmişse)
            if delete_physical_file and document_info.get('file_path'):
                import os
                file_path = document_info['file_path']
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        self.logger.info(f"Fiziksel dosya silindi: {file_path}")
                    except Exception as e:
                        self.logger.warning(f"Fiziksel dosya silinemedi: {e}")
            
            with self.transaction() as cursor:
                # 1. Önce bağımlı kayıtları sil
                
                # Kullanıcı notlarını sil
                cursor.execute("DELETE FROM user_notes WHERE document_id = ?", (document_id,))
                notes_deleted = cursor.rowcount
                
                # Makale ilişkilerini sil
                cursor.execute("""
                    DELETE FROM article_relations 
                    WHERE source_id IN (
                        SELECT id FROM articles WHERE document_id = ?
                    ) OR target_id IN (
                        SELECT id FROM articles WHERE document_id = ?
                    )
                """, (document_id, document_id))
                relations_deleted = cursor.rowcount
                
                # Makale notlarını sil
                cursor.execute("""
                    DELETE FROM user_notes 
                    WHERE article_id IN (
                        SELECT id FROM articles WHERE document_id = ?
                    )
                """, (document_id,))
                article_notes_deleted = cursor.rowcount
                
                # Makaleleri sil
                cursor.execute("DELETE FROM articles WHERE document_id = ?", (document_id,))
                articles_deleted = cursor.rowcount
                
                # Son olarak belgeyi sil
                cursor.execute("DELETE FROM documents WHERE id = ?", (document_id,))
                document_deleted = cursor.rowcount > 0
                
                if document_deleted:
                    # İşlemi logla (undo için)
                    self.log_operation(
                        operation_type='DELETE',
                        table_name='documents',
                        record_id=document_id,
                        old_values=document_info,
                        description=f"Belge silindi: {document_info.get('title', 'Başlıksız')}"
                    )
                    
                    self.logger.info(f"Belge başarıyla silindi - ID: {document_id}")
                    self.logger.info(f"Silinen: {articles_deleted} madde, {notes_deleted} not, {relations_deleted} ilişki")
                    
                    return True
                else:
                    self.logger.error(f"Belge silinemedi: {document_id}")
                    return False
        
        except Exception as e:
            self.logger.error(f"Belge silme hatası: {e}")
            return False
    
    def delete_multiple_documents(self, document_ids: List[int], delete_physical_files: bool = False) -> Dict[str, Any]:
        """
        Birden fazla belgeyi sil
        
        Args:
            document_ids: Silinecek belge ID'leri
            delete_physical_files: Fiziksel dosyaları da sil
        
        Returns:
            Silme işlemi istatistikleri
        """
        result = {
            'success_count': 0,
            'error_count': 0,
            'errors': [],
            'deleted_documents': []
        }
        
        for doc_id in document_ids:
            try:
                document_info = self.get_document(doc_id)
                if document_info:
                    if self.delete_document(doc_id, delete_physical_files):
                        result['success_count'] += 1
                        result['deleted_documents'].append({
                            'id': doc_id,
                            'title': document_info.get('title', 'Başlıksız')
                        })
                    else:
                        result['error_count'] += 1
                        result['errors'].append(f"Belge silinemedi: {doc_id}")
                else:
                    result['error_count'] += 1
                    result['errors'].append(f"Belge bulunamadı: {doc_id}")
                    
            except Exception as e:
                result['error_count'] += 1
                result['errors'].append(f"Belge {doc_id} silme hatası: {e}")
        
        return result
    
    def get_document(self, document_id: int) -> Optional[Dict[str, Any]]:
        """Belge bilgilerini getir"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM documents WHERE id = ?", (document_id,))
        
        row = cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]
            result = dict(zip(columns, row))
            cursor.close()
            return result
        
        cursor.close()
        return None
    
    def update_article(self, article_id: int, **kwargs) -> bool:
        """Madde güncelle"""
        if not kwargs:
            return False
            
        # Mevcut değerleri al (undo için)
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
        old_record = cursor.fetchone()
        
        if not old_record:
            cursor.close()
            return False
            
        columns = [desc[0] for desc in cursor.description]
        old_values = dict(zip(columns, old_record))
        cursor.close()
        
        # Güncellenecek alanları hazırla
        set_clauses = []
        values = []
        
        for key, value in kwargs.items():
            if key in ['title', 'content', 'content_clean', 'article_number', 
                      'article_type', 'is_repealed', 'is_amended']:
                set_clauses.append(f"{key} = ?")
                values.append(value)
        
        if not set_clauses:
            return False
        
        # Updated_at ekle
        set_clauses.append("updated_at = ?")
        values.append(datetime.now().isoformat())
        values.append(article_id)
        
        with self.transaction() as cursor:
            cursor.execute(f"""
                UPDATE articles 
                SET {', '.join(set_clauses)}
                WHERE id = ?
            """, values)
            
            # FTS güncelle
            if any(k in kwargs for k in ['title', 'content', 'content_clean', 'article_number']):
                cursor.execute("""
                    UPDATE articles_fts 
                    SET title = ?, content = ?, content_clean = ?, article_number = ?
                    WHERE rowid = ?
                """, (
                    kwargs.get('title', old_values['title']),
                    kwargs.get('content', old_values['content']),
                    kwargs.get('content_clean', old_values['content_clean']),
                    kwargs.get('article_number', old_values['article_number']),
                    article_id
                ))
            
            # Log operation for undo
            self.log_operation(
                'UPDATE', 'articles', article_id,
                old_values=old_values,
                new_values=kwargs,
                description=f"Madde güncellendi: {article_id}"
            )
            
            return cursor.rowcount > 0
    
    def delete_article(self, article_id: int) -> bool:
        """Madde sil"""
        # Mevcut değerleri al (undo için)
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
        old_record = cursor.fetchone()
        
        if not old_record:
            cursor.close()
            return False
            
        columns = [desc[0] for desc in cursor.description]
        old_values = dict(zip(columns, old_record))
        cursor.close()
        
        with self.transaction() as cursor:
            # FTS'den sil
            cursor.execute("DELETE FROM articles_fts WHERE rowid = ?", (article_id,))
            
            # Ana tablodan sil
            cursor.execute("DELETE FROM articles WHERE id = ?", (article_id,))
            
            # Log operation for undo
            self.log_operation(
                'DELETE', 'articles', article_id,
                old_values=old_values,
                description=f"Madde silindi: {article_id}"
            )
    
    def __del__(self):
        """Nesne yok edilirken bağlantıyı kapat - Deprecated, use explicit close()"""
        # Note: __del__ is unreliable, always call close() explicitly
        pass
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures proper cleanup"""
        self.close()
