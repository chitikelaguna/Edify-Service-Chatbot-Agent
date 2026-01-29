"""
Vercel serverless function handler for FastAPI application.
This file is the entry point for Vercel deployments.
"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from mangum import Mangum

# Wrap FastAPI app for Vercel / serverless compatibility
# Mangum prevents Vercel's handler from inspecting FastAPI MRO directly,
# avoiding the issubclass() TypeError crash
handler = Mangum(app, lifespan="off")

