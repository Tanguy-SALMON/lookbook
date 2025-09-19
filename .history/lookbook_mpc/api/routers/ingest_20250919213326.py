
"""
Ingest API Router

This module handles endpoints for ingesting fashion items
from the shop catalog into the lookbook system.
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from typing import Dict, Any, Optional
import logging
import structlog

from ...domain.entities import IngestRequest, IngestResponse
from ...domain.use_cases import IngestItems
from ...adapters.db_shop import MockShopCatalogAdapter
from ...adapters.vision import MockVisionProvider
