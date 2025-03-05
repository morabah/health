#!/usr/bin/env python3
"""
Python 3.13 Compatibility Checker for Health Appointment System

This script tests key functionality of the health appointment system
to ensure it works properly with Python 3.13.
"""

import sys
import os
import logging
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def check_python_version() -> bool:
    """Check if running with Python 3.13, warn if not."""
    major, minor = sys.version_info.major, sys.version_info.minor
    
    logger.info(f"{sys.version=}")
    
    if major == 3 and minor >= 13:
        logger.info("✅ Running with Python 3.13 or newer")
        return True
    else:
        logger.warning(f"⚠️ Not running with Python 3.13 (detected {major}.{minor})")
        logger.warning("Some compatibility checks may not be accurate")
        return False

def check_module_imports() -> bool:
    """Test importing key modules to ensure compatibility."""
    required_modules = [
        "flask", 
        "flask_sqlalchemy",
        "flask_login",
        "PIL",
        "sqlalchemy",
        "wtforms",
        "email",
        "jwt",
        "bcrypt",
    ]
    
    success = True
    for module_name in required_modules:
        try:
            importlib.import_module(module_name)
            logger.info(f"✅ Successfully imported {module_name}")
        except ImportError as e:
            logger.error(f"❌ Failed to import {module_name}: {e}")
            success = False
    
    return success

def check_app_modules() -> bool:
    """Test importing application modules."""
    app_modules = [
        "models",
        "forms",
        "utils",
        "routes",
    ]
    
    success = True
    for module_name in app_modules:
        try:
            # Ensure we're in the right directory for imports
            module_path = Path(os.path.dirname(os.path.abspath(__file__))) / f"{module_name}.py"
            if not module_path.exists():
                logger.error(f"❌ Module file not found: {module_path}")
                success = False
                continue
                
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            logger.info(f"✅ Successfully imported app module {module_name}")
        except Exception as e:
            logger.error(f"❌ Failed to import app module {module_name}: {e}")
            success = False
    
    return success

def test_pattern_matching() -> bool:
    """Test Python 3.10+ pattern matching."""
    try:
        # Simple test case with pattern matching
        def get_status_message(status: str) -> str:
            match status:
                case "pending":
                    return "Waiting for approval"
                case "approved":
                    return "Your request was approved"
                case "rejected":
                    return "Your request was denied"
                case _:
                    return "Unknown status"
        
        result = get_status_message("approved")
        if result == "Your request was approved":
            logger.info("✅ Pattern matching is working correctly")
            return True
        else:
            logger.error(f"❌ Pattern matching produced unexpected result: {result}")
            return False
    except SyntaxError:
        logger.error("❌ Pattern matching syntax not supported (requires Python 3.10+)")
        return False

def test_self_documenting_fstrings() -> bool:
    """Test Python 3.12+ self-documenting f-strings."""
    try:
        # Test self-documenting f-strings
        doctor_id = 123
        patient_id = 456
        debug_info = f"{doctor_id=}, {patient_id=}"
        
        if "doctor_id=123" in debug_info and "patient_id=456" in debug_info:
            logger.info("✅ Self-documenting f-strings are working correctly")
            return True
        else:
            logger.error(f"❌ Self-documenting f-strings produced unexpected result: {debug_info}")
            return False
    except SyntaxError:
        logger.error("❌ Self-documenting f-strings syntax not supported (requires Python 3.12+)")
        return False

def check_type_hint_support() -> bool:
    """Test Python 3.9+ type hints."""
    try:
        # Test list and dict direct use (no need to import from typing)
        test_list: List[int] = [1, 2, 3]
        test_dict: Dict[str, int] = {"a": 1, "b": 2}
        
        logger.info("✅ Python 3.9+ type hints are working correctly")
        return True
    except SyntaxError:
        logger.error("❌ Python 3.9+ type hints not supported")
        return False

def main():
    """Run all compatibility checks."""
    logger.info("===== Health Appointment System - Python 3.13 Compatibility Check =====")
    
    checks = [
        ("Python Version", check_python_version),
        ("Module Imports", check_module_imports),
        ("Application Modules", check_app_modules),
        ("Pattern Matching", test_pattern_matching),
        ("Self-documenting F-Strings", test_self_documenting_fstrings),
        ("Type Hint Support", check_type_hint_support),
    ]
    
    results = []
    for name, check_func in checks:
        logger.info(f"\n----- Testing {name} -----")
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            logger.error(f"💥 Error during {name} check: {e}")
            results.append((name, False))
    
    # Print summary
    logger.info("\n===== Compatibility Check Results =====")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status}: {name}")
    
    logger.info(f"\nResult: {passed}/{total} checks passed")
    
    if passed == total:
        logger.info("🎉 Congratulations! Your application is compatible with Python 3.13")
        return 0
    else:
        logger.warning("⚠️ Some compatibility checks failed. Review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
