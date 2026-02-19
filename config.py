import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Cloudflare API Configuration
    CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")

    # MongoDB Configuration
    MONGODB_URI = os.getenv("MONGODB_URI")
    DB_NAME = "vercel"
    COLLECTION_NAME = "dfyinfrasetups"

    TRACKING_CSV_PATH = os.getenv("TRACKING_CSV_PATH", "processed_domains.csv")
    REPORTS_DIR = os.getenv("REPORTS_DIR", "reports")
    LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "automation.log")
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", "6"))
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))
    COOLDOWN_SLEEP = int(os.getenv("COOLDOWN_SLEEP", "15"))
    
    @classmethod
    def get_report_path(cls):
        if not os.path.exists(cls.REPORTS_DIR):
            os.makedirs(cls.REPORTS_DIR)
        timestamp = __import__('datetime').datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return os.path.join(cls.REPORTS_DIR, f"domain_updates_{timestamp}.xlsx")

    @classmethod
    def validate(cls):
        if not cls.CLOUDFLARE_API_TOKEN:
            raise ValueError("CLOUDFLARE_API_TOKEN is not set in .env")
        # No error if CSV doesn't exist, we will create it.

config = Config()
