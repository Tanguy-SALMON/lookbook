# Environment Setup Guide

This guide will help you set up the environment variables required to run the Lookbook-MPC Chat Server.

## Quick Setup

1. **Copy the template file:**
   ```bash
   ./setup-env.sh
   ```
   
   Or manually:
   ```bash
   cp .env.template .env
   ```

2. **Edit the `.env` file** with your actual values:
   ```bash
   nano .env
   # or
   code .env
   ```

3. **Start the server:**
   ```bash
   ./start.sh
   ```

## Environment Variables

### Core Configuration

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `LLM_PROVIDER` | Choose between `ollama` or `openrouter` | ✅ | - |
| `S3_BASE_URL` | Your CDN base URL for product images | ✅ | - |
| `LOG_LEVEL` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR` | ✅ | - |
| `LOG_FORMAT` | Log format: `simple`, `detailed`, `json` | ✅ | - |

### Ollama Configuration (if `LLM_PROVIDER=ollama`)

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `OLLAMA_HOST` | Ollama server URL | ✅ | `http://localhost:11434` |
| `OLLAMA_TEXT_MODEL` | Primary text model | ✅ | `llama3.2:latest` |
| `OLLAMA_TEXT_MODEL_FAST` | Fast model for testing | ✅ | `llama3.2:1b` |
| `OLLAMA_VISION_MODEL` | Vision model | ✅ | `llava:latest` |

### OpenRouter Configuration (if `LLM_PROVIDER=openrouter`)

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `OPENROUTER_MODEL` | Model to use | ✅ | `openai/gpt-4o-mini` |
| `OPENROUTER_API_KEY` | Your API key | ✅ | `sk-or-v1-...` |

## Provider-Specific Setup

### Using Ollama (Local AI)

1. **Install Ollama:**
   ```bash
   # macOS
   brew install ollama
   
   # Linux
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

2. **Start Ollama service:**
   ```bash
   ollama serve
   ```

3. **Pull required models:**
   ```bash
   ollama pull llama3.2:latest
   ollama pull llama3.2:1b
   ollama pull llava:latest
   ```

4. **Configure `.env`:**
   ```env
   LLM_PROVIDER=ollama
   OLLAMA_HOST=http://localhost:11434
   OLLAMA_TEXT_MODEL=llama3.2:latest
   OLLAMA_TEXT_MODEL_FAST=llama3.2:1b
   OLLAMA_VISION_MODEL=llava:latest
   ```

### Using OpenRouter (Cloud AI)

1. **Get API Key:**
   - Visit [OpenRouter Keys](https://openrouter.ai/keys)
   - Create a new API key
   - Copy the key (starts with `sk-or-v1-`)

2. **Configure `.env`:**
   ```env
   LLM_PROVIDER=openrouter
   OPENROUTER_MODEL=openai/gpt-4o-mini
   OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
   ```

3. **Available Models:**
   - `openai/gpt-4o-mini` (recommended, cost-effective)
   - `openai/gpt-4o`
   - `anthropic/claude-3-sonnet`
   - `qwen/qwen-2.5-7b-instruct:free` (free tier)
   - See full list at [OpenRouter Models](https://openrouter.ai/models)

## Example Configuration Files

### For Local Development (Ollama)
```env
# .env
LLM_PROVIDER=ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_TEXT_MODEL=llama3.2:latest
OLLAMA_TEXT_MODEL_FAST=llama3.2:1b
OLLAMA_VISION_MODEL=llava:latest
S3_BASE_URL=https://your-cdn-url.cloudfront.net
LOG_LEVEL=DEBUG
LOG_FORMAT=detailed
```

### For Production (OpenRouter)
```env
# .env
LLM_PROVIDER=openrouter
OPENROUTER_MODEL=openai/gpt-4o-mini
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
OLLAMA_VISION_MODEL=qwen2.5vl:7b
S3_BASE_URL=https://d29c1z66frfv6c.cloudfront.net/pub/media/catalog/product/large/
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## Troubleshooting

### Common Issues

1. **"Missing required environment variables"**
   - Check that all required variables are set in `.env`
   - Make sure there are no typos in variable names
   - Verify the `.env` file exists in the project root

2. **"Port 8000 is already in use"**
   ```bash
   # Find the process using port 8000
   lsof -i :8000
   
   # Kill the process
   pkill -f 'python.*main.py'
   ```

3. **Ollama connection issues**
   - Make sure Ollama is running: `ollama serve`
   - Check if models are installed: `ollama list`
   - Verify the `OLLAMA_HOST` URL is correct

4. **OpenRouter API issues**
   - Verify your API key is correct
   - Check your OpenRouter account balance
   - Ensure the model name is correct

### Environment Validation

The start script automatically validates your environment:

```bash
./start.sh
```

If validation fails, you'll see specific error messages about missing variables.

### Manual Validation

You can check if your environment is properly loaded:

```bash
# Check if .env is being read
source .env && echo "LLM_PROVIDER: $LLM_PROVIDER"

# Test OpenRouter connection (if using)
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
     https://openrouter.ai/api/v1/models
```

## Security Best Practices

1. **Never commit `.env` to git**
   - ✅ `.env` is already in `.gitignore`
   - ❌ Don't rename or move it to a tracked location

2. **Keep API keys secure**
   - Don't share them in chat/email
   - Don't log them in plain text
   - Rotate them periodically

3. **Use environment-specific configs**
   - Different `.env` for development/staging/production
   - Use secure secret management in production

4. **Backup your configuration**
   - Keep a secure backup of your `.env` file
   - Document any custom configurations

## Advanced Configuration

### Custom Port
```env
# Add to .env if you want to change the default port
PORT=3000
```

### Database Configuration
```env
# If your app uses a database
DATABASE_URL=postgresql://user:password@localhost:5432/lookbook
```

### Redis Configuration
```env
# If using Redis for caching
REDIS_URL=redis://localhost:6379
```

### JWT Configuration
```env
# For authentication features
JWT_SECRET=your-super-secret-jwt-key-here
```

## Getting Help

If you're still having issues:

1. Check the server logs for detailed error messages
2. Verify your `.env` file format (no spaces around `=`)
3. Make sure you're in the correct directory when running scripts
4. Check that all required services (Ollama, etc.) are running

For more help, check the main README.md or create an issue in the project repository.