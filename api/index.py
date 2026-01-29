import sys
import os

# Add project root to Python path FIRST
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Mangum BEFORE importing FastAPI app
# This ensures Mangum is available when handler is created
from mangum import Mangum

# Import FastAPI app
from app.main import app

# CRITICAL: Create Mangum handler immediately after imports
# Vercel inspects handler.__class__.__mro__ during import
# Mangum provides a clean class hierarchy that passes issubclass() checks
handler = Mangum(app, lifespan="off")

# Verify handler is Mangum (visible in Vercel build logs)
print(f"VERCEL_HANDLER_TYPE: {type(handler).__module__}.{type(handler).__name__}")
print(f"VERCEL_HANDLER_MRO: {handler.__class__.__mro__}")

