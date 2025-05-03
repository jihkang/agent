from utils.util import safe_import
from pathlib import Path


def load_dotenv():
    dotenv = safe_import("python-dotenv", "dotenv")
    env_path = Path(".env")
    if env_path.exists():
        dotenv.load_dotenv(dotenv_path = env_path, override=True)

