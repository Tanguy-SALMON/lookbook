# Recommendation Engine Strategy

## 🎯 Executive Summary

Based on database investigation, we have **100 products with complete vision attributes** covering ฿490-฿10,990 price range. While product categorization needs refinement, we have sufficient data to build a **fuzzy matching recommendation engine** that can suggest outfit combinations.

**Key Finding**: The current dataset has misclassified categories but contains viable clothing items for outfit recommendations.

## 📊 Database Analysis Results

### Available Product Data
- **Total Products**: 100 (100% vision analysis coverage)
- **Price Range**: ฿490 - ฿10,990 (avg ฿3,319)
- **Categories**: 21 different categories (but many misclassified)
- **Colors**: 5 main colors (white:28, beige:22, black:20, grey:16, navy:14)
- **Occasions**: 23 different occasions (picnic:8, running:8, sport:7, etc.)

### Clothing Items Available for Outfits
```
Actual Wearable Items: ~13 products
- Dresses: 6 items (some misclassified as other categories)  
- Tops/Blouses: 5-7 items (scattered across categories)
- Bottoms: 2-4 actual bottoms (some tops misclassified as bottoms)
- Outerwear: 6 items
```

### Data Quality Issues
1. **Category Misclassification**: 
   - "LIGHTWEIGHT V-NECK BLOUSE" labeled as "bottom"
   - "CROPPED WOOL ZIP-UP CARDIGAN" correctly labeled as "top" 
   - "OPEN-BACK MINI PINAFORE DRESS" labeled as "top"

2. **Missing Core Categories**: Limited actual tops and bottoms for combinations

## 🚀 Recommendation Engine Approach

### 1. **MCP Server Decision: YES, Still Valuable**

**Why MCP Makes Sense:**
- **Extensibility**: Can be used by multiple AI agents/systems
- **Protocol Standard**: Future-proof integration with AI tools
- **External Integration**: Other systems can access recommendations
- **LLM Integration**: Perfect for feeding recommendations back to chat LLM

**MCP Server Capabilities:**
```
Tools to Expose:
- recommend_outfit(occasion, style, budget, color_preference)
- get_product_details(sku)
- search_products(filters)
- get_outfit_combinations(top_sku, bottom_sku)
```

### 2. **Fuzzy Matching Strategy**

Given the data quality issues, implement **multi-layer fuzzy matching**:

#### Layer 1: Intent Mapping
```sql
-- Map LLM intent to database searches
"I go to dance" → occasion LIKE '%party%' OR occasion LIKE '%festival%'
"business meeting" → occasion LIKE '%business%' OR occasion LIKE '%interview%'
"casual weekend" → occasion LIKE '%casual%' OR occasion LIKE '%picnic%'
```

#### Layer 2: Multi-Attribute Scoring
```python
def calculate_match_score(product, intent):
    score = 0
    # Occasion match (highest weight)
    if product.occasion in intent.occasions:
        score += 40
    
    # Color preference match
    if product.color in intent.colors:
        score += 25
    
    # Style compatibility
    if product.style in intent.styles:
        score += 20
    
    # Price range match
    if intent.budget_min <= product.price <= intent.budget_max:
        score += 15
    
    return score
```

#### Layer 3: Category Correction
```python
def fix_category_classification(product):
    title_lower = product.title.lower()
    
    # Fix obvious misclassifications
    if any(word in title_lower for word in ['blouse', 'shirt', 'top', 'cardigan']):
        return 'top'
    elif any(word in title_lower for word in ['shorts', 'pants', 'skirt']):
        return 'bottom' 
    elif 'dress' in title_lower:
        return 'dress'
    
    return product.category  # Keep original if uncertain
```

### 3. **Recommendation Algorithm**

#### Core Workflow:
```python
async def recommend_outfit(intent: Intent) -> OutfitRecommendation:
    # 1. Parse and clean intent
    occasions = map_intent_to_occasions(intent)
    
    # 2. Get candidate products with fuzzy matching
    candidates = await search_products_fuzzy(
        occasions=occasions,
        colors=intent.colors,
        budget_max=intent.budget,
        min_score=60  # Minimum match threshold
    )
    
    # 3. Fix category classifications
    corrected_products = [fix_category(p) for p in candidates]
    
    # 4. Group by corrected categories
    tops = filter_by_category(corrected_products, 'top')
    bottoms = filter_by_category(corrected_products, 'bottom') 
    dresses = filter_by_category(corrected_products, 'dress')
    
    # 5. Create outfit combinations
    outfits = []
    
    # Strategy A: Dress-based outfits (complete outfit)
    for dress in dresses[:3]:
        outfits.append(create_outfit([dress], "Complete Look"))
    
    # Strategy B: Top + Bottom combinations
    for top in tops[:2]:
        for bottom in bottoms[:2]:
            if color_compatible(top, bottom):
                outfits.append(create_outfit([top, bottom], "Coordinated Set"))
    
    return OutfitRecommendation(outfits=outfits[:5])  # Limit to top 5
```

## 🛠️ Implementation Plan

### Phase 1: Core Recommendation Engine (Week 1)
1. **Create Fuzzy Matcher Service**
   ```python
   # lookbook_mpc/services/fuzzy_matcher.py
   class FuzzyProductMatcher:
       async def search_by_intent(intent) -> List[Product]
       def calculate_relevance_score(product, intent) -> float
       def fix_category_classification(product) -> Product
   ```

2. **Enhanced Outfit Recommender**
   ```python  
   # lookbook_mpc/services/recommender.py (enhance existing)
   class OutfitRecommender:
       async def recommend_by_intent(intent) -> List[Outfit]
       def create_outfit_combinations(products) -> List[Outfit]
       def validate_color_compatibility(items) -> bool
   ```

### Phase 2: MCP Server Integration (Week 2)
1. **MCP Tools Implementation**
   ```python
   # lookbook_mpc/mcp/recommendation_tools.py
   @mcp_tool
   async def recommend_outfit(occasion, budget, style):
       # Return outfit recommendations with product links
       
   @mcp_tool  
   async def get_product_details(sku):
       # Return full product information
   ```

2. **MCP Server Setup**
   ```python
   # lookbook_mpc/mcp/server.py
   class RecommendationMCPServer:
       # Expose recommendation tools via MCP protocol
   ```

### Phase 3: LLM Integration (Week 2-3)
1. **Enhanced Chat Responses**
   ```python
   # Update ChatTurn to include actual product recommendations
   # Use MCP tools internally to get real suggestions
   # Return product links and images in chat responses
   ```

2. **Product Link Generation**
   ```python
   def generate_product_links(products):
       # Create formatted links with images and prices
       # Return HTML/markdown for chat display
   ```

## 🎯 Expected Outcomes

### Minimum Viable Product (MVP)
- **Input**: "I go to dance" 
- **Output**: 2-3 outfit suggestions with:
  - Product images and links
  - Prices in Thai Baht
  - Style descriptions
  - "Why this works" explanations

### Example Response:
```json
{
  "outfits": [
    {
      "title": "Party Ready Look", 
      "items": [
        {
          "sku": "1099061001003",
          "title": "BELTED DENIM MIDI SHIRT DRESS",
          "price": 3190,
          "image_url": "https://cdn.../image.jpg",
          "role": "main_piece"
        }
      ],
      "total_price": 3190,
      "why_it_works": "Perfect for dancing with comfortable denim fabric and stylish belt detail"
    }
  ]
}
```

## 🔧 Technical Architecture

### Database Strategy
- **Keep Current Schema**: No changes to product_vision_attributes
- **Runtime Classification**: Fix categories in application logic
- **Caching**: Cache corrected classifications for performance

### API Design
```python
# New endpoint in chat router
@router.post("/v1/chat/recommend")
async def get_recommendations(intent: IntentRequest) -> RecommendationResponse:
    # Direct recommendation endpoint for testing
    
# Enhanced chat endpoint  
@router.post("/v1/chat")
async def chat_turn(request: ChatRequest) -> ChatResponse:
    # Now includes actual product recommendations in responses
```

### MCP Integration
```python
# Standalone MCP server process
python -m lookbook_mpc.mcp.server --port 8001

# Tools available to any MCP-compatible system:
# - recommend_outfit
# - search_products  
# - get_product_details
```

## 🎉 Success Metrics

### Technical Metrics
- **Response Time**: < 2 seconds for outfit recommendations
- **Match Quality**: > 70% relevance score for recommended items
- **Coverage**: Recommend outfits for 80% of user intents

### Business Metrics  
- **User Satisfaction**: Natural, helpful recommendations
- **Conversion Potential**: Include product links and prices
- **Scalability**: Ready for larger product catalogs

## 🚀 Next Steps

1. **Week 1**: Build fuzzy matcher and enhanced recommender
2. **Week 1**: Test with current chat system 
3. **Week 2**: Implement MCP server with recommendation tools
4. **Week 2**: Integrate real recommendations into chat responses
5. **Week 3**: Polish and optimize performance

**Goal**: Transform from "I'll help you find outfits" to "Here are 3 specific outfits with links and prices!"

---

**Status**: 📋 **READY TO IMPLEMENT**  
**Confidence**: ✅ **HIGH** - Sufficient data and clear path forward
**Timeline**: 🕒 **2-3 weeks** to full implementation