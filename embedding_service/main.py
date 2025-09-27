#!/usr/bin/env python3
"""
LookbookMPC Embedding Service - Simplified Production Version
============================================================

A lightweight, production-ready embedding service for fashion similarity search.
This version is optimized for easy deployment and testing.

Usage:
    python main.py

API Endpoints:
    GET  /health                 - Health check
    POST /embeddings/create      - Create embedding for image
    POST /embeddings/similar     - Find similar products
    GET  /docs                   - API documentation

Requirements:
    pip install torch transformers pillow requests faiss-cpu scikit-learn fastapi uvicorn pydantic
"""

import os
import sys
import sqlite3
import asyncio
import logging
import hashlib
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import traceback

# Core ML libraries
import numpy as np
import torch
from PIL import Image
import requests
from transformers import CLIPProcessor, CLIPModel
from sklearn.metrics.pairwise import cosine_similarity

# FastAPI
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Configuration
class Config:
    # Service
    HOST = "0.0.0.0"
    PORT = 8001

    # Database
    DB_PATH = "../lookbook.db"
    CACHE_PATH = "cache/embeddings.json"

    # Model
    CLIP_MODEL = "openai/clip-vit-base-patch32"
    EMBEDDING_DIM = 512

    # S3
    S3_BASE_URL = "https://d29c1z66frfv6c.cloudfront.net/pub/media/catalog/product/large/"

    # Performance
    MAX_RESULTS = 50
    TIMEOUT = 30

# API Models
class EmbeddingRequest(BaseModel):
    image_url: str = Field(..., description="URL of the image")
    cache: bool = Field(True, description="Cache the result")

class SimilarRequest(BaseModel):
    image_url: str = Field(..., description="Query image URL")
    limit: int = Field(10, ge=1, le=50, description="Number of results")
    category_filter: Optional[str] = Field(None, description="Filter by category")
    color_filter: Optional[str] = Field(None, description="Filter by color")

class Product(BaseModel):
    sku: str
    title: str
    category: str
    color: str
    price: float
    image_url: str
    similarity_score: float

class SimilarResponse(BaseModel):
    products: List[Product]
    query_time_ms: float
    total_processed: int

class EmbeddingResponse(BaseModel):
    embedding: List[float]
    processing_time_ms: float
    cached: bool

# Main Service Class
class EmbeddingService:
    def __init__(self):
        self.setup_logging()
        self.load_models()
        self.products = []
        self.embeddings = []
        self.embedding_cache = {}
        self.load_cache()
        self.preload_products()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def load_models(self):
        """Load CLIP model"""
        try:
            self.logger.info("Loading CLIP model...")
            self.device = "cpu"  # Use CPU for stability

            self.model = CLIPModel.from_pretrained(Config.CLIP_MODEL)
            self.processor = CLIPProcessor.from_pretrained(Config.CLIP_MODEL)
            self.model.eval()

            self.logger.info("✅ CLIP model loaded successfully")

        except Exception as e:
            self.logger.error(f"❌ Failed to load model: {e}")
            raise

    def load_cache(self):
        """Load embedding cache from file"""
        try:
            if os.path.exists(Config.CACHE_PATH):
                with open(Config.CACHE_PATH, 'r') as f:
                    cache_data = json.load(f)
                    # Convert lists back to numpy arrays
                    self.embedding_cache = {
                        k: np.array(v) for k, v in cache_data.items()
                    }
                self.logger.info(f"Loaded {len(self.embedding_cache)} cached embeddings")
            else:
                self.embedding_cache = {}
                self.logger.info("No cache found, starting fresh")

        except Exception as e:
            self.logger.warning(f"Failed to load cache: {e}")
            self.embedding_cache = {}

    def save_cache(self):
        """Save embedding cache to file"""
        try:
            os.makedirs(os.path.dirname(Config.CACHE_PATH), exist_ok=True)
            # Convert numpy arrays to lists for JSON serialization
            cache_data = {
                k: v.tolist() for k, v in self.embedding_cache.items()
            }
            with open(Config.CACHE_PATH, 'w') as f:
                json.dump(cache_data, f)
            self.logger.debug(f"Cache saved with {len(cache_data)} entries")

        except Exception as e:
            self.logger.warning(f"Failed to save cache: {e}")

    def get_products_from_db(self) -> List[Dict]:
        """Load products from database"""
        try:
            if not os.path.exists(Config.DB_PATH):
                self.logger.warning(f"Database not found: {Config.DB_PATH}")
                return self.get_mock_products()

            conn = sqlite3.connect(Config.DB_PATH)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT sku, title, image_key, category, color, price
                FROM products
                WHERE in_stock = 1 OR in_stock IS NULL
                ORDER BY sku
            ''')

            products = []
            for row in cursor.fetchall():
                sku, title, image_key, category, color, price = row
                products.append({
                    'sku': sku,
                    'title': title,
                    'image_key': image_key,
                    'category': category or 'unknown',
                    'color': color or 'unknown',
                    'price': float(price or 0),
                    'image_url': Config.S3_BASE_URL + (image_key or '')
                })

            conn.close()
            self.logger.info(f"Loaded {len(products)} products from database")
            return products

        except Exception as e:
            self.logger.error(f"Database error: {e}")
            return self.get_mock_products()

    def get_mock_products(self) -> List[Dict]:
        """Create mock products for testing"""
        return [
            {
                'sku': 'DEMO001', 'title': 'Red Summer Dress', 'category': 'dress',
                'color': 'red', 'price': 89.99, 'image_key': 'red_dress.jpg',
                'image_url': 'https://example.com/red_dress.jpg'
            },
            {
                'sku': 'DEMO002', 'title': 'Black Sneakers', 'category': 'shoes',
                'color': 'black', 'price': 129.99, 'image_key': 'black_sneakers.jpg',
                'image_url': 'https://example.com/black_sneakers.jpg'
            },
            {
                'sku': 'DEMO003', 'title': 'Blue Jeans', 'category': 'bottom',
                'color': 'blue', 'price': 79.99, 'image_key': 'blue_jeans.jpg',
                'image_url': 'https://example.com/blue_jeans.jpg'
            }
        ]

    def preload_products(self):
        """Load and create embeddings for all products"""
        try:
            self.products = self.get_products_from_db()
            self.logger.info(f"Preloading embeddings for {len(self.products)} products...")

            self.embeddings = []
            for i, product in enumerate(self.products):
                try:
                    embedding = self.get_or_create_embedding(product['image_url'])
                    if embedding is not None:
                        self.embeddings.append(embedding)
                    else:
                        # Create random embedding as fallback
                        self.embeddings.append(np.random.rand(Config.EMBEDDING_DIM))

                    if (i + 1) % 10 == 0:
                        self.logger.info(f"Processed {i + 1}/{len(self.products)} products")

                except Exception as e:
                    self.logger.warning(f"Failed to process product {product['sku']}: {e}")
                    self.embeddings.append(np.random.rand(Config.EMBEDDING_DIM))

            self.save_cache()
            self.logger.info(f"✅ Preloaded {len(self.embeddings)} product embeddings")

        except Exception as e:
            self.logger.error(f"Failed to preload products: {e}")

    def load_image(self, url: str, timeout: int = 10) -> Optional[Image.Image]:
        """Load image from URL with error handling"""
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            image = Image.open(requests.get(url, stream=True).raw)
            return image.convert('RGB')

        except Exception as e:
            self.logger.debug(f"Failed to load image {url}: {e}")
            return self.create_placeholder_image()

    def create_placeholder_image(self) -> Image.Image:
        """Create a simple placeholder image"""
        return Image.new('RGB', (224, 224), color=(128, 128, 128))

    def create_embedding(self, image: Image.Image) -> Optional[np.ndarray]:
        """Create CLIP embedding for image"""
        try:
            inputs = self.processor(images=image, return_tensors="pt")

            with torch.no_grad():
                features = self.model.get_image_features(**inputs)
                # Normalize for cosine similarity
                embedding = features / features.norm(p=2, dim=-1, keepdim=True)

            return embedding.cpu().numpy().flatten()

        except Exception as e:
            self.logger.error(f"Failed to create embedding: {e}")
            return None

    def get_cache_key(self, url: str) -> str:
        """Generate cache key for URL"""
        return hashlib.md5(url.encode()).hexdigest()

    def get_or_create_embedding(self, image_url: str) -> Optional[np.ndarray]:
        """Get embedding from cache or create new one"""
        cache_key = self.get_cache_key(image_url)

        # Check cache first
        if cache_key in self.embedding_cache:
            return self.embedding_cache[cache_key]

        # Create new embedding
        image = self.load_image(image_url)
        if image is None:
            return None

        embedding = self.create_embedding(image)
        if embedding is not None:
            self.embedding_cache[cache_key] = embedding

        return embedding

    def find_similar_products(self, query_embedding: np.ndarray,
                            filters: Dict, limit: int) -> List[Dict]:
        """Find similar products using cosine similarity"""
        try:
            if not self.embeddings:
                return []

            # Calculate similarities
            query = query_embedding.reshape(1, -1)
            embeddings_matrix = np.array(self.embeddings)
            similarities = cosine_similarity(query, embeddings_matrix)[0]

            # Create product-similarity pairs
            results = []
            for i, similarity in enumerate(similarities):
                if i < len(self.products):
                    product = self.products[i].copy()
                    product['similarity_score'] = float(similarity)
                    results.append(product)

            # Apply filters
            if filters.get('category_filter'):
                results = [p for p in results if p['category'] == filters['category_filter']]

            if filters.get('color_filter'):
                results = [p for p in results if p['color'] == filters['color_filter']]

            # Sort by similarity and limit
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            return results[:limit]

        except Exception as e:
            self.logger.error(f"Search error: {e}")
            return []

# Global service instance
service = None

# FastAPI app
app = FastAPI(
    title="LookbookMPC Embedding Service",
    version="1.0.0",
    description="AI-powered fashion similarity search"
)

# CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    global service
    try:
        service = EmbeddingService()
        print("🚀 Embedding service initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize service: {e}")
        raise

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy" if service else "unhealthy",
        "products_loaded": len(service.products) if service else 0,
        "embeddings_cached": len(service.embedding_cache) if service else 0,
        "timestamp": datetime.utcnow().isoformat(),
        "model": Config.CLIP_MODEL
    }

@app.post("/embeddings/create", response_model=EmbeddingResponse)
async def create_embedding_endpoint(request: EmbeddingRequest):
    """Create embedding for an image"""
    start_time = datetime.utcnow()

    try:
        if not service:
            raise HTTPException(status_code=503, detail="Service not initialized")

        cache_key = service.get_cache_key(request.image_url)
        cached = cache_key in service.embedding_cache

        embedding = service.get_or_create_embedding(request.image_url)

        if embedding is None:
            raise HTTPException(status_code=400, detail="Failed to process image")

        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        return EmbeddingResponse(
            embedding=embedding.tolist(),
            processing_time_ms=processing_time,
            cached=cached
        )

    except HTTPException:
        raise
    except Exception as e:
        service.logger.error(f"Create embedding error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/embeddings/similar", response_model=SimilarResponse)
async def find_similar_endpoint(request: SimilarRequest):
    """Find products similar to query image"""
    start_time = datetime.utcnow()

    try:
        if not service:
            raise HTTPException(status_code=503, detail="Service not initialized")

        # Create query embedding
        query_embedding = service.get_or_create_embedding(request.image_url)
        if query_embedding is None:
            raise HTTPException(status_code=400, detail="Failed to process query image")

        # Search for similar products
        filters = {
            'category_filter': request.category_filter,
            'color_filter': request.color_filter
        }

        results = service.find_similar_products(
            query_embedding, filters, request.limit
        )

        # Convert to response format
        products = [
            Product(
                sku=p['sku'],
                title=p['title'],
                category=p['category'],
                color=p['color'],
                price=p['price'],
                image_url=p['image_url'],
                similarity_score=p['similarity_score']
            )
            for p in results
        ]

        query_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        return SimilarResponse(
            products=products,
            query_time_ms=query_time,
            total_processed=len(service.products)
        )

    except HTTPException:
        raise
    except Exception as e:
        service.logger.error(f"Similar search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Get service statistics"""
    if not service:
        return {"error": "Service not initialized"}

    return {
        "products_loaded": len(service.products),
        "embeddings_cached": len(service.embedding_cache),
        "cache_file_exists": os.path.exists(Config.CACHE_PATH),
        "database_exists": os.path.exists(Config.DB_PATH),
        "model": Config.CLIP_MODEL,
        "device": service.device if hasattr(service, 'device') else 'unknown'
    }

if __name__ == "__main__":
    print("🚀 Starting LookbookMPC Embedding Service")
    print(f"📊 Model: {Config.CLIP_MODEL}")
    print(f"🌐 Server: http://{Config.HOST}:{Config.PORT}")
    print(f"📖 API Docs: http://{Config.HOST}:{Config.PORT}/docs")
    print(f"💾 Database: {Config.DB_PATH}")
    print("🔥 Ready for production!")

    try:
        uvicorn.run(
            "main:app",
            host=Config.HOST,
            port=Config.PORT,
            reload=False,
            workers=1
        )
    except KeyboardInterrupt:
        print("\n👋 Service stopped by user")
    except Exception as e:
        print(f"❌ Service error: {e}")
        traceback.print_exc()
