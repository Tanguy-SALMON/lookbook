#!/usr/bin/env python3
"""
Production-Ready Embedding Service for LookbookMPC
=================================================

This file shows how to integrate embeddings into your Next.js application
as a Python microservice. It provides:

1. FastAPI service for embedding generation
2. Vector database integration (FAISS/Pinecone)
3. Product similarity search
4. Fashion-specific enhancements
5. Caching and performance optimizations

Usage:
    python embedding_production_example.py

API Endpoints:
    POST /embeddings/create - Create embedding for image
    POST /embeddings/similar - Find similar products
    GET /embeddings/health - Health check

Integration with Next.js:
    Your Next.js app calls these endpoints for product recommendations
"""

import os
import sqlite3
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional, Any
import hashlib
import json

# Core ML libraries
import numpy as np
import torch
from PIL import Image
import requests
from transformers import CLIPModel, CLIPProcessor

# FastAPI for production API
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Vector database (choose one)
import faiss  # Local option
# import pinecone  # Cloud option (uncomment if using)

# Caching
from functools import lru_cache
import redis  # Optional: for distributed caching

# Configuration
class Config:
    # Database
    DB_PATH = "lookbook.db"
    EMBEDDING_CACHE_PATH = "embeddings_cache.db"

    # Model settings
    CLIP_MODEL = "openai/clip-vit-base-patch32"
    EMBEDDING_DIMENSION = 512

    # API settings
    HOST = "localhost"
    PORT = 8001

    # Performance
    MAX_CACHE_SIZE = 10000
    BATCH_SIZE = 32

    # S3/CDN
    S3_BASE_URL = "https://d29c1z66frfv6c.cloudfront.net/pub/media/catalog/product/large/"

    # Redis (optional)
    REDIS_URL = "redis://localhost:6379"
    CACHE_EXPIRY_HOURS = 24

# Pydantic models for API
class CreateEmbeddingRequest(BaseModel):
    image_url: str = Field(..., description="URL of the image to process")
    product_sku: Optional[str] = Field(None, description="SKU if this is a product")
    cache: bool = Field(True, description="Whether to cache the embedding")

class SimilarProductsRequest(BaseModel):
    image_url: str = Field(..., description="Query image URL")
    limit: int = Field(10, description="Number of results to return")
    category_filter: Optional[str] = Field(None, description="Filter by category")
    color_filter: Optional[str] = Field(None, description="Filter by color")
    price_range: Optional[Tuple[float, float]] = Field(None, description="Price range filter")

class Product(BaseModel):
    sku: str
    title: str
    category: str
    color: str
    price: float
    image_url: str
    similarity_score: Optional[float] = None

class EmbeddingResponse(BaseModel):
    embedding: List[float]
    dimension: int
    processing_time_ms: float

class SimilarProductsResponse(BaseModel):
    products: List[Product]
    query_time_ms: float
    total_candidates: int

# Main embedding service
class ProductionEmbeddingService:
    """Production-ready embedding service with caching and optimization"""

    def __init__(self):
        self.setup_logging()
        self.load_models()
        self.setup_vector_store()
        self.setup_cache()
        self.preload_product_embeddings()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def load_models(self):
        """Load CLIP model with error handling"""
        try:
            self.logger.info("Loading CLIP model...")
            self.device = "cuda" if torch.cuda.is_available() else "cpu"

            # Load model with optimizations
            self.model = CLIPModel.from_pretrained(Config.CLIP_MODEL)
            self.processor = CLIPProcessor.from_pretrained(Config.CLIP_MODEL)
            self.model.to(self.device)
            self.model.eval()  # Set to evaluation mode

            self.logger.info(f"CLIP model loaded on {self.device}")
        except Exception as e:
            self.logger.error(f"Failed to load CLIP model: {e}")
            raise

    def setup_vector_store(self):
        """Initialize vector database"""
        try:
            # FAISS for local development
            self.index = faiss.IndexFlatIP(Config.EMBEDDING_DIMENSION)
            self.product_map = {}  # Maps index position to product SKU
            self.sku_to_index = {}  # Maps SKU to index position

            # For production, consider Pinecone:
            # pinecone.init(api_key="your-key", environment="us-west1-gcp")
            # self.index = pinecone.Index("fashion-embeddings")

            self.logger.info("Vector store initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize vector store: {e}")
            raise

    def setup_cache(self):
        """Setup embedding cache"""
        try:
            # SQLite cache for embeddings
            self.cache_conn = sqlite3.connect(Config.EMBEDDING_CACHE_PATH, check_same_thread=False)
            self.cache_conn.execute('''
                CREATE TABLE IF NOT EXISTS embedding_cache (
                    url_hash TEXT PRIMARY KEY,
                    url TEXT,
                    embedding BLOB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Optional: Redis for distributed caching
            try:
                self.redis_client = redis.from_url(Config.REDIS_URL)
                self.redis_client.ping()
                self.logger.info("Redis cache connected")
            except:
                self.redis_client = None
                self.logger.info("Redis not available, using SQLite cache only")

        except Exception as e:
            self.logger.error(f"Failed to setup cache: {e}")
            raise

    def preload_product_embeddings(self):
        """Load existing product embeddings on startup"""
        try:
            products = self.get_all_products()

            if not products:
                self.logger.info("No products found in database")
                return

            self.logger.info(f"Preloading embeddings for {len(products)} products...")

            # Load embeddings in batches
            for i in range(0, len(products), Config.BATCH_SIZE):
                batch = products[i:i + Config.BATCH_SIZE]
                embeddings = []
                skus = []

                for product in batch:
                    embedding = self.get_or_create_embedding(product['image_url'])
                    if embedding is not None:
                        embeddings.append(embedding)
                        skus.append(product['sku'])

                if embeddings:
                    self.add_to_vector_store(embeddings, skus)

            self.logger.info(f"Preloaded {len(self.product_map)} product embeddings")

        except Exception as e:
            self.logger.error(f"Failed to preload embeddings: {e}")

    def get_all_products(self) -> List[Dict]:
        """Get all products from database"""
        try:
            conn = sqlite3.connect(Config.DB_PATH)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT sku, title, image_key, category, color, price
                FROM products
                WHERE in_stock = 1
                ORDER BY sku
            ''')

            products = []
            for row in cursor.fetchall():
                sku, title, image_key, category, color, price = row
                products.append({
                    'sku': sku,
                    'title': title,
                    'image_key': image_key,
                    'category': category,
                    'color': color,
                    'price': price,
                    'image_url': Config.S3_BASE_URL + image_key
                })

            conn.close()
            return products

        except Exception as e:
            self.logger.error(f"Database error: {e}")
            return []

    def load_image_with_retry(self, url: str, max_retries: int = 3) -> Optional[Image.Image]:
        """Load image with retry logic"""
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                image = Image.open(requests.get(url, stream=True).raw)
                return image.convert('RGB')
            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == max_retries - 1:
                    self.logger.error(f"Failed to load image after {max_retries} attempts: {url}")
                    return None
        return None

    def create_embedding(self, image: Image.Image) -> Optional[np.ndarray]:
        """Create CLIP embedding with error handling"""
        try:
            inputs = self.processor(images=image, return_tensors="pt").to(self.device)

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

    def get_cached_embedding(self, url: str) -> Optional[np.ndarray]:
        """Get embedding from cache"""
        try:
            cache_key = self.get_cache_key(url)

            # Try Redis first
            if self.redis_client:
                cached = self.redis_client.get(f"embedding:{cache_key}")
                if cached:
                    return np.frombuffer(cached, dtype=np.float32)

            # Fallback to SQLite
            cursor = self.cache_conn.cursor()
            cursor.execute('SELECT embedding FROM embedding_cache WHERE url_hash = ?', (cache_key,))
            row = cursor.fetchone()

            if row:
                return np.frombuffer(row[0], dtype=np.float32)

        except Exception as e:
            self.logger.warning(f"Cache retrieval error: {e}")

        return None

    def cache_embedding(self, url: str, embedding: np.ndarray):
        """Cache embedding"""
        try:
            cache_key = self.get_cache_key(url)
            embedding_bytes = embedding.astype(np.float32).tobytes()

            # Cache in Redis
            if self.redis_client:
                self.redis_client.setex(
                    f"embedding:{cache_key}",
                    timedelta(hours=Config.CACHE_EXPIRY_HOURS),
                    embedding_bytes
                )

            # Cache in SQLite
            cursor = self.cache_conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO embedding_cache (url_hash, url, embedding)
                VALUES (?, ?, ?)
            ''', (cache_key, url, embedding_bytes))
            self.cache_conn.commit()

        except Exception as e:
            self.logger.warning(f"Cache storage error: {e}")

    def get_or_create_embedding(self, image_url: str) -> Optional[np.ndarray]:
        """Get embedding from cache or create new one"""
        # Try cache first
        embedding = self.get_cached_embedding(image_url)
        if embedding is not None:
            return embedding

        # Create new embedding
        image = self.load_image_with_retry(image_url)
        if image is None:
            return None

        embedding = self.create_embedding(image)
        if embedding is not None:
            self.cache_embedding(image_url, embedding)

        return embedding

    def add_to_vector_store(self, embeddings: List[np.ndarray], skus: List[str]):
        """Add embeddings to vector store"""
        try:
            embeddings_matrix = np.array(embeddings).astype('float32')
            faiss.normalize_L2(embeddings_matrix)

            start_idx = len(self.product_map)
            self.index.add(embeddings_matrix)

            # Update mappings
            for i, sku in enumerate(skus):
                idx = start_idx + i
                self.product_map[idx] = sku
                self.sku_to_index[sku] = idx

        except Exception as e:
            self.logger.error(f"Failed to add to vector store: {e}")

    def search_similar(self, query_embedding: np.ndarray, k: int = 120) -> List[Tuple[str, float]]:
        """Search for similar products"""
        try:
            query = query_embedding.reshape(1, -1).astype('float32')
            faiss.normalize_L2(query)

            scores, indices = self.index.search(query, min(k, len(self.product_map)))

            results = []
            for idx, score in zip(indices[0], scores[0]):
                if idx in self.product_map:
                    results.append((self.product_map[idx], float(score)))

            return results

        except Exception as e:
            self.logger.error(f"Search error: {e}")
            return []

    def apply_filters(self, products: List[Dict], filters: Dict) -> List[Dict]:
        """Apply business logic filters"""
        filtered = products

        # Category filter
        if filters.get('category_filter'):
            filtered = [p for p in filtered if p['category'] == filters['category_filter']]

        # Color filter
        if filters.get('color_filter'):
            filtered = [p for p in filtered if p['color'] == filters['color_filter']]

        # Price range filter
        if filters.get('price_range'):
            min_price, max_price = filters['price_range']
            filtered = [p for p in filtered if min_price <= p['price'] <= max_price]

        return filtered

# FastAPI app
app = FastAPI(title="LookbookMPC Embedding Service", version="1.0.0")

# CORS for Next.js integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your Next.js app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global service instance
embedding_service = None

@app.on_event("startup")
async def startup_event():
    global embedding_service
    embedding_service = ProductionEmbeddingService()

@app.get("/embeddings/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": embedding_service is not None,
        "products_indexed": len(embedding_service.product_map) if embedding_service else 0,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/embeddings/create", response_model=EmbeddingResponse)
async def create_embedding_endpoint(request: CreateEmbeddingRequest):
    """Create embedding for an image"""
    start_time = datetime.utcnow()

    try:
        embedding = embedding_service.get_or_create_embedding(request.image_url)

        if embedding is None:
            raise HTTPException(status_code=400, detail="Failed to process image")

        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        return EmbeddingResponse(
            embedding=embedding.tolist(),
            dimension=len(embedding),
            processing_time_ms=processing_time
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/embeddings/similar", response_model=SimilarProductsResponse)
async def find_similar_products(request: SimilarProductsRequest):
    """Find products similar to the query image"""
    start_time = datetime.utcnow()

    try:
        # Create query embedding
        query_embedding = embedding_service.get_or_create_embedding(request.image_url)
        if query_embedding is None:
            raise HTTPException(status_code=400, detail="Failed to process query image")

        # Search for candidates
        candidates = embedding_service.search_similar(query_embedding, k=120)

        # Get product details
        all_products = embedding_service.get_all_products()
        product_dict = {p['sku']: p for p in all_products}

        # Convert to Product objects with similarity scores
        products = []
        for sku, similarity in candidates:
            if sku in product_dict:
                product_data = product_dict[sku]
                product = Product(
                    sku=product_data['sku'],
                    title=product_data['title'],
                    category=product_data['category'],
                    color=product_data['color'],
                    price=product_data['price'],
                    image_url=product_data['image_url'],
                    similarity_score=similarity
                )
                products.append(product)

        # Apply filters
        filters = {
            'category_filter': request.category_filter,
            'color_filter': request.color_filter,
            'price_range': request.price_range
        }

        filtered_products = embedding_service.apply_filters(
            [p.dict() for p in products],
            filters
        )

        # Convert back to Product objects and limit results
        final_products = [
            Product(**p) for p in filtered_products[:request.limit]
        ]

        query_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        return SimilarProductsResponse(
            products=final_products,
            query_time_ms=query_time,
            total_candidates=len(candidates)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Background task for adding new products
@app.post("/embeddings/add-product")
async def add_product_embedding(
    sku: str,
    image_url: str,
    background_tasks: BackgroundTasks
):
    """Add embedding for a new product (background task)"""

    async def process_product():
        try:
            embedding = embedding_service.get_or_create_embedding(image_url)
            if embedding is not None:
                embedding_service.add_to_vector_store([embedding], [sku])
                embedding_service.logger.info(f"Added embedding for product {sku}")
            else:
                embedding_service.logger.error(f"Failed to create embedding for {sku}")
        except Exception as e:
            embedding_service.logger.error(f"Error processing product {sku}: {e}")

    background_tasks.add_task(process_product)
    return {"message": f"Queued embedding creation for product {sku}"}

if __name__ == "__main__":
    import uvicorn

    print("🚀 Starting LookbookMPC Embedding Service")
    print(f"📊 Model: {Config.CLIP_MODEL}")
    print(f"🌐 Server: http://{Config.HOST}:{Config.PORT}")
    print(f"📖 Docs: http://{Config.HOST}:{Config.PORT}/docs")
    print("🔥 Ready for Next.js integration!")

    uvicorn.run(
        "embedding_production_example:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=False,  # Set to True for development
        workers=1  # Single worker for shared state
    )
