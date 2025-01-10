#! python3.13

import os
import pytest


def main():
    """
    Main function to discover and run all tests recursively.
    """
    # Get the root directory of the project
    root_dir = os.path.dirname(os.path.abspath(__file__))

    # Run pytest on all test files recursively
    pytest_args = [root_dir]
    pytest.main(pytest_args)


if __name__ == "__main__":
    main()
