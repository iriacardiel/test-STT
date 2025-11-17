import os

from dotenv import load_dotenv  # pip install python-dotenv

load_dotenv()


class Settings:

    BASE_FOLDER = os.environ.get("BASE_FOLDER")
    TEST_FOLDER = os.environ.get("TEST_FOLDER")
    
    STT_SERVICE_URL = os.environ.get("STT_SERVICE_URL")
    GOLD_STANDARD_FILE = os.environ.get("GOLD_STANDARD_FILE")
    RUNS = os.environ.get("RUNS")

    TEST_RESULT_FILE = os.environ.get("TEST_RESULT_FILE")