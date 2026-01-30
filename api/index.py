import sys
import os

# Setup Python path at module level (safe - no complex MRO)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class VercelHandlerProxy:
    """
    Proxy class with simple MRO that Vercel can safely inspect.
    Delays FastAPI import until handler is actually called.
    Vercel inspects this class's MRO (simple: VercelHandlerProxy, object),
    not FastAPI's complex MRO chain.
    """
    _handler_cache = None  # Class-level cache to avoid instance attributes
    
    def __call__(self, event, context):
        """Delegate to actual Mangum handler - creates on first call."""
        if VercelHandlerProxy._handler_cache is None:
            from mangum import Mangum
            from app.main import app
            VercelHandlerProxy._handler_cache = Mangum(app, lifespan="off")
        return VercelHandlerProxy._handler_cache(event, context)

# Create proxy instance at module level
# Vercel inspects this - it sees only VercelHandlerProxy (simple MRO), not FastAPI
handler = VercelHandlerProxy()

# Validation: Verify handler type (visible in Vercel build logs)
print("HANDLER TYPE:", type(handler))
print("HANDLER MRO:", handler.__class__.__mro__)

