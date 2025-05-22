import unittest
import sys
import os
from pathlib import Path

def setup_python_path():
    # Get the absolute path to the project root
    project_root = Path(__file__).resolve().parent
    
    # Add project root to Python path if not already there
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Also add the parent directory to handle the utils import
    parent_dir = project_root.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))

if __name__ == '__main__':
    # Setup Python path
    setup_python_path()
    
    # Import test modules
    from tests.test_text_matching import TestTajweedMatching
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTajweedMatching)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate status code
    sys.exit(not result.wasSuccessful()) 