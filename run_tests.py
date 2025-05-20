#!/usr/bin/env python
"""
Script to run tests for Milestone 3.
"""

import os
import sys
import subprocess
import argparse


def run_tests(test_type=None, verbose=False):
    """Run the tests."""
    # Determine the command
    cmd = ["pytest"]
    
    # Add verbosity
    if verbose:
        cmd.append("-v")
    
    # Add test type
    if test_type == "unit":
        cmd.append("tests/unit/")
    elif test_type == "integration":
        cmd.append("tests/integration/")
    else:
        cmd.append("tests/")
    
    # Run the tests
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Print the output
    print(result.stdout)
    
    if result.stderr:
        print("Errors:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
    
    # Return the exit code
    return result.returncode


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run tests for Milestone 3")
    parser.add_argument(
        "--type",
        choices=["unit", "integration", "all"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # Run the tests
    test_type = None if args.type == "all" else args.type
    exit_code = run_tests(test_type, args.verbose)
    
    # Exit with the same code
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
