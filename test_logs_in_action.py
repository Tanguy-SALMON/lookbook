#!/usr/bin/env python3
"""
Test to show SmartRecommender logs with proper configuration.
This demonstrates where and how logs appear during recommendation processing.
"""

import asyncio
import os
import sys
import logging
import structlog

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging exactly like main.py does
def setup_logging():
    """Setup logging configuration matching main.py"""
    from lookbook_mpc.config.settings import get_settings

    settings = get_settings()

    # Configure logging level from settings
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(level=log_level, format='%(message)s')

    # Configure structured logging
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Add appropriate renderer based on log format
    if settings.log_format.lower() == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    print(f"✅ Logging configured: Level={settings.log_level.upper()}, Format={settings.log_format}")
    return structlog.get_logger()

async def test_smart_recommender_logs():
    """Test SmartRecommender and show all log output."""
    print("\n" + "="*60)
    print("SMART RECOMMENDER LOGS TEST")
    print("="*60)

    logger = setup_logging()

    print(f"\n🔍 Testing SmartRecommender with detailed logging")
    print(f"📋 You should see logs for each step below:")
    print(f"   1. Starting smart recommendation")
    print(f"   2. Keywords generated successfully")
    print(f"   3. Added missing bottoms (if needed)")
    print(f"   4. Product diversification completed")
    print(f"   5. Smart recommendation completed")
    print(f"\n" + "-"*60)
    print("LOG OUTPUT:")
    print("-"*60)

    try:
        from lookbook_mpc.services.smart_recommender import SmartRecommender
        from lookbook_mpc.adapters.db_lookbook import MySQLLookbookRepository
        from lookbook_mpc.config.settings import get_settings

        # Create recommender
        settings = get_settings()
        repository = MySQLLookbookRepository(settings.get_database_url())
        recommender = SmartRecommender(repository)

        # Test with a message that should trigger all log points
        test_message = "I need something for a business meeting"

        # This will generate logs at each step
        outfits = await recommender.recommend_outfits(test_message, limit=2)

        print("-"*60)
        print("RESULTS:")
        print("-"*60)
        print(f"✅ Returned {len(outfits)} outfits")

        for i, outfit in enumerate(outfits, 1):
            items = outfit.get('items', [])
            title = outfit.get('title', 'Untitled')
            outfit_type = outfit.get('outfit_type', 'unknown')
            total_price = outfit.get('total_price', 0)

            print(f"\nOutfit {i}: {title}")
            print(f"  Type: {outfit_type}")
            print(f"  Items: {len(items)}")
            for item in items:
                item_title = item.get('title', 'Unknown')
                category = item.get('category', 'unknown')
                price = item.get('price', 0)
                print(f"    - {item_title} ({category}) - ${price}")
            print(f"  Total: ${total_price}")

            # Check if complete outfit
            categories = [item.get('category') for item in items]
            has_top = 'top' in categories
            has_bottom = 'bottom' in categories
            has_dress = 'dress' in categories

            if has_dress or (has_top and has_bottom):
                print(f"  ✅ COMPLETE OUTFIT")
            else:
                print(f"  ⚠️  Incomplete outfit")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def show_log_locations():
    """Show where logs appear and how to control them."""
    print(f"\n" + "="*60)
    print("WHERE TO FIND LOGS")
    print("="*60)

    print(f"""
📍 LOG LOCATIONS:
   • Console/Terminal: All logs appear in stdout when running the server
   • Server startup: ./start.sh shows logging configuration
   • Development: Use LOG_LEVEL=DEBUG for maximum detail

🔧 CONTROLLING LOG LEVELS:
   • DEBUG: All messages including detailed debugging
   • INFO: General information messages (default)
   • WARNING: Only warnings and errors
   • ERROR: Only error messages

📝 LOG SOURCES IN SMART RECOMMENDER:
   • Line 77: "Starting smart recommendation"
   • Line 195: "Keywords generated successfully"
   • Line 207: "LLM keyword generation failed" (on error)
   • Line 242: "Failed to parse keywords JSON" (on error)
   • Line 347: "Product search failed" (on error)
   • Line 587: "Product diversification completed"
   • Line 623: "Added missing tops"
   • Line 629: "Added missing bottoms"
   • Line 635: "Category balance failed" (on error)
   • Line 688: "Specific category search failed" (on error)
   • Line 804: "Outfit creation failed" (on error)
   • Line 95: "Smart recommendation completed"

🚀 TO SEE MORE LOGS:
   1. Set LOG_LEVEL=DEBUG in your .env file
   2. Or run: LOG_LEVEL=DEBUG ./start.sh
   3. Or export LOG_LEVEL=DEBUG before starting

📊 LOG FORMAT OPTIONS:
   • LOG_FORMAT=json: Structured JSON logs (default)
   • LOG_FORMAT=text: Human-readable console logs
""")

async def main():
    """Main test function."""
    print("LOOKBOOK-MPC SMART RECOMMENDER LOGGING TEST")
    print("This shows you exactly where and how logs appear")

    await test_smart_recommender_logs()
    show_log_locations()

    print(f"\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    print(f"✅ If you saw structured logs above, logging is working correctly!")
    print(f"🔧 Adjust LOG_LEVEL in .env or start.sh to control verbosity")
    print(f"💡 Use LOG_LEVEL=DEBUG to see all SmartRecommender internal steps")

if __name__ == "__main__":
    asyncio.run(main())
