# Environment Setup Guide - Lookbook MPC

This guide helps you set up the correct environment variables for the Lookbook-MPC Fashion Recommendation Service.

## 📋 Required Environment Variables

Create a `.env` file in the project root with these variables:

### Core Configuration
```bash
# LLM Configuration - Ollama Models
OLLAMA_HOST=http://localhost:11434
OLLAMA_VISION_MODEL=qwen2.5vl:7b
OLLAMA_TEXT_MODEL=qwen3:4b
OLLAMA_TEXT_MODEL_FAST=llama3.2:1b-instruct-q4_K_M

# CDN Configuration - COS Thailand CloudFront
S3_BASE_URL=https://d29c1z66frfv6c.cloudfront.net/pub/media/catalog/product/large/

# Database Configuration
MYSQL_APP_URL=mysql+pymysql://magento:Magento@COS(*)@127.0.0.1:3306/lookbookMPC

# API Configuration (Optional)
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=1
LOG_LEVEL=info
```

## 🚀 Quick Setup

1. **Copy the template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit the `.env` file** with the values above

3. **Start the server:**
   ```bash
   ./start_server.sh
   ```

## 🔧 Configuration Details

### LLM Models
- **`OLLAMA_TEXT_MODEL`**: Primary model for intent parsing and responses (qwen3:4b)
- **`OLLAMA_TEXT_MODEL_FAST`**: Faster model for testing and development (llama3.2:1b)
- **`OLLAMA_VISION_MODEL`**: Vision model for product image analysis (qwen2.5vl:7b)

### CDN Configuration
- **`S3_BASE_URL`**: **CRITICAL** - Must use the exact CloudFront URL for COS Thailand:
  ```
  https://d29c1z66frfv6c.cloudfront.net/pub/media/catalog/product/large/
  ```
  This ensures product images display correctly in chat recommendations.

### Database
- **`MYSQL_APP_URL`**: Connection string for the Magento/COS product catalog
- Contains product information, pricing, and vision attributes

## 🧪 Testing Configuration

For development and testing, you can use the fast model:

```bash
# In your application code or configuration
text_model = settings.ollama_text_model_fast  # Use for testing
text_model = settings.ollama_text_model       # Use for production
```

## 🔍 Verification

After setup, verify your configuration:

1. **Check service health:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Test image URLs:**
   - Chat query: "I want to go dancing"
   - Check that `image_url` in response starts with the CloudFront URL

3. **Verify LLM connection:**
   ```bash
   curl http://localhost:11434/api/tags
   ```

## 🚨 Common Issues

### Image URLs showing "example.com"
- **Problem**: S3_BASE_URL not set correctly
- **Solution**: Ensure exact CloudFront URL is used (with trailing slash)

### No outfit recommendations
- **Problem**: Database connection or LLM issues
- **Solution**: Check `/ready` endpoint for dependency status

### Slow responses
- **Problem**: Using heavy LLM model for testing
- **Solution**: Switch to `OLLAMA_TEXT_MODEL_FAST` for development

## 📍 Service URLs

After setup, these URLs will be available:

- **Main Service**: http://localhost:8000/
- **Demo Interface**: http://localhost:8000/demo  
- **Test Interface**: http://localhost:8000/test
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🛠️ Development Mode

For faster development iteration:

```bash
# Set fast model as primary for testing
export OLLAMA_TEXT_MODEL=$OLLAMA_TEXT_MODEL_FAST

# Start with hot reload
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

**Note**: The S3_BASE_URL is critical for proper product image display. Always use the exact CloudFront URL provided above.