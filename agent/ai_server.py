"""Container AI Server - HTTP interface for CloudRun

This is the entry point for uvicorn. The actual implementation
is in the agent.server package.

Usage:
    uvicorn agent.ai_server:app --host 0.0.0.0 --port 8000
"""

from agent.server import app

__all__ = ["app"]
