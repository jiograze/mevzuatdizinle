#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test runner script - Farklı test kategorilerini çalıştırmak için
"""

import sys
import subprocess
import argparse
from pathlib import Path

def run_tests(test_type="all", verbose=True, coverage=False, parallel=False):
    """
    Testleri çalıştır
    
    Args:
        test_type: "unit", "integration", "ui", "all"
        verbose: Detaylı çıktı
        coverage: Coverage raporu oluştur
        parallel: Paralel çalıştırma
    """
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Test path
    if test_type == "unit":
        cmd.extend(["tests/unit/"])
    elif test_type == "integration":
        cmd.extend(["tests/integration/", "-m", "integration"])
    elif test_type == "ui":
        cmd.extend(["tests/ui/", "-m", "ui"])
    elif test_type == "all":
        cmd.extend(["tests/"])
    else:
        cmd.extend([f"tests/{test_type}/"])
    
    # Verbosity
    if verbose:
        cmd.append("-v")
    
    # Coverage
    if coverage:
        cmd.extend([
            "--cov=app",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-report=xml"
        ])
    
    # Parallel execution  
    if parallel:
        try:
            import pytest_xdist
            cmd.extend(["-n", "auto"])
        except ImportError:
            print("⚠️  pytest-xdist not installed, running sequentially")
    
    # Additional options
    cmd.extend([
        "--tb=short",
        "--color=yes", 
        "--durations=10"
    ])
    
    print(f"🧪 Running {test_type} tests...")
    print(f"📝 Command: {' '.join(cmd)}")
    print("-" * 60)
    
    # Run tests
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode == 0
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def install_test_dependencies():
    """Test bağımlılıklarını yükle"""
    print("📦 Installing test dependencies...")
    
    dependencies = [
        "pytest>=7.4.3",
        "pytest-qt>=4.2.0", 
        "pytest-cov>=4.1.0",
        "pytest-xdist>=3.3.1",
        "pytest-mock>=3.11.1",
        "coverage>=7.3.0"
    ]
    
    for dep in dependencies:
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", dep
            ], check=True, capture_output=True)
            print(f"✅ {dep}")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {dep}")
            return False
    
    return True

def generate_test_report():
    """Test raporu oluştur"""
    print("📊 Generating comprehensive test report...")
    
    # Coverage report
    coverage_cmd = [
        "python", "-m", "pytest",
        "tests/",
        "--cov=app",
        "--cov-report=html:htmlcov",
        "--cov-report=xml:coverage.xml", 
        "--cov-report=term-missing",
        "--junit-xml=test-results.xml"
    ]
    
    try:
        subprocess.run(coverage_cmd, check=True)
        print("✅ Test report generated:")
        print("   📄 HTML Coverage: htmlcov/index.html")
        print("   📄 XML Coverage: coverage.xml")  
        print("   📄 JUnit XML: test-results.xml")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to generate test report")
        return False

def main():
    parser = argparse.ArgumentParser(description="Mevzuat Sistemi Test Runner")
    
    parser.add_argument(
        "test_type", 
        choices=["unit", "integration", "ui", "all", "install", "report"],
        default="all",
        nargs="?",
        help="Test type to run"
    )
    
    parser.add_argument(
        "--no-verbose", 
        action="store_true",
        help="Disable verbose output"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true", 
        help="Generate coverage report"
    )
    
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run tests in parallel"
    )
    
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Skip slow tests"
    )
    
    args = parser.parse_args()
    
    # Special commands
    if args.test_type == "install":
        success = install_test_dependencies()
        sys.exit(0 if success else 1)
    
    if args.test_type == "report":
        success = generate_test_report()
        sys.exit(0 if success else 1)
    
    # Run tests
    success = run_tests(
        test_type=args.test_type,
        verbose=not args.no_verbose,
        coverage=args.coverage,
        parallel=args.parallel
    )
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
