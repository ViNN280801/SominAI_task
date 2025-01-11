import os
import sys
import pytest


def main():
    """
    Main function to discover and run all tests recursively.
    """
    # Get the root directory of the project
    root_dir = os.path.dirname(os.path.abspath(__file__))

    # Run pytest on all test files recursively
    pytest_args = [root_dir]
    exit_code = pytest.main(pytest_args)

    # Exit with the pytest exit code
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
