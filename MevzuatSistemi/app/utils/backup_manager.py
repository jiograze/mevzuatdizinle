"""
Otomatik Yedekleme Sistemi
Veritabanı ve config dosyalarının düzenli yedeğini alır
"""

import os
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import zipfile
import json

class BackupManager:
    """Otomatik yedekleme sistemi"""
    
    def __init__(self, config_manager, db_manager):
        self.config = config_manager
        self.db = db_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Yedekleme ayarları
        self.backup_enabled = self.config.get('backup.enabled', True)
        self.backup_folder = Path(self.config.get('backup.folder', 'backups'))
        self.backup_interval_days = self.config.get('backup.interval_days', 7)
        self.keep_backups = self.config.get('backup.keep_backups', 10)
        self.auto_backup = self.config.get('backup.auto_backup', True)
        
        self._ensure_backup_folder()
    
    def _ensure_backup_folder(self):
        """Yedekleme klasörünü oluştur"""
        try:
            self.backup_folder.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Backup klasörü hazır: {self.backup_folder}")
        except Exception as e:
            self.logger.error(f"Backup klasörü oluşturulamadı: {e}")
    
    def create_backup(self, backup_name: Optional[str] = None) -> Optional[Path]:
        """
        Tam sistem yedeği oluştur
        
        Args:
            backup_name: Özel yedek adı (otomatik oluşturulur)
            
        Returns:
            Oluşturulan yedek dosyasının yolu
        """
        if not self.backup_enabled:
            self.logger.info("Yedekleme devre dışı")
            return None
        
        try:
            # Yedek adını belirle
            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"mevzuat_backup_{timestamp}"
            
            backup_file = self.backup_folder / f"{backup_name}.zip"
            
            self.logger.info(f"Yedekleme başlatılıyor: {backup_file}")
            
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 1. Veritabanı dosyalarını yedekle
                self._backup_database(zipf)
                
                # 2. Konfigürasyon dosyalarını yedekle
                self._backup_configs(zipf)
                
                # 3. Index dosyalarını yedekle
                self._backup_indexes(zipf)
                
                # 4. Log dosyalarını yedekle (son 30 gün)
                self._backup_logs(zipf)
                
                # 5. Metadata oluştur
                self._create_backup_metadata(zipf, backup_name)
            
            self.logger.info(f"Yedekleme tamamlandı: {backup_file}")
            
            # Eski yedekleri temizle
            self._cleanup_old_backups()
            
            return backup_file
            
        except Exception as e:
            self.logger.error(f"Yedekleme hatası: {e}")
            return None
    
    def _backup_database(self, zipf: zipfile.ZipFile):
        """Veritabanı dosyalarını yedekle"""
        db_path = Path(self.config.get('database.db_file', 'db/mevzuat.db'))
        if db_path.exists():
            zipf.write(db_path, f"database/{db_path.name}")
            self.logger.debug(f"Database yedeklendi: {db_path}")
    
    def _backup_configs(self, zipf: zipfile.ZipFile):
        """Konfigürasyon dosyalarını yedekle"""
        config_folder = Path('config')
        if config_folder.exists():
            for config_file in config_folder.glob('*.yaml'):
                if config_file.exists():
                    zipf.write(config_file, f"config/{config_file.name}")
                    self.logger.debug(f"Config yedeklendi: {config_file}")
    
    def _backup_indexes(self, zipf: zipfile.ZipFile):
        """Index dosyalarını yedekle"""
        index_folder = Path(self.config.get('search.index_folder', 'index'))
        if index_folder.exists():
            for index_file in index_folder.rglob('*'):
                if index_file.is_file():
                    rel_path = index_file.relative_to(index_folder)
                    zipf.write(index_file, f"index/{rel_path}")
            self.logger.debug(f"Index dosyaları yedeklendi: {index_folder}")
    
    def _backup_logs(self, zipf: zipfile.ZipFile):
        """Log dosyalarını yedekle (son 30 gün)"""
        logs_folder = Path('logs')
        if logs_folder.exists():
            cutoff_date = datetime.now() - timedelta(days=30)
            
            for log_file in logs_folder.glob('*.log'):
                if log_file.exists():
                    # Dosya tarihi kontrol et
                    file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if file_time > cutoff_date:
                        zipf.write(log_file, f"logs/{log_file.name}")
                        self.logger.debug(f"Log yedeklendi: {log_file}")
    
    def _create_backup_metadata(self, zipf: zipfile.ZipFile, backup_name: str):
        """Yedekleme metadata'sı oluştur"""
        metadata = {
            'backup_name': backup_name,
            'created_at': datetime.now().isoformat(),
            'system_info': {
                'python_version': self._get_python_version(),
                'app_version': self.config.get('app.version', '1.0.0'),
                'db_version': self._get_db_version()
            },
            'files_backed_up': [],
            'backup_size': 0
        }
        
        metadata_json = json.dumps(metadata, indent=2, ensure_ascii=False)
        zipf.writestr('metadata.json', metadata_json.encode('utf-8'))
        self.logger.debug("Backup metadata oluşturuldu")
    
    def _get_python_version(self) -> str:
        """Python versiyon bilgisi"""
        import sys
        return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    def _get_db_version(self) -> str:
        """Veritabanı şema versionu"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = 'db_version'")
            result = cursor.fetchone()
            return result[0] if result else '1.0.0'
        except:
            return '1.0.0'
    
    def _cleanup_old_backups(self):
        """Eski yedekleri temizle"""
        try:
            backup_files = sorted(
                self.backup_folder.glob('mevzuat_backup_*.zip'),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            # Fazla yedekleri sil
            for old_backup in backup_files[self.keep_backups:]:
                old_backup.unlink()
                self.logger.info(f"Eski yedek silindi: {old_backup}")
                
        except Exception as e:
            self.logger.error(f"Eski yedek temizleme hatası: {e}")
    
    def restore_backup(self, backup_file: Path) -> bool:
        """
        Yedekten sistem geri yükle
        
        Args:
            backup_file: Geri yüklenecek yedek dosyası
            
        Returns:
            Başarı durumu
        """
        if not backup_file.exists():
            self.logger.error(f"Yedek dosyası bulunamadı: {backup_file}")
            return False
        
        try:
            self.logger.info(f"Yedekten geri yükleme başlatılıyor: {backup_file}")
            
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                # 1. Metadata kontrol et
                if not self._validate_backup_metadata(zipf):
                    return False
                
                # 2. Mevcut dosyaları yedekle (güvenlik)
                self._backup_current_before_restore()
                
                # 3. Dosyaları geri yükle
                self._restore_files(zipf)
                
            self.logger.info("Geri yükleme tamamlandı")
            return True
            
        except Exception as e:
            self.logger.error(f"Geri yükleme hatası: {e}")
            return False
    
    def _validate_backup_metadata(self, zipf: zipfile.ZipFile) -> bool:
        """Yedek metadata'sını doğrula"""
        try:
            metadata_content = zipf.read('metadata.json')
            metadata = json.loads(metadata_content.decode('utf-8'))
            
            # Temel doğrulamalar
            required_fields = ['backup_name', 'created_at', 'system_info']
            for field in required_fields:
                if field not in metadata:
                    self.logger.error(f"Metadata'da eksik alan: {field}")
                    return False
            
            self.logger.info(f"Backup metadata doğrulandı: {metadata['backup_name']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Metadata doğrulama hatası: {e}")
            return False
    
    def _backup_current_before_restore(self):
        """Geri yükleme öncesi mevcut durumu yedekle"""
        try:
            self.create_backup("pre_restore_backup")
            self.logger.info("Geri yükleme öncesi mevcut durum yedeklendi")
        except Exception as e:
            self.logger.warning(f"Geri yükleme öncesi yedek oluşturulamadı: {e}")
    
    def _restore_files(self, zipf: zipfile.ZipFile):
        """Dosyaları geri yükle"""
        # Veritabanı dosyasını kapat
        self.db.close()
        
        # Tüm dosyaları çıkart
        zipf.extractall(Path('.'))
        
        # Veritabanını yeniden aç
        self.db.initialize()
        
        self.logger.info("Tüm dosyalar geri yüklendi")
    
    def list_backups(self) -> List[Dict]:
        """Mevcut yedekleri listele"""
        backups = []
        
        try:
            for backup_file in sorted(
                self.backup_folder.glob('mevzuat_backup_*.zip'),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            ):
                stat = backup_file.stat()
                backups.append({
                    'name': backup_file.stem,
                    'file': backup_file.name,
                    'path': backup_file,
                    'size': stat.st_size,
                    'size_mb': round(stat.st_size / 1024 / 1024, 2),
                    'created': datetime.fromtimestamp(stat.st_mtime),
                    'created_str': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
                })
        
        except Exception as e:
            self.logger.error(f"Yedek listesi oluşturulamadı: {e}")
        
        return backups
    
    def auto_backup_check(self):
        """Otomatik yedekleme kontrolü"""
        if not self.auto_backup or not self.backup_enabled:
            return
        
        try:
            # Son yedekleme tarihi
            backups = self.list_backups()
            if not backups:
                self.logger.info("Hiç yedek yok, otomatik yedekleme başlatılıyor")
                self.create_backup()
                return
            
            last_backup = backups[0]['created']
            days_since_backup = (datetime.now() - last_backup).days
            
            if days_since_backup >= self.backup_interval_days:
                self.logger.info(f"Son yedeklemeden {days_since_backup} gün geçti, otomatik yedekleme başlatılıyor")
                self.create_backup()
            else:
                self.logger.debug(f"Otomatik yedekleme gerekmiyor (son yedek: {days_since_backup} gün önce)")
        
        except Exception as e:
            self.logger.error(f"Otomatik yedekleme kontrolü hatası: {e}")
    
    def get_backup_status(self) -> Dict:
        """Yedekleme sistemi durumu"""
        backups = self.list_backups()
        
        status = {
            'enabled': self.backup_enabled,
            'auto_backup': self.auto_backup,
            'backup_folder': str(self.backup_folder),
            'total_backups': len(backups),
            'interval_days': self.backup_interval_days,
            'keep_backups': self.keep_backups,
            'last_backup': None,
            'next_backup': None,
            'total_size_mb': 0
        }
        
        if backups:
            status['last_backup'] = backups[0]['created_str']
            status['total_size_mb'] = sum(b['size_mb'] for b in backups)
            
            if self.auto_backup:
                next_backup_date = backups[0]['created'] + timedelta(days=self.backup_interval_days)
                status['next_backup'] = next_backup_date.strftime('%Y-%m-%d %H:%M')
        
        return status
