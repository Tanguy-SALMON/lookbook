# PROJECT KNOWLEDGE BASE
# Lookbook-MPC Fashion Recommendation System

## 🚀 PROJECT OVERVIEW

**Project Name:** Lookbook-MPC  
**Purpose:** Fashion lookbook recommendation microservice with AI vision analysis  
**Market:** Thailand fashion e-commerce  
**Currency:** Thai Baht (THB)  
**Architecture:** FastAPI + MySQL + Ollama AI + Next.js Dashboard  

## 🎯 CORE FUNCTIONALITY

The system transfers fashion products from a Magento source database to a recommendation engine that provides:
- AI-powered outfit recommendations
- Vision analysis of product images
- Natural language intent parsing
- Fashion-specific recommendation rules
- REST API and MCP (Model Context Protocol) integration

## 📊 DATABASE ARCHITECTURE

### **Source Database: cos-magento-4**
- **Type:** MySQL Magento e-commerce database
- **Connection:** `mysql+pymysql://magento:Magento@COS(*)@localhost:3306/cos-magento-4`
- **Key Tables:**
  - `catalog_product_entity` - Main products (6,629 configurable, 41,030 simple)
  - `catalog_product_entity_decimal` - Price data (attribute_id = 77)
  - `catalog_product_entity_varchar` - Text attributes (name = 73, url_key)
  - `catalog_product_entity_int` - Integer attributes (status = 97, color = 93)
  - `catalog_product_entity_text` - Text attributes (material = 148, swatch_image = 358)
  - `catalog_product_super_link` - Parent-child product relationships
  - `cataloginventory_stock_item` - Stock quantities

### **Destination Database: lookbookMPC**
- **Type:** MySQL application database
- **Connection:** `mysql+pymysql://magento:Magento@COS(*)@127.0.0.1:3306/lookbookMPC`
- **Schema:**
```sql
CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sku VARCHAR(100) NOT NULL UNIQUE,
    title VARCHAR(500) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    size_range JSON,
    image_key VARCHAR(255) NOT NULL,
    in_stock TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    season VARCHAR(50),
    url_key VARCHAR(255) UNIQUE,
    product_created_at TIMESTAMP,
    stock_qty INT DEFAULT 0,
    category VARCHAR(100),
    color VARCHAR(100),
    material VARCHAR(100),
    pattern VARCHAR(100),
    occasion VARCHAR(100)
);
```

## 💰 PRICING & CURRENCY

- **Currency:** Thai Baht (THB)
- **Price Range:** ฿490 - ฿10,990
- **Storage:** Direct THB values (no conversion needed)
- **Display:** Use ฿ symbol for Thai Baht
- **Note:** Prices in Magento are already in THB, not cents

## 🔧 ENVIRONMENT CONFIGURATION

### Required Environment Variables (.env):
```bash
MYSQL_SHOP_URL=mysql+pymysql://magento:Magento@COS(*)@localhost:3306/cos-magento-4
MYSQL_APP_URL=mysql+pymysql://magento:Magento@COS(*)@127.0.0.1:3306/lookbookMPC
S3_BASE_URL=https://your-cdn-domain.com/
OLLAMA_HOST=http://localhost:11434
OLLAMA_VISION_MODEL=qwen2.5vl
OLLAMA_TEXT_MODEL=qwen3:4b
```

### Key Configuration Details:
- **Password Special Characters:** "Magento@COS(*)" - handle carefully in URL parsing
- **Connection String Alias:** `MYSQL_APP_URL` maps to `lookbook_db_url` in settings
- **Database Names:** Exactly "cos-magento-4" and "lookbookMPC"

## 📁 CRITICAL FILES & SCRIPTS

### **Core Scripts:**
- `scripts/sync_100_products.py` - **MAIN IMPORT SCRIPT** - transfers products from Magento to app DB
- `scripts/verify_product_import.py` - Data verification and quality analysis
- `scripts/test_db_connections.py` - Database connection testing
- `scripts/init_db_mysql_tables.py` - Database initialization
- `scripts/cleanup_database_schema.py` - Schema optimization

### **Core Application Files:**
- `lookbook_mpc/config/settings.py` - Configuration management
- `lookbook_mpc/adapters/db_shop.py` - Magento database adapter
- `lookbook_mpc/adapters/db_lookbook.py` - Application database adapter
- `lookbook_mpc/domain/entities.py` - Domain models and validation
- `main.py` - FastAPI application entry point

## 🔍 MAGENTO DATA EXTRACTION

### **Critical SQL Query Structure:**
```sql
SELECT DISTINCT
    p.sku,
    eav.value as gc_swatchimage,
    COALESCE(
        price.value,
        (SELECT MIN(child_price.value)
         FROM catalog_product_super_link super_link
         JOIN catalog_product_entity child ON super_link.product_id = child.entity_id
         JOIN catalog_product_entity_decimal child_price ON child.entity_id = child_price.entity_id
         WHERE super_link.parent_id = p.entity_id
         AND child_price.attribute_id = 77
         AND child_price.store_id = 0
         AND child_price.value > 0)
    ) as price,
    name.value as product_name,
    url.value as url_key,
    status.value as status,
    COALESCE(csi.qty, 0) as stock_qty,
    season.value as season,
    color_option.value as color,
    material.value as material
FROM catalog_product_entity p
JOIN catalog_product_entity_text eav ON p.entity_id = eav.entity_id AND eav.store_id = 0
LEFT JOIN catalog_product_entity_decimal price ON p.entity_id = price.entity_id AND price.attribute_id = 77 AND price.store_id = 0
-- Additional joins for attributes...
WHERE eav.attribute_id = 358
AND p.type_id IN ('configurable', 'simple')
AND status.value = 1
```

### **Key Insights:**
- **Attribute IDs:** price=77, name=73, status=97, color=93, material=148, swatch_image=358
- **Price Strategy:** Configurable products inherit prices from simple child products
- **Image Storage:** Swatch images stored in `catalog_product_entity_text` with attribute_id=358
- **Product Types:** Focus on 'configurable' and 'simple' products only
- **Status Filter:** Only active products (status=1)

## 🧪 TESTING & VALIDATION

### **Test Status:** ✅ 117 tests passing
- **Fixed Issues:**
  - VisionAttributes missing description field
  - Intent validation for empty strings and negative budgets
  - Session ID generation (UUID format)
  - Outfit creation with required title fields
  - Pydantic model validation conflicts

### **Key Test Commands:**
```bash
poetry run pytest tests/ -v                    # Run all tests
poetry run python scripts/sync_100_products.py # Main sync command
poetry run python scripts/verify_product_import.py # Data verification
```

## 🎨 PRODUCT ATTRIBUTES

### **Available Attributes:**
- **Colors:** Black, Blue, White, Beige, Grey, Brown, Green, Orange, Purple, Yellow
- **Categories:** Fashion (default), Top, Bottom, Dress, Accessories
- **Materials:** Cotton, Polyester, Wool, Silk, Denim, etc.
- **Seasons:** Spring, Summer, Autumn, Winter
- **Occasions:** Casual, Business, Formal, Party, Sport
- **Sizes:** S, M, L, XL (configurable), ONE_SIZE (simple)

### **Data Quality Standards:**
- **Complete Products:** Must have SKU, title, price > 0, image_key
- **Thai Market Focus:** Prices in THB, localized categories
- **SEO Optimization:** URL-friendly keys for all products

## 🚨 COMMON ISSUES & SOLUTIONS

### **Database Connection Issues:**
- **Problem:** "Access denied" or "cryptography package required"
- **Solution:** Install `cryptography` package, verify password encoding
- **Command:** `poetry add cryptography`

### **Price Data Missing:**
- **Problem:** Configurable products showing ฿0.00
- **Solution:** Use child product price lookup via `catalog_product_super_link`
- **Note:** Simple products have direct prices, configurables inherit from children

### **Session ID Format Errors:**
- **Problem:** "badly formed hexadecimal UUID string"
- **Solution:** Use `uuid.uuid4()` instead of timestamp strings
- **Import:** `import uuid`

### **Pydantic Validation Conflicts:**
- **Problem:** Built-in validators conflicting with custom ones
- **Solution:** Remove `ge=0` constraints, use custom validators only
- **Pattern:** Use `@validator("field_name")` decorators

## 🔄 DATA SYNC WORKFLOW

### **Standard Sync Process:**
1. **Connect** to both Magento and application databases
2. **Fetch** products using optimized SQL query (limit 100)
3. **Transform** data to application schema format
4. **Validate** required fields and data quality
5. **Upsert** to application database (update existing, insert new)
6. **Verify** import success and data completeness

### **Sync Performance:**
- **Speed:** ~0.08-0.09 seconds for 100 products
- **Efficiency:** Direct database transfer (no API calls)
- **Safety:** Upsert strategy prevents duplicates
- **Monitoring:** Comprehensive logging and error handling

## 🛡️ SECURITY & BEST PRACTICES

### **Database Security:**
- Use connection pooling for production
- Store credentials in environment variables
- Handle special characters in passwords properly
- Implement proper error handling and logging

### **Data Integrity:**
- Validate all input data before database insertion
- Use transactions for batch operations
- Implement proper foreign key constraints
- Regular backup and recovery procedures

## 🚀 DEPLOYMENT & SCALING

### **Development Setup:**
```bash
poetry install
poetry run python scripts/init_db_mysql_tables.py
poetry run python scripts/sync_100_products.py
poetry run python main.py
```

### **Production Considerations:**
- **Database:** MySQL with proper indexing
- **Caching:** Redis for frequently accessed data
- **Monitoring:** Health checks and metrics endpoints
- **Scaling:** Horizontal scaling with load balancers
- **CDN:** S3/CloudFront for image delivery

## 📈 MONITORING & METRICS

### **Key Metrics to Track:**
- Products successfully synced vs failed
- Data completeness percentage
- Sync performance (products/second)
- Database connection health
- API response times
- Recommendation accuracy

### **Health Check Endpoints:**
- `GET /health` - Basic service health
- `GET /ready` - Dependency health checks
- `GET /metrics` - Performance metrics

## 🔮 FUTURE ENHANCEMENTS

### **Planned Features:**
- Real-time sync via database triggers
- Advanced AI vision analysis
- Personalized recommendation engine
- Multi-language support for Thai/English
- Mobile app integration
- Advanced analytics dashboard

### **Technical Debt:**
- Migrate from SQLite references to full MySQL
- Implement proper async database connection pooling
- Add comprehensive API rate limiting
- Enhance error recovery mechanisms

---

## 📞 SUPPORT & MAINTENANCE

### **For Future Developers:**
1. **Always test database connections first** using `test_db_connections.py`
2. **Check product sync results** with `verify_product_import.py`
3. **Monitor logs** for sync errors and performance issues
4. **Keep environment variables secure** and up to date
5. **Run tests** before deploying changes: `poetry run pytest tests/ -v`

### **Emergency Procedures:**
- **Data Loss:** Restore from Magento source using sync scripts
- **Connection Issues:** Verify MySQL service and credentials
- **Performance Problems:** Check database indexes and query optimization
- **Schema Changes:** Use migration scripts, never manual alterations

---

**Last Updated:** September 2025  
**System Status:** ✅ Production Ready  
**Test Coverage:** 117 tests passing  
**Data Quality:** 50-100% depending on source data completeness