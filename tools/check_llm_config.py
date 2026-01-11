import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.config import config

print("START_CONFIG_CHECK")
try:
    llm_config = config.llm.get("default")
    if llm_config:
        model = llm_config.model
        base_url = llm_config.base_url
        print(f"MODEL:{model}")
        print(f"BASE_URL:'{base_url}'")
    else:
        print("NO_DEFAULT_CONFIG")
except Exception as e:
    print(f"ERROR:{e}")
print("END_CONFIG_CHECK")
