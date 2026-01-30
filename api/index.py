# CRITICAL: Import ONLY standard library at module level
# NO third-party imports until handler is called
import sys
import os

# Setup path
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Handler cache (module-level, but no imports yet)
_handler_instance = None

def handler(event, context):
    """
    Vercel serverless function handler.
    All imports happen INSIDE this function to prevent Vercel inspection issues.
    """
    global _handler_instance
    
    # Create handler on first call only
    if _handler_instance is None:
        # Import ONLY when handler is actually invoked (not during inspection)
        from mangum import Mangum
        from app.main import app
        _handler_instance = Mangum(app, lifespan="off")
    
    # Call the handler
    return _handler_instance(event, context)

