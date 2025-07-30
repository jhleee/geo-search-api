#!/usr/bin/env python3
"""
Run all tests for GeoTag API
"""

import subprocess
import sys

def run_tests():
    """Run all test suites"""
    print("🧪 Running GeoTag API Tests...")
    print("=" * 50)
    
    # Run pytest with coverage
    cmd = [sys.executable, "-m", "pytest", "tests/", "-v", "--cov=src", "--cov-report=term-missing"]
    
    try:
        result = subprocess.run(cmd, check=True)
        print("\n✅ All tests passed!")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Tests failed with exit code: {e.returncode}")
        return e.returncode

if __name__ == "__main__":
    sys.exit(run_tests())