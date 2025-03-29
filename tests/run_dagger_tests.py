#!/usr/bin/env python
"""
Main test runner for Dagger integration tests.
"""
import os
import sys
import subprocess
import argparse


def run_tests(test_type=None, verbose=False, coverage=False):
    """Run the specified tests."""
    # Base directory of the tests
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Build the pytest command
    cmd = ["pytest"]
    
    # Add verbosity
    if verbose:
        cmd.append("-v")
    
    # Add coverage
    if coverage:
        cmd.extend(["--cov=src", "--cov-report=term", "--cov-report=html"])
    
    # Add test type selection
    if test_type == "unit":
        cmd.append(os.path.join(base_dir, "dagger/unit"))
    elif test_type == "integration":
        cmd.append(os.path.join(base_dir, "dagger/integration"))
    elif test_type == "error":
        cmd.append(os.path.join(base_dir, "dagger/error_handling"))
    elif test_type == "all":
        cmd.append(os.path.join(base_dir, "dagger"))
    else:
        # Default to all tests
        cmd.append(os.path.join(base_dir, "dagger"))
    
    # Run the tests
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    
    return result.returncode


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Dagger integration tests")
    parser.add_argument("--type", choices=["unit", "integration", "error", "all"],
                        default="all", help="Type of tests to run")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--coverage", "-c", action="store_true", help="Generate coverage report")
    
    args = parser.parse_args()
    
    sys.exit(run_tests(args.type, args.verbose, args.coverage))