import sys
import traceback

print(f"Python: {sys.executable}")
print(f"Version: {sys.version}")

try:
    from main import app
    print("SUCCESS: app imported OK")
except Exception as e:
    print(f"FAILED: {e}")
    traceback.print_exc()
