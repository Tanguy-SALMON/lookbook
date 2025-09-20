# Lookbook-MPC User Guide

## Overview

This guide covers how to use the Lookbook-MPC system after setup is complete. For installation instructions, see `SETUP_GUIDE.md`.

## Using the System

### Web Interfaces

#### Admin Dashboard (Recommended)
**URL**: http://localhost:3000

Modern Next.js dashboard providing:
- **Real-time monitoring** of all services
- **Product management** with comprehensive attribute editing
- **Analytics** showing processed items, recommendations, and chat sessions
- **One-click operations** for ingestion and system control
- **Visual stats** with category distribution and performance metrics

Key features:
- Items page with full attribute editing (category, material, pattern, season, occasion, fit, style, etc.)
- System status monitoring
- Performance analytics
- Recent activity feed

#### Demo Chat Interface
**URL**: http://localhost:8000/demo

Simple chat interface for testing recommendations:
- Type natural language fashion requests
- Get AI-powered outfit suggestions
- See visual product recommendations

#### API Documentation
**URL**: http://localhost:8000/docs

Interactive Swagger documentation for all API endpoints.

### API Usage Patterns

#### Basic Workflow

1. **Ingest Products**
```bash
# Basic ingestion
curl -X POST "http://localhost:8000/v1/ingest/products" \
  -H "Content-Type: application/json" \
  -d '{"limit": 20}'

# With date filter
curl -X POST "http://localhost:8000/v1/ingest/products" \
  -H "Content-Type: application/json" \
  -d '{"limit": 50, "since": "2025-01-19T00:00:00Z"}'
```

2. **Get Recommendations**
```bash
curl -X POST "http://localhost:8000/v1/recommendations" \
  -H "Content-Type: application/json" \
  -d '{"text_query": "I want to do yoga"}'
```

3. **Chat Interaction**
```bash
curl -X POST "http://localhost:8000/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "user-123", "message": "I need an outfit for a business meeting"}'
```

#### Common Request Examples

**Activity-based requests:**
- "I want to do yoga"
- "Going for a run tomorrow morning"
- "Need gym clothes"

**Occasion-based requests:**
- "Restaurant this weekend, attractive for $50"
- "Business meeting outfit"
- "Date night outfit under $100"

**Style-based requests:**
- "I am fat, look slim"
- "Something casual but stylish"
- "Professional but comfortable"

**Constraint-based requests:**
- "Winter outfit under $200"
- "Formal dress for size L"
- "Casual top in black or white"

### Advanced Usage

#### Chat Sessions

Create persistent conversations:
```bash
# Start session
curl -X POST "http://localhost:8000/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "session-abc", "message": "I need help with my wardrobe"}'

# Continue conversation
curl -X POST "http://localhost:8000/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "session-abc", "message": "Show me business casual options"}'

# List sessions
curl "http://localhost:8000/v1/chat/sessions"
```

#### Product Search and Filtering

```bash
# List products with filters
curl "http://localhost:8000/v1/ingest/products?category=top&limit=20"

# Get ingestion statistics
curl "http://localhost:8000/v1/ingest/stats"

# Popular recommendations
curl "http://localhost:8000/v1/recommendations/popular?limit=10"

# Trending by category
curl "http://localhost:8000/v1/recommendations/trending?category=outerwear&limit=5"
```

#### Image Access

```bash
# Get product image
curl "http://localhost:8000/v1/images/product_image_key_here"

# Get image info
curl "http://localhost:8000/v1/images/info/product_image_key_here"

# Redirect to original image
curl "http://localhost:8000/v1/images/product_image_key_here/redirect"
```

## Understanding the AI System

### How Recommendations Work

1. **Intent Analysis**: Your text query is analyzed by the qwen3:4b model to extract:
   - Activity/occasion (yoga, business meeting, date)
   - Style preferences (casual, formal, attractive)
   - Constraints (budget, size, color)
   - Body considerations (slim-fit, flattering)

2. **Product Matching**: The system queries the catalog for items matching your intent
3. **Vision Analysis**: Product images are analyzed by qwen2.5vl to extract:
   - Color, material, pattern
   - Style, fit, season appropriateness
   - Category and occasion suitability

4. **Rule Engine**: Fashion rules are applied to create coherent outfits:
   - Color coordination
   - Style consistency
   - Occasion appropriateness
   - Seasonal matching

5. **Outfit Assembly**: Complete outfits are created with 3-7 items each:
   - Top, bottom, shoes
   - Outerwear (when appropriate)
   - Accessories

### Response Format

Recommendations include:
- **Outfits**: Complete clothing combinations
- **Rationale**: Why each outfit was recommended
- **Item Details**: SKU, title, price, attributes
- **Images**: Product photos when available
- **Constraints Used**: How your request was interpreted

## Monitoring and Management

### System Health

```bash
# Quick health check
curl http://localhost:8000/health

# Comprehensive readiness check
curl http://localhost:8000/ready
```

The readiness check verifies:
- Ollama connectivity and models
- Vision sidecar availability
- Image CDN accessibility
- Database connectivity

### Performance Monitoring

Use the admin dashboard (http://localhost:3000) to monitor:
- **Processing times** for image analysis
- **Success rates** for recommendations
- **Error rates** and failed operations
- **Recent activity** across all components

### Data Management

**View ingestion statistics:**
```bash
curl http://localhost:8000/v1/ingest/stats
```

**Check specific products via admin dashboard:**
- Navigate to Items page
- Use search and filtering
- Edit product attributes
- View processing status

## Best Practices

### For Better Recommendations

1. **Be specific about context:**
   - ✅ "Business meeting in winter"
   - ❌ "Need clothes"

2. **Include constraints:**
   - ✅ "Casual date outfit under $80"
   - ❌ "Something nice"

3. **Mention preferences:**
   - ✅ "I prefer dark colors and loose fit"
   - ❌ "Whatever looks good"

### For System Management

1. **Regular ingestion:**
   - Ingest new products daily/weekly
   - Use date filters to only process new items
   - Monitor ingestion stats

2. **Monitor performance:**
   - Check system health regularly
   - Review error rates in admin dashboard
   - Ensure all models are loaded

3. **Data quality:**
   - Use admin dashboard to edit incorrect product attributes
   - Review vision analysis results for accuracy
   - Update product information as needed

## Troubleshooting Usage Issues

### No Recommendations Returned

```bash
# Check if products are available
curl http://localhost:8000/v1/ingest/stats

# If no products, ingest some
curl -X POST "http://localhost:8000/v1/ingest/products" \
  -d '{"limit": 50}' -H "Content-Type: application/json"
```

### Poor Quality Recommendations

1. **Check product data quality:**
   - Use admin dashboard to review product attributes
   - Ensure vision analysis has completed
   - Verify product categorization

2. **Refine your requests:**
   - Be more specific about context
   - Include budget and size constraints
   - Mention style preferences

### Chat Context Issues

```bash
# Use consistent session IDs
# Each conversation should maintain the same session_id

# List active sessions to debug
curl "http://localhost:8000/v1/chat/sessions"

# Review specific session
curl "http://localhost:8000/v1/chat/sessions/your-session-id"
```

### Image Loading Issues

1. **Check CDN connectivity:**
   ```bash
   curl -I "https://d29c1z66frfv6c.cloudfront.net/pub/media/catalog/product/large/sample_image.jpg"
   ```

2. **Use image proxy:**
   ```bash
   # Instead of direct CDN access
   curl "http://localhost:8000/v1/images/your_image_key"
   ```

## Advanced Features

### MCP Integration

For LLM clients that support Model Context Protocol:

**Available tools:**
- `recommend_outfits(query, budget?, size?)` - Get recommendations
- `search_items(filters)` - Search product catalog
- `ingest_batch(limit?)` - Trigger product ingestion

**MCP server endpoint:** http://localhost:8000/mcp

### Custom Rules

The system uses built-in fashion rules, but you can understand how they work:

1. **Color coordination rules**
2. **Seasonal appropriateness**
3. **Occasion matching**
4. **Style consistency**
5. **Fit recommendations**

Rules are applied automatically but can be observed in recommendation rationales.

## Getting Help

- **System issues**: Check `DEBUG_GUIDE.md`
- **Setup problems**: See `SETUP_GUIDE.md`
- **API reference**: http://localhost:8000/docs
- **Admin dashboard help**: Built-in tooltips at http://localhost:3000

For optimal experience, use the admin dashboard for most management tasks and the API for automated interactions.