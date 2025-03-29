#!/usr/bin/env python3
"""
Simple verification script for the Dagger Workflow Integration task.
This script checks if the required files exist and have content.
"""

import os
import sys

def verify_implementation():
    """Verify that the Dagger Workflow Integration implementation is complete."""
    # Check if the implementation file exists
    implementation_file = "src/task_manager/mcp_servers/dagger_workflow_integration.py"
    if not os.path.exists(implementation_file):
        print(f"Error: Implementation file {implementation_file} does not exist.")
        return False
    
    # Check if the implementation file has content
    if os.path.getsize(implementation_file) == 0:
        print(f"Error: Implementation file {implementation_file} is empty.")
        return False
    
    # Check if the README file exists
    readme_file = "docs/guides/DAGGER_WORKFLOW_INTEGRATION_README.md"
    if not os.path.exists(readme_file):
        print(f"Error: README file {readme_file} does not exist.")
        return False
    
    # Check if the README file has content
    if os.path.getsize(readme_file) == 0:
        print(f"Error: README file {readme_file} is empty.")
        return False
    
    # Check if the test file exists
    test_file = "tests/test_dagger_workflow_integration.py"
    if not os.path.exists(test_file):
        print(f"Error: Test file {test_file} does not exist.")
        return False
    
    # Check if the test file has content
    if os.path.getsize(test_file) == 0:
        print(f"Error: Test file {test_file} is empty.")
        return False
    
    print("Verification successful! All required files exist and have content.")
    return True

if __name__ == "__main__":
    success = verify_implementation()
    sys.exit(0 if success else 1)
