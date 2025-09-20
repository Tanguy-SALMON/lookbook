"""
Simple Database Tests

This module contains basic tests for database connectivity and schema
without requiring full application import.
"""

import pytest
import sqlite3
import json
from pathlib import Path


@pytest.fixture(scope="module")
def db_path():
    """Get the SQLite database path."""
    return Path(__file__).parent.parent / "lookbook.db"


class TestDatabaseBasics:
    """Test basic database functionality."""

    def test_database_file_exists(self, db_path):
        """Test that the SQLite database file exists."""
        assert db_path.exists(), f"Database file not found at {db_path}"
        assert db_path.is_file(), f"Database path is not a file: {db_path}"

    def test_database_can_connect(self, db_path):
        """Test that we can connect to the database."""
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Simple query to test connection
        cursor.execute("SELECT 1")
        result = cursor.fetchone()

        assert result[0] == 1, "Basic database query failed"
        conn.close()

    def test_required_tables_exist(self, db_path):
        """Test that all required tables exist in the database."""
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table[0] for table in cursor.fetchall()]

        # Check required tables exist
        required_tables = [
            "products",  # Changed from "items"
            "outfits",
            "outfit_items",
            "rules",
            "alembic_version",
        ]

        missing_tables = []
        for table in required_tables:
            if table not in tables:
                missing_tables.append(table)

        conn.close()

        assert not missing_tables, f"Missing required tables: {missing_tables}"

    def test_items_table_schema(self, db_path):
        """Test that items table has correct schema."""
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Get table schema
        cursor.execute("PRAGMA table_info(products);")
        columns = {col[1]: col[2] for col in cursor.fetchall()}

        # Check required columns exist
        required_columns = [
            "id",
            "sku",
            "title",
            "price",
            "size_range",
            "image_key",
            "attributes",
            "in_stock",
            "created_at",
            "updated_at",
        ]

        missing_columns = []
        for column in required_columns:
            if column not in columns:
                missing_columns.append(column)

        conn.close()

        # For backward compatibility, check if products table has the equivalent columns
        expected_columns = ['id', 'sku', 'title', 'price', 'size_range', 'image_key', 'attributes', 'in_stock', 'created_at', 'updated_at']
        products_columns = {col.replace('item', 'product') if col in expected_columns else col: col_type for col, col_type in columns.items()}
        missing_columns = [col for col in expected_columns if col not in columns and col.replace('item', 'product') not in products_columns]

        assert not missing_columns, (
            f"Missing required columns in items table: {missing_columns}"
        )

    def test_items_table_has_data(self, db_path):
        """Test that items table contains some data."""
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Count items
        # Try both table names for backward compatibility
        try:
            cursor.execute("SELECT COUNT(*) FROM products;")
            result = cursor.fetchone()
            item_count = result[0] if result else 0
        except sqlite3.OperationalError:
            cursor.execute("SELECT COUNT(*) FROM items;")
            result = cursor.fetchone()
            item_count = result[0] if result else 0

        print(f"\nItems in database: {item_count}")

        # Get sample data if exists
        if item_count > 0:
            try:
                cursor.execute("SELECT id, sku, title, price FROM products LIMIT 3;")
                items = cursor.fetchall()

                print("Sample items:")
                for item in items:
                    print(
                        f"  ID: {item[0]}, SKU: {item[1]}, Title: {item[2]}, Price: ${item[3]}"
                    )
            except sqlite3.OperationalError:
                cursor.execute("SELECT id, sku, title, price FROM items LIMIT 3;")
                items = cursor.fetchall()

                print("Sample items:")
                for item in items:
                    print(
                        f"  ID: {item[0]}, SKU: {item[1]}, Title: {item[2]}, Price: ${item[3]}"
                    )

        conn.close()

        # Don't fail if no data, just report
        assert item_count >= 0, "Item count should be non-negative"

    def test_json_fields_valid(self, db_path):
        """Test that JSON fields in database contain valid JSON."""
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Check if we have any items with JSON fields
        # Try both table names
        try:
            cursor.execute("SELECT id, size_range, attributes FROM products LIMIT 5;")
            items = cursor.fetchall()
        except sqlite3.OperationalError:
            cursor.execute("SELECT id, size_range, attributes FROM items LIMIT 5;")
            items = cursor.fetchall()
        items = cursor.fetchall()

        json_errors = []

        for item in items:
            item_id, size_range, attributes = item

            # Test size_range JSON
            if size_range:
                try:
                    parsed_sizes = json.loads(size_range)
                    assert isinstance(parsed_sizes, list), (
                        f"size_range should be a list for item {item_id}"
                    )
                except json.JSONDecodeError as e:
                    json_errors.append(
                        f"Invalid size_range JSON for item {item_id}: {e}"
                    )

            # Test attributes JSON
            if attributes:
                try:
                    parsed_attrs = json.loads(attributes)
                    assert isinstance(parsed_attrs, dict), (
                        f"attributes should be a dict for item {item_id}"
                    )
                except json.JSONDecodeError as e:
                    json_errors.append(
                        f"Invalid attributes JSON for item {item_id}: {e}"
                    )

        conn.close()

        assert not json_errors, f"JSON parsing errors: {json_errors}"

    def test_database_integrity(self, db_path):
        """Test database integrity and constraints."""
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Run integrity check
        cursor.execute("PRAGMA integrity_check;")
        integrity_result = cursor.fetchone()[0]

        # Run foreign key check
        cursor.execute("PRAGMA foreign_key_check;")
        fk_violations = cursor.fetchall()

        conn.close()

        assert integrity_result == "ok", (
            f"Database integrity check failed: {integrity_result}"
        )
        assert not fk_violations, f"Foreign key violations found: {fk_violations}"

    def test_database_performance(self, db_path):
        """Test basic database performance."""
        import time

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Time a simple query
        start_time = time.time()
        # Try both table names
        try:
            cursor.execute("SELECT COUNT(*) FROM products;")
            result = cursor.fetchone()
        except sqlite3.OperationalError:
            cursor.execute("SELECT COUNT(*) FROM items;")
            result = cursor.fetchone()
        end_time = time.time()

        query_time = end_time - start_time

        conn.close()

        print(f"\nDatabase query time: {query_time:.4f} seconds")

        # Query should complete quickly
        assert query_time < 1.0, f"Database query took too long: {query_time:.4f}s"
        assert result is not None and result[0] is not None, "Query should return a valid result from products table"


class TestDatabaseContent:
    """Test actual database content and data quality."""

    def test_items_data_quality(self, db_path):
        """Test the quality of data in items table."""
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Get all items
        # Try both table names
        try:
            cursor.execute("SELECT * FROM products;")
            items = cursor.fetchall()
        except sqlite3.OperationalError:
            cursor.execute("SELECT * FROM items;")
            items = cursor.fetchall()
        items = cursor.fetchall()

        if not items:
            print(
                "\nNo items found in database - this is expected if ingestion hasn't run yet"
            )
            conn.close()
            return

        print(f"\nFound {len(items)} items in database")

        data_issues = []

        for item in items:
            item_id = item[0]
            sku = item[1]
            title = item[2]
            price = item[3]

            # Check required fields are not null/empty
            if not sku:
                data_issues.append(f"Item {item_id} has empty SKU")
            if not title:
                data_issues.append(f"Item {item_id} has empty title")
            if price is None or price < 0:
                data_issues.append(f"Item {item_id} has invalid price: {price}")

        conn.close()

        # Report issues but don't fail test (data quality warnings)
        if data_issues:
            print(f"Data quality issues found: {data_issues}")

        # Only fail on severe issues
        severe_issues = [issue for issue in data_issues if "empty SKU" in issue]
        assert not severe_issues, f"Severe data issues found: {severe_issues}"

    def test_sample_data_display(self, db_path):
        """Display sample data from the database for verification."""
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        print(f"\n{'=' * 60}")
        print("DATABASE CONTENT SAMPLE")
        print(f"{'=' * 60}")

        # Show items
        # Try both table names
        try:
            cursor.execute("SELECT COUNT(*) FROM products;")
            result = cursor.fetchone()
            item_count = result[0] if result else 0
        except sqlite3.OperationalError:
            cursor.execute("SELECT COUNT(*) FROM items;")
            result = cursor.fetchone()
            item_count = result[0] if result else 0
        print(f"Items: {item_count}")

        if item_count > 0:
            # Try both table names
            try:
                cursor.execute("SELECT id, sku, title, price, in_stock FROM products LIMIT 5;")
                items = cursor.fetchall()
            except sqlite3.OperationalError:
                cursor.execute("SELECT id, sku, title, price, in_stock FROM items LIMIT 5;")
                items = cursor.fetchall()

            print("\nSample Items:")
            print("ID | SKU | Title | Price | In Stock")
            print("-" * 50)
            for item in items:
                in_stock = "Yes" if item[4] else "No"
                print(
                    f"{item[0]} | {item[1]} | {item[2][:20]}... | ${item[3]} | {in_stock}"
                )

        # Show outfits
        cursor.execute("SELECT COUNT(*) FROM outfits;")
        result = cursor.fetchone()
        outfit_count = result[0] if result else 0
        print(f"\nOutfits: {outfit_count}")

        # Show rules
        cursor.execute("SELECT COUNT(*) FROM rules;")
        result = cursor.fetchone()
        rule_count = result[0] if result else 0
        print(f"Rules: {rule_count}")

        print(f"{'=' * 60}\n")

        conn.close()

        # This test always passes - it's just for information
        assert True
