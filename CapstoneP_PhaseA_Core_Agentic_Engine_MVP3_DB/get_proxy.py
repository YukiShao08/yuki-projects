"""
New Python file
"""

from typing import Tuple, Optional
from dotenv import load_dotenv
from pathlib import Path
import os


def get_proxy() -> Tuple[Optional[str], Optional[str]]: #fix number of value, so use Tuple instead of list.
    """
    Get the proxy from the environment variables
    """
    BASE_DIR = Path(__file__).resolve().parent
    env_path = BASE_DIR / ".env"
    load_dotenv(dotenv_path=env_path)

    http_proxy = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
    https_proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
    proxy_port = os.getenv("PROXY_PORT", "7890")

    if not http_proxy:
        http_proxy = f"http://127.0.0.1:{proxy_port}"
    if not https_proxy:
        https_proxy = http_proxy

    os.environ["HTTP_PROXY"] = http_proxy
    os.environ["HTTPS_PROXY"] = https_proxy

    return http_proxy, https_proxy

if __name__ == "__main__":
    print(get_proxy())


