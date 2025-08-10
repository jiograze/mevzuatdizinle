#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Kod Kalitesi İyileştirme Uygulamaları - Mevzuat Sistemi

Bu dosya, kod kalitesi değerlendirme raporuna dayanarak yapılan iyileştirmelerin
uygulanması için rehberlik eden ana orchestrator'dür.
"""

import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import time

# Güvenlik ve validation imports
from app.security import (
    FileSecurityValidator,
    InputValidator, 
    SecureErrorHandler,
    ConfigSecurityValidator
)

# Base classes import
from app.core.base import (
    BaseComponent,
    BaseUIWidget,
    ComponentManager
)

# Existing core components
from app.core.database_manager import DatabaseManager
from app.core.search_engine import SearchEngine
from app.core.document_processor import DocumentProcessor
from app.core.app_manager import MevzuatApp
from app.utils.config_manager import ConfigManager
from app.utils.logger import setup_logger


class EnhancedSecurityManager(BaseComponent):
    """Güvenlik yöneticisi - Tüm güvenlik kontrollerini merkezi olarak yönetir"""
    
    def __init__(self, config: ConfigManager):
        super().__init__(config, "SecurityManager")
        
        self.file_validator = FileSecurityValidator()
        self.input_validator = InputValidator()
        self.config_validator = ConfigSecurityValidator()
        self.error_handler = SecureErrorHandler()
        
    def _do_initialize(self) -> bool:
        """Güvenlik bileşenlerini başlat"""
        try:
            # Config güvenlik kontrolü
            config_data = self.config._data if hasattr(self.config, '_data') else {}
            validation_result = self.config_validator.validate_config(config_data)
            
            if validation_result.warnings:
                for warning in validation_result.warnings:
                    self.logger.warning(f"Config security warning: {warning}")
            
            self.logger.info("Security manager initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Security manager initialization failed: {e}")
            return False
    
    def validate_file_upload(self, file_path: str) -> Dict[str, Any]:
        """Dosya yükleme güvenlik kontrolü"""
        result = self.file_validator.validate_file_path(file_path)
        
        return {
            'is_safe': result.is_valid,
            'error_message': result.error_message,
            'warnings': result.warnings
        }
    
    def validate_search_input(self, query: str) -> Dict[str, Any]:
        """Arama girdi güvenlik kontrolü"""
        result = self.input_validator.validate_search_query(query)
        
        return {
            'is_valid': result.is_valid,
            'error_message': result.error_message,
            'warnings': result.warnings,
            'sanitized_query': self.input_validator.sanitize_text(query) if query else ""
        }
    
    def handle_error_safely(self, error: Exception, context: str = "", 
                          user_mode: bool = True) -> str:
        """Güvenli hata işleme"""
        return self.error_handler.handle_error(error, context, user_mode)


class QualityEnhancedAppManager(MevzuatApp):
    """Geliştirilmiş uygulama yöneticisi - Kod kalitesi iyileştirmeleri ile"""
    
    def __init__(self, config_path: Optional[str] = None):
        # Önce güvenlik kontrolü
        if config_path and not Path(config_path).exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        # MevzuatApp parametresiz çağrı
        super().__init__()
        
        # Config path varsa yeniden yükle
        if config_path:
            self.config = ConfigManager(config_path)
        
        # Enhanced components
        self.security_manager: Optional[EnhancedSecurityManager] = None
        self.component_manager: Optional[ComponentManager] = None
        
        # Performance tracking
        self.performance_metrics = {
            'startup_time': 0,
            'total_operations': 0,
            'error_count': 0,
            'last_health_check': None
        }
    
    def initialize_enhanced_components(self) -> bool:
        """Geliştirilmiş bileşenleri başlat"""
        start_time = time.time()
        
        try:
            # Component Manager oluştur
            self.component_manager = ComponentManager(self.config)
            
            # Security Manager oluştur ve kaydet
            self.security_manager = EnhancedSecurityManager(self.config)
            self.component_manager.register_component(
                "security_manager", 
                self.security_manager
            )
            
            # Existing components'ları enhance et
            self._enhance_existing_components()
            
            # Tüm bileşenleri başlat
            success = self.component_manager.initialize_all()
            
            self.performance_metrics['startup_time'] = time.time() - start_time
            self.logger.info(f"Enhanced initialization completed in {self.performance_metrics['startup_time']:.2f}s")
            
            return success
            
        except Exception as e:
            error_msg = f"Enhanced initialization failed: {e}"
            self.logger.error(error_msg)
            return False
    
    def _enhance_existing_components(self):
        """Mevcut bileşenleri geliştir"""
        
        # Database Manager enhancement
        if hasattr(self, 'database_manager') and self.database_manager:
            # Güvenlik validasyonu ekle
            original_add_document = self.database_manager.add_document
            
            def enhanced_add_document(document_data: Dict[str, Any]) -> Optional[int]:
                # Güvenlik kontrolü
                if self.security_manager:
                    validation = self.security_manager.input_validator.validate_document_metadata(document_data)
                    if not validation.is_valid:
                        self.logger.error(f"Document validation failed: {validation.error_message}")
                        return None
                
                return original_add_document(document_data)
            
            self.database_manager.add_document = enhanced_add_document
        
        # Search Engine enhancement
        if hasattr(self, 'search_engine') and self.search_engine:
            original_search = self.search_engine.search
            
            def enhanced_search(query: str, **kwargs):
                # Güvenlik kontrolü
                if self.security_manager:
                    validation = self.security_manager.validate_search_input(query)
                    if not validation['is_valid']:
                        self.logger.error(f"Search validation failed: {validation['error_message']}")
                        return []
                    
                    # Sanitized query kullan
                    query = validation['sanitized_query']
                
                return original_search(query, **kwargs)
            
            self.search_engine.search = enhanced_search
        
        # Document Processor enhancement
        if hasattr(self, 'document_processor') and self.document_processor:
            original_process_file = self.document_processor.process_file
            
            def enhanced_process_file(file_path: str) -> bool:
                # Dosya güvenlik kontrolü
                if self.security_manager:
                    validation = self.security_manager.validate_file_upload(file_path)
                    if not validation['is_safe']:
                        self.logger.error(f"File security validation failed: {validation['error_message']}")
                        return False
                
                return original_process_file(file_path)
            
            self.document_processor.process_file = enhanced_process_file
    
    def health_check(self) -> Dict[str, Any]:
        """Sistem sağlık kontrolü"""
        health_status = {
            'timestamp': time.time(),
            'overall_status': 'healthy',
            'components': {},
            'performance': self.performance_metrics.copy(),
            'issues': []
        }
        
        try:
            # Component status kontrolü
            if self.component_manager:
                component_stats = self.component_manager.get_component_stats()
                for name, stats in component_stats.items():
                    component = self.component_manager.get_component(name)
                    health_status['components'][name] = {
                        'status': 'healthy' if component and component.is_ready() else 'unhealthy',
                        'stats': stats
                    }
                    
                    # Hata oranı kontrolü
                    total_ops = stats.get('total_operations', 0)
                    failed_ops = stats.get('failed_operations', 0)
                    if total_ops > 0 and failed_ops / total_ops > 0.1:  # %10'dan fazla hata
                        health_status['issues'].append(f"{name} high error rate: {failed_ops}/{total_ops}")
            
            # Database bağlantısı kontrolü
            if hasattr(self, 'database_manager') and self.database_manager:
                try:
                    # Basit veritabanı sorgusu
                    cursor = self.database_manager.connection.cursor()
                    cursor.execute("SELECT 1")
                    cursor.close()
                    health_status['components']['database'] = {'status': 'healthy'}
                except Exception as e:
                    health_status['components']['database'] = {
                        'status': 'unhealthy',
                        'error': str(e)
                    }
                    health_status['issues'].append(f"Database connection error: {e}")
            
            # Overall status belirleme
            unhealthy_components = [
                name for name, info in health_status['components'].items()
                if info.get('status') == 'unhealthy'
            ]
            
            if unhealthy_components:
                health_status['overall_status'] = 'degraded'
                if len(unhealthy_components) > len(health_status['components']) / 2:
                    health_status['overall_status'] = 'unhealthy'
            
            self.performance_metrics['last_health_check'] = health_status['timestamp']
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            health_status['overall_status'] = 'error'
            health_status['issues'].append(f"Health check error: {e}")
        
        return health_status
    
    def generate_quality_report(self) -> Dict[str, Any]:
        """Kod kalitesi raporu oluştur"""
        report = {
            'timestamp': time.time(),
            'version': '1.0.2-enhanced',
            'quality_metrics': {},
            'security_status': {},
            'performance_metrics': self.performance_metrics.copy(),
            'recommendations': []
        }
        
        try:
            # Security status
            if self.security_manager:
                report['security_status'] = {
                    'file_validation_active': True,
                    'input_validation_active': True,
                    'error_handling_enhanced': True
                }
            
            # Component quality metrics
            if self.component_manager:
                component_stats = self.component_manager.get_component_stats()
                for name, stats in component_stats.items():
                    success_rate = 0
                    total_ops = stats.get('total_operations', 0)
                    if total_ops > 0:
                        success_ops = stats.get('successful_operations', 0)
                        success_rate = success_ops / total_ops
                    
                    report['quality_metrics'][name] = {
                        'success_rate': success_rate,
                        'total_operations': total_ops,
                        'last_operation': stats.get('last_operation_time')
                    }
                    
                    # Öneriler
                    if success_rate < 0.9 and total_ops > 10:
                        report['recommendations'].append(
                            f"{name} component has low success rate ({success_rate:.2%}), investigate issues"
                        )
            
            # Genel öneriler
            if self.performance_metrics['error_count'] > 50:
                report['recommendations'].append("High error count detected, review error handling")
            
            if self.performance_metrics['startup_time'] > 10:
                report['recommendations'].append("Slow startup time, optimize initialization process")
            
        except Exception as e:
            self.logger.error(f"Quality report generation failed: {e}")
            report['error'] = str(e)
        
        return report
    
    def run(self) -> int:
        """Enhanced uygulamayı başlat"""
        try:
            # Enhanced bileşenleri başlat
            if not self.initialize_enhanced_components():
                self.logger.error("❌ Enhanced initialization failed")
                return 1
            
            self.logger.info("✅ Enhanced initialization completed")
            
            # Sağlık kontrolü
            health = self.health_check()
            self.logger.info(f"🏥 System health: {health['overall_status']}")
            
            if health['issues']:
                for issue in health['issues']:
                    self.logger.warning(f"⚠️  {issue}")
            
            # Kalite raporu oluştur
            quality_report = self.generate_quality_report()
            self.logger.info(f"📊 Quality Report Generated - Success rates: {len(quality_report['quality_metrics'])} components")
            
            if quality_report['recommendations']:
                self.logger.info("💡 Quality Recommendations:")
                for rec in quality_report['recommendations']:
                    self.logger.info(f"   - {rec}")
            
            # Ana uygulama başlat (PyQt5 app)
            from PyQt5.QtWidgets import QApplication
            
            qt_app = QApplication(sys.argv)
            self.qt_app = qt_app
            
            # Ana pencereyi enhanced manager ile başlat
            from app.ui.main_window import MainWindow
            
            main_window = MainWindow(
                config=self.config,
                db=self.db,
                search_engine=self.search_engine,
                document_processor=self.document_processor,
                file_watcher=self.file_watcher
            )
            
            self.main_window = main_window
            
            # Security manager'ı main window'a bağla
            if self.security_manager:
                # Security event handlers
                def on_file_upload_request(file_path: str):
                    validation = self.security_manager.validate_file_upload(file_path)
                    if not validation['is_safe']:
                        main_window.show_error_message("Güvenlik Uyarısı", validation['error_message'])
                        return False
                    return True
                
                # Main window'a security callback ekle (eğer destekliyorsa)
                if hasattr(main_window, 'set_file_upload_validator'):
                    main_window.set_file_upload_validator(on_file_upload_request)
            
            main_window.show()
            
            self.logger.info("🖥️  GUI Application started")
            
            # Event loop
            return qt_app.exec_()
            
        except Exception as e:
            self.logger.error(f"❌ Application startup failed: {e}")
            return 1
        
        finally:
            # Cleanup
            try:
                if self.component_manager:
                    self.component_manager.cleanup_all()
                self.logger.info("🧹 Cleanup completed")
            except Exception as e:
                self.logger.error(f"Cleanup error: {e}")


def main():
    """Ana enhanced uygulama başlatma"""
    
    # Logger setup
    logger = setup_logger("ENHANCED_APP")
    logger.info("🚀 Starting Mevzuat Sistemi with Quality Enhancements")
    
    try:
        # Config dosyası path
        config_path = Path(__file__).parent / "config" / "config.yaml"
        
        # Enhanced App Manager oluştur
        app_manager = QualityEnhancedAppManager(str(config_path))
        
        # Enhanced uygulamayı başlat
        return app_manager.run()
        
    except Exception as e:
        logger.error(f"❌ Application startup failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
