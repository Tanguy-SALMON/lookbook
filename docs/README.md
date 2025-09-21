# Lookbook-MPC Documentation

This directory contains documentation and demo interfaces for the Lookbook-MPC Fashion Recommendation Service.

## 📂 Files Overview

### Chat Interfaces

- **`demo.html`** - Main chat interface with full UI
  - Complete responsive dashboard
  - Modern Tailwind CSS design
  - Product recommendation cards with images and prices
  - Customer analytics sidebar
  - Real-time chat with AI fashion assistant

- **`test_chat_frontend.html`** - Simple test interface for API testing
  - Minimal UI focused on testing functionality
  - Quick test buttons for known working queries
  - Debug information display
  - Real-time API status checking

- **`index.html`** - Documentation hub page
  - Navigation to all available interfaces
  - Quick API testing functionality
  - System information and status

### Documentation

- **`README.md`** - This file, overview of documentation structure

## 🚀 Quick Start

### Access Pages

When the server is running (`http://localhost:8000`):

- **Main Service**: `http://localhost:8000/` - Landing page with navigation
- **Demo Interface**: `http://localhost:8000/demo` - Full chat interface
- **Test Interface**: `http://localhost:8000/test` - Simple testing interface  
- **Docs Hub**: `http://localhost:8000/docs-index` - Documentation index
- **API Docs**: `http://localhost:8000/docs` - Swagger UI

### Working Test Queries

The recommendation system works best with these types of queries:

✅ **Working Examples:**
- "I want to go dancing tonight"
- "I need party outfits" 
- "Show me something for parties"
- "I want elegant clothes"

❓ **Limited Results:**
- "I need work clothes" (few business items in database)
- "I want casual outfits" (depends on available inventory)

## 🎯 Features Demonstrated

### Chat System
- Natural language processing with Ollama LLM
- Intent parsing and context understanding
- Session management and conversation flow
- Real-time connection status monitoring

### Product Recommendations
- AI-powered outfit generation
- Real COS Thailand products with pricing (Thai Baht)
- Product images from CloudFront CDN
- Coordinated outfit combinations
- Style explanations and rationales

### Frontend Integration
- Responsive design (mobile/tablet/desktop)
- Product card displays with hover effects
- Real-time typing indicators
- Error handling and connection status
- Debug information for developers

## 🔧 Technical Details

### API Endpoints Used
- `GET /health` - Service health check
- `GET /v1/chat/suggestions` - Get suggested chat prompts
- `POST /v1/chat` - Main chat endpoint with recommendations
- `GET /v1/chat/sessions` - List chat sessions

### Response Format
```json
{
  "session_id": "string",
  "replies": [
    {
      "type": "recommendations",
      "message": "Natural LLM response",
      "outfits": 2
    }
  ],
  "outfits": [
    {
      "title": "Outfit Name",
      "items": [
        {
          "sku": "product_sku",
          "title": "Product Name",
          "price": 790.0,
          "image_url": "https://cdn.../image.jpg",
          "color": "black",
          "category": "activewear"
        }
      ],
      "total_price": 3380.0,
      "rationale": "Style explanation...",
      "score": 0.85
    }
  ]
}
```

### Architecture
```
Frontend (HTML/JS/Tailwind) 
    ↓ HTTP Requests
FastAPI Backend 
    ↓ LLM Calls
Ollama (Intent Parsing + Natural Responses)
    ↓ Database Queries  
MySQL (Products + Vision Attributes)
    ↓ Image URLs
CloudFront CDN
```

## 🛠️ Development Notes

### File Organization
- All demo files use relative API paths (`/v1/chat`) for backend communication
- Images are served from S3/CloudFront with proper CORS configuration
- Tailwind CSS is loaded from CDN for rapid development
- Minimal custom CSS, mostly utility-first approach

### Styling Approach
- **95% Tailwind utilities** - Modern utility-first CSS
- **5% custom CSS** - Only for complex animations and scrollbar styling
- **Responsive design** - Mobile-first with proper breakpoints
- **Consistent colors** - Professional gray scale with blue accents

### Testing Strategy
1. **Backend API Testing** - Direct curl commands to test endpoints
2. **Frontend Integration** - Live testing through demo interfaces  
3. **Cross-browser Testing** - Verify compatibility across browsers
4. **Mobile Responsive** - Test on various screen sizes

## 📱 Browser Compatibility

### Supported Browsers
- ✅ Chrome 90+ (full support)
- ✅ Firefox 88+ (full support) 
- ✅ Safari 14+ (full support)
- ✅ Edge 90+ (full support)

### Features Used
- CSS Grid and Flexbox (modern layout)
- Fetch API (HTTP requests)
- ES6+ JavaScript (modern syntax)
- CSS Custom Properties (theming)

## 🔮 Future Enhancements

### Planned Features
- **WebSocket Integration** - Real-time bidirectional communication
- **User Authentication** - Session management and user preferences
- **Shopping Cart** - Add recommended items to cart
- **Product Links** - Direct links to COS Thailand product pages
- **Multi-language** - Thai and English language support
- **Voice Input** - Speech-to-text for mobile users

### Technical Improvements
- **Offline Support** - Service worker for offline functionality
- **Performance** - Image lazy loading and caching
- **Analytics** - User interaction tracking and metrics
- **A/B Testing** - Interface variations for optimization

---

## 📞 Support

For technical issues or questions:
- Check the main service status at `/health`
- Review API documentation at `/docs`
- Test functionality using the demo interfaces
- Check console logs for debugging information

**Service Status**: The recommendation system is fully operational with real product data and AI-powered responses.