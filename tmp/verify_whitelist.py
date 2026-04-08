import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.db_service import is_user_blocked
from backend.config import WHITELIST_PSIDS

def test_whitelist():
    test_id = "27197242823207121"
    print(f"Checking if {test_id} is in WHITELIST_PSIDS: {test_id in WHITELIST_PSIDS}")
    
    blocked = is_user_blocked(test_id)
    print(f"Is {test_id} blocked? {blocked}")
    
    if not blocked and test_id in WHITELIST_PSIDS:
        print("✅ SUCCESS: Whitelisted user is NOT blocked.")
    else:
        print("❌ FAILURE: Whitelist logic failed.")

if __name__ == "__main__":
    test_whitelist()
