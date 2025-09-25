# Recommendation Engine Guide

## Overview

The Lookbook-MPC recommendation engine is a sophisticated AI-powered system that converts natural language requests into fashion outfit recommendations. It combines Large Language Models (LLMs) with rule-based logic to understand user intent and provide personalized fashion suggestions.

## Architecture Overview

```
User Message → Intent Parser → Smart Recommender → Product Search → Outfit Assembly → Response
     ↓              ↓              ↓                ↓               ↓             ↓
"I go dance"   LLM Analysis    Keyword Gen     Database Query   Rule Engine   JSON Response
```

## Core Components

### 1. Intent Parser (`lookbook_mpc/adapters/intent.py`)

**Purpose**: Converts natural language into structured intent using LLM

**Input**: `"I go to dance"`
**Output**: 
```json
{
  "intent": "recommend_outfits",
  "activity": "dancing", 
  "occasion": "party",
  "objectives": ["style", "trendy"],
  "formality": "elevated",
  "natural_response": "Perfect! I'll help you find stylish outfits for dancing..."
}
```

**How it works**:
1. Uses flexible LLM provider (Ollama or OpenRouter)
2. Sends structured prompt with examples to LLM
3. Parses JSON response with fallback handling
4. Returns structured intent + natural response

### 2. Smart Recommender (`lookbook_mpc/services/smart_recommender.py`)

**Purpose**: Core recommendation logic using LLM-generated keywords

**Flow**:
```
User Message → LLM Keyword Generation → Product Search → Outfit Assembly
```

**Key Methods**:

#### `recommend_outfits(user_message, limit=5)`
- **Input**: `"I go to dance"`, `limit=5`
- **Output**: Array of outfit recommendations
- **Process**: Orchestrates the entire recommendation pipeline

#### `_generate_keywords_from_message(message)`
- **Input**: `"I go to dance"`
- **Output**: 
```json
{
  "keywords": ["party", "dance", "movement", "stylish", "trendy"],
  "colors": ["black", "navy", "white"],
  "occasions": ["party", "festival", "concert"],
  "styles": ["trendy", "chic", "modern"],
  "categories": ["dress", "top", "bottom"],
  "materials": ["stretchy", "comfortable"],
  "mood": "confident and ready to dance"
}
```

#### `_search_products_by_keywords(keywords, limit=15)`
- **Input**: Generated keywords dictionary
- **Output**: Scored product list
- **Process**: 
  1. Builds SQL query with keyword matching
  2. Searches across product attributes (color, style, material, title)
  3. Calculates relevance scores for each product
  4. Returns top-scoring products

#### `_create_outfit_combinations(products, keywords, limit)`
- **Input**: Product list, keywords, outfit limit
- **Output**: Complete outfit recommendations
- **Process**:
  1. Groups products by category (tops, bottoms, dresses)
  2. Creates outfit combinations following rules
  3. Checks color compatibility
  4. Generates titles and explanations
  5. Returns formatted outfit objects

### 3. Rules Engine (`lookbook_mpc/services/rules.py`)

**Purpose**: Maps intents to specific fashion constraints

**Pre-defined Rule Sets**:

#### Yoga Rules
```json
{
  "constraints": {
    "category": ["top", "bottom"],
    "material": ["cotton", "nylon", "spandex"],
    "stretch": true,
    "comfort": "high",
    "formality": "athleisure"
  },
  "objectives": ["comfort", "flexibility"],
  "excluded_categories": ["dress", "outerwear"]
}
```

#### Dinner Rules
```json
{
  "constraints": {
    "category": ["top", "bottom", "dress"],
    "formality": "elevated",
    "occasion": "dinner"
  },
  "objectives": ["style", "confidence"],
  "budget_range": [30, 150]
}
```

#### Slimming Rules
```json
{
  "constraints": {
    "color": ["dark", "monochrome", "navy", "black"],
    "pattern": ["plain", "vertical"],
    "fit": ["slim", "regular"]
  },
  "excluded_patterns": ["horizontal", "large_print"],
  "excluded_colors": ["white", "light_colors"]
}
```

### 4. LLM Provider System (`lookbook_mpc/adapters/llm_providers.py`)

**Purpose**: Flexible LLM backend supporting multiple providers

**Supported Providers**:
- **Ollama**: Local models (qwen3, llama3.2)
- **OpenRouter**: Cloud models with free tiers

**Configuration**:
```bash
# Local Ollama
export LLM_PROVIDER="ollama"
export OLLAMA_HOST="http://localhost:11434"
export LLM_MODEL="qwen3:4b-instruct"

# Cloud OpenRouter  
export LLM_PROVIDER="openrouter"
export OPENROUTER_API_KEY="sk-or-v1-..."
export LLM_MODEL="qwen/qwen-2.5-7b-instruct:free"
```

### 5. Chat Use Case (`lookbook_mpc/domain/use_cases.py`)

**Purpose**: Orchestrates the complete chat interaction

**Flow**:
1. Parse user intent using LLM
2. Determine if recommendation is needed
3. Generate outfit suggestions via Smart Recommender
4. Format response for frontend
5. Return ChatResponse with natural language + outfits

## Complete Request Flow

### Example: "I go to dance"

#### Step 1: Intent Parsing
```python
# Input: "I go to dance"
intent = await intent_parser.parse_intent("I go to dance")
# Output: {"activity": "dancing", "occasion": "party", "formality": "elevated", ...}
```

#### Step 2: Keyword Generation  
```python
# LLM expands the request
keywords = await smart_recommender._generate_keywords_from_message("I go to dance")
# Output: {"keywords": ["party", "dance", "stylish"], "colors": ["black", "navy"], ...}
```

#### Step 3: Product Search
```python
# Search database using keywords
products = await smart_recommender._search_products_by_keywords(keywords, 15)
# Output: [{"sku": "123", "title": "Black Top", "score": 0.85}, ...]
```

#### Step 4: Outfit Assembly
```python
# Create outfit combinations
outfits = await smart_recommender._create_outfit_combinations(products, keywords, 3)
# Output: [{"title": "Party Ready Look", "items": [...], "total_price": 89.0}, ...]
```

#### Step 5: Response Formatting
```python
# Format for frontend
response = ChatResponse(
    replies=[{"type": "recommendations", "message": "Perfect! I'll help...", "outfits": 2}],
    outfits=[...],  # Complete outfit data
    session_id="uuid-1234"
)
```

## Database Schema

### Product Tables
```sql
-- Main products table
CREATE TABLE products (
  id INT PRIMARY KEY,
  sku VARCHAR(50),
  title VARCHAR(255),
  price DECIMAL(10,2),
  size_range VARCHAR(50),
  image_key VARCHAR(255)
);

-- Product visual attributes (from AI vision analysis)  
CREATE TABLE product_visual_attributes (
  product_id INT,
  occasion VARCHAR(100),
  color VARCHAR(50),
  style VARCHAR(100), 
  material VARCHAR(100),
  pattern VARCHAR(100),
  fit VARCHAR(50)
);
```

### Scoring Algorithm

Products are scored based on keyword relevance:

```python
def _calculate_keyword_score(self, product, keywords):
    """
    Score products based on keyword matching.
    
    Input: product = {"title": "Black Party Dress", "color": "black", ...}
           keywords = {"keywords": ["party", "stylish"], "colors": ["black"]}
    Output: score = 0.85 (float between 0-1)
    """
    score = 0.0
    total_possible = 0
    
    # Color matching (high weight)
    if keywords.get("colors"):
        total_possible += 0.3
        if product.get("color") in keywords["colors"]:
            score += 0.3
    
    # Keyword matching in title/description  
    if keywords.get("keywords"):
        total_possible += 0.4
        title_lower = product.get("title", "").lower()
        matches = sum(1 for kw in keywords["keywords"] if kw in title_lower)
        score += (matches / len(keywords["keywords"])) * 0.4
    
    # Style matching
    if keywords.get("styles"):
        total_possible += 0.3
        if product.get("style") in keywords["styles"]:
            score += 0.3
    
    return score / total_possible if total_possible > 0 else 0.0
```

## API Response Format

### Chat Endpoint Response
```json
{
  "session_id": "uuid-1234-5678",
  "replies": [
    {
      "type": "recommendations", 
      "message": "Perfect! I'll help you find stylish outfits for dancing. I found 2 great outfits for you!",
      "outfits": 2
    }
  ],
  "outfits": [
    {
      "title": "Party Ready Look",
      "items": [
        {
          "sku": "0888940046012",
          "title": "RIBBED TANK TOP", 
          "price": 79.0,
          "image_url": "https://cdn.../image.jpg",
          "color": "black",
          "category": "top",
          "relevance_score": 0.89
        },
        {
          "sku": "0888940046013", 
          "title": "PARTY SKIRT",
          "price": 45.0,
          "image_url": "https://cdn.../skirt.jpg", 
          "color": "black",
          "category": "bottom",
          "relevance_score": 0.82
        }
      ],
      "total_price": 124.0,
      "rationale": "This black top paired with party skirt creates the perfect dancing look - stylish and comfortable for movement",
      "score": 0.85,
      "outfit_type": "coordinated_set"
    }
  ]
}
```

## Error Handling & Fallbacks

### LLM Failures
- **Intent Parser**: Falls back to generic casual intent
- **Keyword Generation**: Uses rule-based keyword extraction
- **Provider Switching**: Automatically tries Ollama if OpenRouter fails

### Empty Results
- **No Products Found**: Returns helpful message explaining the search
- **No Outfits Created**: Suggests broader search terms
- **Database Errors**: Returns cached recommendations if available

## Performance Considerations

### Caching
- **Intent Results**: Cache parsed intents for repeated messages
- **Product Searches**: Cache keyword searches for 5 minutes
- **LLM Responses**: Cache common request patterns

### Optimization
- **Keyword Limiting**: Max 10 keywords per search to prevent slow queries
- **Product Limiting**: Fetch max 15 products per search
- **Timeout Handling**: 10s timeout for LLM calls, 5s for database

### Monitoring
- **Response Times**: Track intent parsing, search, assembly times
- **Success Rates**: Monitor LLM parsing success, outfit generation rates  
- **User Satisfaction**: Track click-through rates on recommendations

## Configuration

### Environment Variables
```bash
# LLM Configuration
LLM_PROVIDER=ollama|openrouter
OLLAMA_HOST=http://localhost:11434
OLLAMA_TEXT_MODEL=qwen3:4b-instruct
OPENROUTER_API_KEY=sk-or-v1-...

# Database
MYSQL_URL=mysql://user:pass@host:3306/db

# Performance
LLM_TIMEOUT=10
SEARCH_LIMIT=15
OUTFIT_LIMIT=5
```

### Model Selection
- **Development**: Ollama with qwen3:4b-instruct (fast, local)
- **Production**: OpenRouter with qwen/qwen-2.5-7b-instruct:free (reliable)
- **High-volume**: OpenRouter paid models for better quality

## Troubleshooting

### Common Issues

#### "No outfits found"
- **Cause**: Keywords too specific, no matching products
- **Solution**: Check product database, verify keyword generation
- **Debug**: Log generated keywords, check product search results

#### "LLM timeout"  
- **Cause**: Model overloaded or network issues
- **Solution**: Increase timeout, check model availability
- **Debug**: Test LLM endpoint directly with curl

#### "Poor recommendations"
- **Cause**: Insufficient product data or poor keyword matching  
- **Solution**: Improve product attributes, tune keyword generation
- **Debug**: Review generated keywords vs product attributes

### Debug Commands
```bash
# Test LLM providers
poetry run python scripts/test_llm_providers.py

# Test keyword generation
poetry run python -c "
from lookbook_mpc.services.smart_recommender import SmartRecommender
import asyncio
sr = SmartRecommender(None)
result = asyncio.run(sr._generate_keywords_from_message('I go to dance'))
print(result)
"

# Test database search  
poetry run python scripts/test_product_search.py
```

## Future Enhancements

### V2 Features
- **User Preference Learning**: Track user choices to improve recommendations
- **Seasonal Adjustments**: Factor in weather and season
- **Trend Integration**: Include current fashion trends in scoring
- **Multi-language Support**: Support for non-English requests

### Advanced AI
- **Vision-based Recommendations**: Use product images for better matching
- **Style Transfer**: Recommend items similar to user's uploaded photos
- **Collaborative Filtering**: "Users like you also bought..." recommendations

### Performance Improvements
- **Vector Search**: Use embeddings for semantic product matching
- **Real-time Updates**: Stream recommendations as they're generated
- **Edge Caching**: Cache popular recommendations at CDN level