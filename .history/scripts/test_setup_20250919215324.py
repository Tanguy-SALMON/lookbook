
#!/usr/bin/env python3
"""
Test runner script to validate the Lookbook-MPC setup.
This script runs basic tests to ensure the application is properly configured.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Run a command and return success status."""
    print(f"\n{'='*50}")
    print(f"Testing: {description}")
    print(f"Command: {' '.join(command)}")
    print(f"{'='*50}")

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )

        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            if result.stdout:
                print("Output:", result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout)
            return True
        else:
            print(f"❌ {description} - FAILED")
            if result.stderr:
                print("Error:", result.stderr[:500] + "..." if len(result.stderr) > 500 else result.stderr)
            return False

    except Exception as e:
        print(f"❌ {description} - EXCEPTION: {str(e)}")
        return False


def check_file_exists(filepath, description):
    """Check if a file exists."""
    full_path = Path(__file__).parent.parent / filepath
    if full_path.exists():
        print(f"✅ {description} - EXISTS: {filepath}")
        return True
    else:
        print(f"❌ {description} - MISSING: {filepath}")
        return False


def main():
    """Main test runner function."""
    print("🚀 Lookbook-MPC Setup Validation")
    print("=" * 50)

    # Check if we're in the right directory
    if not (Path(__file__).parent.parent / "pyproject.toml").exists():
        print("❌ ERROR: Run this script from the project root directory")
        sys.exit(1)

    # Track results
    results = []

    # Check essential files
    print("\n📁 Checking essential files...")
    essential_files = [
        ("pyproject.toml", "Project configuration"),
        ("main.py", "Main application file"),
        (".env.example", "Environment template"),
        ("README.md", "Documentation"),
        (".gitignore", "Git ignore file"),
        ("pytest.ini", "Pytest configuration"),
        ("lookbook_mpc/__init__.py", "Main package"),
        ("lookbook_mpc/domain/__init__.py", "Domain package"),
        ("lookbook_mpc/adapters/__init__.py", "Adapters package"),
        ("lookbook_mpc/services/__init__.py", "Services package"),
        ("lookbook_mpc/api/__init__.py", "API package"),
        ("tests/test_main.py", "Main tests"),
        ("tests/conftest.py", "Test configuration"),
    ]

    for filepath, description in essential_files:
        results.append(check_file_exists(filepath, description))

    # Check Python syntax
    print("\n🐍 Checking Python syntax...")
    python_files = [
        "main.py",
        "lookbook_mpc/domain/entities.py",
        "lookbook_mpc/domain/use_cases.py",
        "lookbook_mpc/adapters/db_shop.py",
        "lookbook_mpc/adapters/db_lookbook.py",
        "lookbook_mpc/adapters/vision.py",
        "lookbook_mpc/adapters/intent.py",
        "lookbook_mpc/adapters/images.py",
        "lookbook_mpc/services/rules.py",
        "lookbook_mpc/services/recommender.py",
        "lookbook_mpc/api/routers/ingest.py",
        "lookbook_mpc/api/routers/reco.py",
        "lookbook_mpc/api/routers/chat.py",
        "lookbook_mpc/api/routers/images.py",
        "lookbook_mpc/api/mcp_server.py",
    ]

    for python_file in python_files:
        results.append(run_command(
            [sys.executable, "-m", "py_compile", python_file],
            f"Python syntax check for {python_file}"
        ))

    # Check if we can import the main module
    print("\n📦 Checking module imports...")
    results.append(run_command(
        [sys.executable, "-c", "import main; print('Main module imported successfully')"],
        "Main module import"
    ))

    # Check if we can import the package
    print("\n📦 Checking package imports...")
    results.append(run_command(
        [sys.executable, "-c", "import lookbook_mpc; print('Package imported successfully')"],
        "Package import"
    ))

    # Check pytest configuration
    print("\n🧪 Checking pytest configuration...")
    results.append(run_command(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        "Pytest collection"
    ))

    # Run basic tests
    print("\n🧪 Running basic tests...")
    results.append(run_command(
        [sys.executable, "-m", "pytest", "tests/test_main.py", "-v"],
        "Basic tests"
    ))

    # Check FastAPI app creation
    print("\n🚀 Checking FastAPI app creation...")
    results.append(run_command(
        [sys.executable, "-c", """
import main
app = main.app
print(f"App title: {app.title}")
print(f"App version: {app.version}")
print(f"App description: {app.description}")
print("FastAPI app created successfully")
"""],
        "FastAPI app creation"
    ))

    # Check environment variables
    print("\n🔧 Checking environment variables...")
    results.append(run_command(
        [sys.executable, "-c", """
import os
required_vars = ['OLLAMA_HOST', 'OLLAMA_VISION_MODEL', 'OLLAMA_TEXT_MODEL', 'S3_BASE_URL']
print(f"Required environment variables:")
for var in required_vars:
    value = os.getenv(var)
    status = "SET" if value else "NOT SET"
    print(f"  {var}: {status}")
print("Environment check completed")
"""],
        "Environment variables check"
    ))

    # Summary
    print("\n" + "=" * 50)
    print("📊 SETUP VALIDATION SUMMARY")
    print("=" * 50)

    total_tests = len(results)
    passed_tests = sum(results)
    failed_tests = total_tests - passed_tests

    print(f"Total checks: {total_tests}")
    print(f"Passed: ✅ {passed_tests}")
    print(f"Failed: ❌ {failed_tests}")
    print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")

    if failed_tests == 0:
        print("\n🎉 ALL CHECKS PASSED! Setup is ready.")
        print("\nNext steps:")
        print("1. Copy .env.example to .env and configure your environment")
        print("2. Install dependencies: pip install -e .")
        print("3. Start the application: python main.py")
        print("4. Access API docs at: http://localhost:8000/docs")
        return 0
    else:
