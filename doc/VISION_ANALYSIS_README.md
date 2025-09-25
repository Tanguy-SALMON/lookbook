# Vision Analysis System

This document describes the vision analysis system for the Lookbook-MPC project, which uses Ollama's `qwen2.5vl:latest` model to analyze product images and extract fashion attributes.

## Overview

The vision analysis system automatically analyzes product images to extract:

- **Color**: Primary color of the product (e.g., "black", "navy", "white")
- **Category**: Product type (e.g., "top", "bottom", "dress", "outerwear")
- **Material**: Fabric composition (e.g., "cotton", "denim", "silk", "polyester")
- **Pattern**: Visual pattern (e.g., "plain", "striped", "floral", "print")
- **Season**: Appropriate season (e.g., "spring", "summer", "autumn", "winter")
- **Occasion**: Suitable occasion (e.g., "casual", "formal", "business", "party")
- **Fit**: Garment fit (e.g., "slim", "regular", "loose", "relaxed")
- **Style**: Fashion style descriptor
- **Plus Size**: Whether the item is plus-size
- **Description**: Detailed product description

## Prerequisites

### 1. Ollama Setup

Make sure Ollama is installed and running:

```bash
# Install Ollama (if not already installed)
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# Pull the vision model (this may take several minutes)
ollama pull qwen2.5vl:latest
```

### 2. Database Configuration

Set up your MySQL database connection:

```bash
export MYSQL_APP_URL="mysql+aiomysql://username:password@host:port/database_name"
```

### 3. Dependencies

Ensure all Python dependencies are installed:

```bash
cd lookbookMPC
pip install -r requirements.txt
```

## Quick Start

### 1. Test the System

Run the test script to verify everything is working:

```bash
python scripts/test_vision_analysis.py
```

This will check:
- Ollama connection and model availability
- Database connectivity
- Product data availability
- Vision analysis functionality

### 2. Run Vision Analysis

Analyze products with missing vision attributes:

```bash
# Analyze 50 products in batches of 5
python scripts/analyze_products_vision.py --limit 50 --batch-size 5

# Analyze a specific product by SKU
python scripts/analyze_products_vision.py --sku "PRODUCT-SKU-HERE"

# Analyze all products (not just missing attributes)
python scripts/analyze_products_vision.py --all --limit 100

# Run automatically without prompts
python scripts/analyze_products_vision.py --auto --limit 20
```

### 3. Monitor Progress

The script provides real-time progress updates:

```
🚀 Starting vision analysis...
   Model: qwen2.5vl:latest
   Batch size: 5
   Products: 50

Processing batch 1/10: 5 products
Progress: 10.0% - 0.33 products/sec
Waiting 1.0s before next batch...
```

## Admin Panel Integration

### API Endpoints

The system provides REST API endpoints for admin panel integration:

#### Get Analysis Statistics
```http
GET /admin/vision-analysis/stats
```
Returns overview of analysis coverage and statistics.

#### Get Products Needing Analysis
```http
GET /admin/vision-analysis/products/needing-analysis?limit=50
```
Returns products that need vision analysis.

#### Start Batch Analysis
```http
POST /admin/vision-analysis/start-batch
Content-Type: application/json

{
  "limit": 100,
  "batch_size": 5
}
```
Starts a background analysis task.

#### Monitor Progress
```http
GET /admin/vision-analysis/progress/{task_id}
```
Gets real-time progress of a running analysis task.

#### Cancel Analysis
```http
POST /admin/vision-analysis/cancel/{task_id}
```
Cancels a running analysis task.

#### Get Recent Analyses
```http
GET /admin/vision-analysis/recent?limit=20
```
Returns recently analyzed products.

### Frontend Integration

To add a vision analysis button to your admin panel:

1. **Create Analysis Button**:
```javascript
const startAnalysis = async () => {
  const response = await fetch('/admin/vision-analysis/start-batch', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ limit: 100, batch_size: 5 })
  });
  
  const result = await response.json();
  if (result.success) {
    const taskId = result.task_id;
    // Start monitoring progress
    monitorProgress(taskId);
  }
};
```

2. **Monitor Progress**:
```javascript
const monitorProgress = async (taskId) => {
  const interval = setInterval(async () => {
    const response = await fetch(`/admin/vision-analysis/progress/${taskId}`);
    const progress = await response.json();
    
    if (progress.success) {
      const { processed, total_products, status } = progress.progress;
      const percentage = (processed / total_products) * 100;
      
      updateProgressBar(percentage);
      
      if (status === 'completed' || status === 'failed') {
        clearInterval(interval);
        handleCompletion(progress);
      }
    }
  }, 2000); // Check every 2 seconds
};
```

## Configuration

### Model Selection

The system uses `qwen2.5vl:latest` by default. To use a different model:

```python
vision_analyzer = VisionAnalyzer(
    model="llava:latest",  # Alternative model
    save_processed=False
)
```

### Batch Processing

Adjust batch processing parameters:

```python
# In scripts/analyze_products_vision.py
await analyzer.batch_analyze_products(
    products,
    batch_size=3,              # Smaller batches for stability
    delay_between_batches=2.0  # Longer delays to reduce load
)
```

### Analysis Criteria

Products are considered needing analysis if they have missing:
- Color
- Material  
- Pattern
- Season
- Occasion

You can modify the criteria in `VisionAnalysisService.get_products_needing_analysis()`.

## Performance Considerations

### Processing Speed

- **Average**: ~3 seconds per product
- **Batch size**: 3-5 products recommended
- **Concurrent batches**: Not recommended (can overload Ollama)

### Resource Usage

- **RAM**: Ollama with qwen2.5vl requires ~8GB
- **Disk**: Model file is ~7GB
- **CPU**: Higher CPU improves processing speed

### Optimization Tips

1. **Use smaller batch sizes** (3-5) for stability
2. **Add delays between batches** to prevent overload
3. **Monitor system resources** during large batch processing
4. **Run during off-peak hours** for production systems

## Troubleshooting

### Common Issues

#### "Connection refused" error
- **Cause**: Ollama not running
- **Solution**: Run `ollama serve`

#### "Model not found" error
- **Cause**: Vision model not installed
- **Solution**: Run `ollama pull qwen2.5vl:latest`

#### "Database connection failed"
- **Cause**: Invalid database URL or credentials
- **Solution**: Check `MYSQL_APP_URL` environment variable

#### "No products found"
- **Cause**: No products in database or all already analyzed
- **Solution**: Import products first or use `--all` flag

#### Analysis taking too long
- **Cause**: Large images or system overload
- **Solution**: Reduce batch size, add delays, check system resources

### Debugging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check Ollama logs:
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Check model status
ollama list
```

Monitor system resources:
```bash
# Check RAM usage
free -h

# Check GPU usage (if applicable)
nvidia-smi

# Check disk space
df -h
```

## File Structure

```
lookbookMPC/
├── scripts/
│   ├── analyze_products_vision.py      # Main analysis script
│   └── test_vision_analysis.py         # Test script
├── lookbook_mpc/
│   ├── services/
│   │   └── vision_analysis_service.py  # Core service
│   ├── api/routers/
│   │   └── vision_analysis.py          # API endpoints
│   └── domain/entities.py              # Data models
├── image/
│   └── vision_analyzer.py              # Ollama integration
└── VISION_ANALYSIS_README.md           # This file
```

## Next Steps

1. **Test the system**: Run the test script
2. **Start with small batches**: Analyze 10-20 products first
3. **Monitor results**: Check database for updated attributes
4. **Scale up gradually**: Increase batch sizes as system proves stable
5. **Add to admin panel**: Integrate API endpoints into your UI
6. **Set up monitoring**: Track analysis coverage and performance

## Support

For issues or questions:

1. Check this README for common solutions
2. Run the test script to identify problems
3. Review log files for error details
4. Check Ollama and database connectivity
5. Verify model installation and system resources