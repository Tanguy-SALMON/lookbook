
"""
Images API Router

This module handles endpoints for image proxying and serving
with CORS control for embedding in external applications.
"""

from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import RedirectResponse, StreamingResponse
from typing import Dict, Any, Optional
import logging
import structlog
import httpx
from io import BytesIO

