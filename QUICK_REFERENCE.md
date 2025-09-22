# QUICK REFERENCE CARD
# Lookbook-MPC Fashion Recommendation System

## 🚀 ESSENTIAL COMMANDS

```bash
# Database connection test (run this first)
poetry run python scripts/test_db_connections.py

# Main product sync (most important command)
poetry run python scripts/sync_100_products.py

# Verify imported data
poetry run python scripts/verify_product_import.py

# Test API endpoints
poetry run python scripts/test_api.py

# Comprehensive chat testing
poetry run python scripts/test_chat_comprehensive.py

# Run all tests
poetry run pytest tests/ -v

# Start API server
poetry run python main.py
```

## 📊 DATABASE INFO

**Source (Magento):** `cos-magento-4`
- Connection: `mysql+pymysql://magento:Magento@COS(*)@localhost:3306/cos-magento-4`
- Products: 6,629 configurable + 41,030 simple

**Destination (App):** `lookbookMPC`  
- Connection: `mysql+pymysql://magento:Magento@COS(*)@127.0.0.1:3306/lookbookMPC`
- Schema: Flat structure (no JSON attributes)

## 💰 CURRENCY & PRICING

- **Market:** Thailand
- **Currency:** Thai Baht (THB)
- **Display:** ฿1,090 - ฿10,990 range
- **Storage:** Direct THB values (no conversion)

## 🔧 ENVIRONMENT VARIABLES (.env)

```bash
MYSQL_SHOP_URL=mysql+pymysql://magento:Magento@COS(*)@localhost:3306/cos-magento-4
MYSQL_APP_URL=mysql+pymysql://magento:Magento@COS(*)@127.0.0.1:3306/lookbookMPC
S3_BASE_URL=https://your-cdn-domain.com/
```

## 🗂️ KEY FILE LOCATIONS

- **Essential scripts:** `scripts/` (23 core scripts, see `scripts/README.md`)
- **Main sync script:** `scripts/sync_100_products.py`
- **Database testing:** `scripts/test_db_connections.py`
- **API testing:** `scripts/test_api.py`
- **Benchmark scripts:** `scripts/benchmark_models*.py`
- **Database adapters:** `lookbook_mpc/adapters/db_*.py`
- **Domain models:** `lookbook_mpc/domain/entities.py`
- **Configuration:** `lookbook_mpc/config/settings.py`
- **API entry:** `main.py`

## 🎯 MAGENTO ATTRIBUTE IDs

- Price: 77
- Name: 73  
- Status: 97
- Color: 93
- Material: 148
- Swatch Image: 358

## ⚠️ COMMON FIXES

**Missing cryptography:**
```bash
poetry add cryptography
```

**Password in URL:** Use direct string `"Magento@COS(*)"` in connection code

**UUID Sessions:** Use `uuid.uuid4()` not timestamps

**Pydantic Validation:** Remove `ge=0` constraints, use custom `@validator`

## 🧪 TEST STATUS

✅ **117 tests passing**
- Fixed entity validation
- Fixed session ID format  
- Fixed outfit creation
- Fixed database connections

## 📁 SCRIPTS STATUS

✅ **Scripts consolidated: 50+ → 23 essential files**
- All benchmark scripts preserved
- Duplicate chat testing scripts consolidated
- Database scripts streamlined
- Archive: `scripts/archive/` (30+ files preserved)

## 📋 PRODUCT SCHEMA

```sql
products:
  - id (PK)
  - sku (unique)
  - title, price (THB)
  - color, material, season
  - image_key, url_key
  - stock_qty, in_stock
  - created_at, updated_at
```

## 🎨 SAMPLE DATA

- **T-Shirts:** ฿1,090 - ฿1,190
- **Dresses:** ฿5,990 - ฿6,990  
- **Jackets:** ฿7,990 - ฿9,990
- **Colors:** Black, Blue, White, Beige
- **Brands:** H&M style fashion items

## 🚨 EMERGENCY CHECKLIST

1. ✅ MySQL service running?
2. ✅ Environment variables set?
3. ✅ Database connections working?
4. ✅ Tests passing?
5. ✅ Product sync successful?

**If issues:** Run `test_db_connections.py` first!