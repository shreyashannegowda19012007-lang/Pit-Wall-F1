import pytest
import time
import sys
import os

sys.path.insert(0, os.path.abspath('src'))
from universal_session_engine import SessionPreparationManager
import fastf1
import logging

fastf1.set_log_level(logging.WARNING)

@pytest.fixture(autouse=True, scope="session")
def prepare_test_session():
    print("\nPreparing test session data (2024 SPAIN R)...")
    SessionPreparationManager.prepare_session_async(2024, "SPAIN", "R")

    for _ in range(90):
        status = SessionPreparationManager.check_session_status(2024, "SPAIN", "R")
        if status["status"] == "READY":
            print("Test session data READY.")
            break
        time.sleep(1)
