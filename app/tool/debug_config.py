
import sys
import os

# Add project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import config

def check_config():
    print("🔍 Checking Amap Configuration...")
    
    if hasattr(config, 'amap'):
        print(f"✅ [amap] section found.")
        
        api_key = getattr(config.amap, 'api_key', None)
        sec_code = getattr(config.amap, 'security_js_code', None)
        web_key = getattr(config.amap, 'web_service_key', None)
        
        print(f"   - api_key (JS): {'PRESENT' if api_key else 'MISSING'} ({api_key[:4]}... if present)")
        print(f"   - security_js_code: {'PRESENT' if sec_code else 'MISSING'} ({sec_code[:4]}... if present)")
        print(f"   - web_service_key: {'PRESENT' if web_key else 'MISSING'}")
        
        if not sec_code:
            print("❌ security_js_code is MISSING from loaded config!")
            print("   Please check config/config.toml")
    else:
        print("❌ [amap] section MISSING in config object!")

if __name__ == "__main__":
    check_config()
