"""
Test Runner - Tüm testleri çalıştıran ana script
"""

import unittest
import sys
import logging
from pathlib import Path

# Test modüllerini import et
from test_advanced_integration import (
    BaseTestCase, IntegrationTestCase, UIAutomationTestCase,
    PerformanceTestCase, EndToEndTestCase, create_test_suite
)

def setup_logging():
    """Test logging setup"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('test_results.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Ana test çalıştırıcı"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Mevzuat System Test Suite")
    logger.info("=" * 50)
    
    # Test suite oluştur
    suite = create_test_suite()
    
    # Test runner konfigüre et
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        buffer=False,
        failfast=False
    )
    
    # Testleri çalıştır
    result = runner.run(suite)
    
    # Sonuçları raporla
    logger.info("=" * 50)
    logger.info("Test Results:")
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        logger.error("FAILURES:")
        for test, traceback in result.failures:
            logger.error(f"  {test}: {traceback}")
    
    if result.errors:
        logger.error("ERRORS:")
        for test, traceback in result.errors:
            logger.error(f"  {test}: {traceback}")
    
    # Exit code
    success = result.wasSuccessful()
    logger.info(f"Test Suite {'PASSED' if success else 'FAILED'}")
    
    return 0 if success else 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
