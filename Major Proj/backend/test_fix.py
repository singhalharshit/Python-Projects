
import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

from app.services.intelligence.profile_analyzer_v2 import profile_analyzer

print("Running manual test...")
try:
    result = profile_analyzer.analyze_profile("aliabdaal")
    print("\n\nSUCCESS! Result:")
    import json
    # Custom encoder for non-serializable objects if any
    print(json.dumps(result, indent=2, default=str))
except Exception as e:
    print(f"\n\nERROR: {e}")
    import traceback
    traceback.print_exc()
