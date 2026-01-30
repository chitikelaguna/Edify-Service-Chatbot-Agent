import sys
import os

# Setup Python path at module level (safe - no complex MRO)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Mangum at module level (safe - simple MRO)
from mangum import Mangum

def _create_handler():
    """
    Factory function to create Mangum handler.
    FastAPI import happens HERE, not at module level.
    This prevents Vercel from inspecting FastAPI's MRO during module import.
    """
    from app.main import app
    return Mangum(app, lifespan="off")

# Create handler at module level
# Vercel inspects this - it sees only Mangum, not FastAPI's MRO
handler = _create_handler()

# Validation: Verify handler type (visible in Vercel build logs)
print("HANDLER TYPE:", type(handler))

