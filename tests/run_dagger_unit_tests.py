#!/usr/bin/env python3
"""
Run unit tests for the Dagger integration, bypassing the problematic imports.
"""
import os
import sys
import unittest
import importlib.util

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Create a test suite
suite = unittest.TestSuite()

# Define the test modules to run
test_modules = [
    'tests.dagger.unit.test_dagger_adapter_config'
]

# Load and add the test modules to the suite
for module_name in test_modules:
    try:
        # Try direct import first
        module = __import__(module_name, fromlist=['*'])
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, type) and issubclass(obj, unittest.TestCase):
                suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(obj))
    except ImportError as e:
        print(f"Could not import {module_name}: {e}")
        # Try loading from file path
        module_path = module_name.replace('.', '/') + '.py'
        if os.path.exists(module_path):
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            for name in dir(module):
                obj = getattr(module, name)
                if isinstance(obj, type) and issubclass(obj, unittest.TestCase):
                    suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(obj))
        else:
            print(f"Module file {module_path} not found")

# Run the tests
if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(not result.wasSuccessful())