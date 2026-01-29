import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Mangum first to ensure it's available
from mangum import Mangum

# Import FastAPI app
from app.main import app

# Create Mangum handler - this must be the ONLY handler export
# Vercel inspects handler.__class__.__mro__, so Mangum's clean MRO prevents issubclass() errors
handler = Mangum(app, lifespan="off")

# Verify handler type at import time (visible in Vercel build logs)
if __name__ == "__main__" or os.getenv("VERCEL"):
    print(f"VERCEL_HANDLER_TYPE: {type(handler).__module__}.{type(handler).__name__}")

