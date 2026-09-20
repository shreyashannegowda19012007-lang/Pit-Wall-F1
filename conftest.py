import pytest
import os
import glob

@pytest.fixture(scope="session", autouse=True)
def cleanup_test_dbs():
    """Clean up any ephemeral test SQLite databases after all tests run."""
    yield
    for db_file in glob.glob("test_*.db"):
        try:
            os.remove(db_file)
        except OSError:
            pass
