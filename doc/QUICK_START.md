# 🚀 Quick Start Guide - Lookbook MPC

Get the Lookbook-MPC Fashion Recommendation Service running in minutes!

## 🔄 Server Restart Required

**Important**: The server must be restarted to apply the correct S3_BASE_URL configuration for proper image display.

### 1. Stop Current Server
```bash
# If running in terminal, press Ctrl+C
# Or find and kill the process
ps aux | grep "python main.py" | grep -v grep
kill <PID>
```

### 2. Start with Correct Configuration
```bash
# Use the provided start script with updated environment
./start_server.sh
```

## 📍 Access Points

Once the server is running, visit these URLs:

### 🏠 Main Navigation
- **Landing Page**: http://localhost:8000/
  - Beautiful interface with all navigation links
  - System status and feature overview
  - No more copy/pasting URLs!

### 💬 Chat Interfaces  
- **Full Demo**: http://localhost:8000/demo
  - Complete chat interface with product recommendations
  - Professional UI matching COS Thailand design

- **Simple Test**: http://localhost:8000/test  
  - Minimal interface for quick API testing
  - Pre-configured test buttons for working queries

### 📚 Documentation
- **Docs Hub**: http://localhost:8000/docs-index
  - File listings and quick tests
  - System information and API overview

- **API Docs**: http://localhost:8000/docs
  - Interactive Swagger UI for API testing

## 🧪 Quick Test

Try these working queries to see recommendations:

1. **"I want to go dancing tonight"** ✅
   - Returns 2 outfit recommendations
   - Real COS Thailand products with pricing

2. **"I need party outfits"** ✅  
   - Multiple coordinated outfit suggestions
   - Product images from CloudFront CDN

3. **"Show me something elegant"** ✅
   - Styled recommendations with explanations

## 🔍 Verify Setup

### Check Image URLs
After restart, test that images load correctly:
```bash
curl -s -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "message": "I want to go dancing"}' | \
  jq '.outfits[0].items[0].image_url'
```

**Expected**: URLs starting with `https://d29c1z66frfv6c.cloudfront.net`

### Check System Health
```bash
curl http://localhost:8000/health
```

**Expected**: `{"status": "healthy", ...}`

## 🎯 What's New

### ✅ Completed Features
- **AI Recommendations Working**: Real products with natural language responses
- **Beautiful Navigation**: Professional landing page with easy access
- **Multiple Interfaces**: Demo, test, and documentation pages  
- **Real Product Data**: COS Thailand catalog with Thai Baht pricing
- **CloudFront Images**: Proper CDN URLs for fast image loading
- **Connection Status**: Real-time backend monitoring

### 🚀 Ready for Demo
- Chat interfaces are production-ready
- AI responses are natural and contextual
- Product recommendations include real COS items
- Images load from official CDN
- Professional UI suitable for client presentations

## 📱 Mobile Ready

All interfaces are fully responsive:
- **Mobile**: Optimized touch interface
- **Tablet**: Balanced layout with sidebar
- **Desktop**: Full-featured experience
- **4K Displays**: Scales beautifully

## 🛠️ Development Mode

For faster testing during development:
```bash
# Use the fast LLM model
export OLLAMA_TEXT_MODEL="llama3.2:1b-instruct-q4_K_M"

# Start with hot reload
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 🚨 Troubleshooting

### Images Show Placeholder
- **Issue**: S3_BASE_URL not updated
- **Fix**: Restart server with `./start_server.sh`

### No Recommendations
- **Issue**: Database or LLM connection
- **Fix**: Check `/ready` endpoint for status

### Slow Responses  
- **Issue**: Using heavy LLM model
- **Fix**: Switch to `OLLAMA_TEXT_MODEL_FAST`

## 🎉 Success Indicators

You'll know everything is working when:
- ✅ Landing page shows beautiful navigation
- ✅ Chat returns outfit recommendations  
- ✅ Product images load from CloudFront
- ✅ Pricing displays in Thai Baht
- ✅ Connection status shows "Connected"

---

**Next Steps**: Visit http://localhost:8000/ and explore the interfaces!

**Demo Ready**: The system is now fully operational for client demonstrations and development.