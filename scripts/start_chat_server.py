#!/usr/bin/env python3
"""
Chat Server Startup Script

Simple script to start the Lookbook-MPC server with minimal environment
variables for chat testing.
"""

import os
import sys
import subprocess
import signal
import time
from pathlib import Path

# Add the project root to the path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def set_minimal_env_vars():
    """Set minimal required environment variables for chat testing."""
    env_vars = {
        "OLLAMA_HOST": "http://localhost:11434",
        "OLLAMA_VISION_MODEL": "qwen2.5vl:7b",
        "OLLAMA_TEXT_MODEL": "qwen3:4b",
        "S3_BASE_URL": "https://example.com/",
        "MYSQL_APP_URL": "mysql+pymysql://magento:Magento@COS(*)@127.0.0.1:3306/lookbookMPC",
    }

    for key, value in env_vars.items():
        if key not in os.environ:
            os.environ[key] = value
            print(f"Set {key}={value}")


def start_server():
    """Start the FastAPI server."""
    print("🚀 Starting Lookbook-MPC Chat Server...")
    print("=" * 50)

    # Set environment variables
    set_minimal_env_vars()

    # Change to project directory
    os.chdir(PROJECT_ROOT)

    print(f"Project directory: {PROJECT_ROOT}")
    print(f"Server will be available at: http://localhost:8000")
    print(f"Demo chat interface: http://localhost:8000/demo")
    print(f"API documentation: http://localhost:8000/docs")
    print("=" * 50)
    print("Press Ctrl+C to stop the server")
    print()

    try:
        # Start the server using poetry
        cmd = ["poetry", "run", "python", "main.py"]
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
        )

        # Stream output
        while True:
            output = process.stdout.readline()
            if output == "" and process.poll() is not None:
                break
            if output:
                print(output.strip())

    except KeyboardInterrupt:
        print("\n🛑 Shutting down server...")
        process.terminate()
        process.wait()
        print("✅ Server stopped.")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Start Lookbook-MPC Chat Server")
    parser.add_argument(
        "--test-first",
        action="store_true",
        help="Run chat tests before starting server",
    )

    args = parser.parse_args()

    if args.test_first:
        print("🧪 Running chat tests first...")
        test_cmd = ["poetry", "run", "python", "scripts/test_chat_direct.py"]
        result = subprocess.run(test_cmd, cwd=PROJECT_ROOT)

        if result.returncode != 0:
            print("❌ Chat tests failed. Please fix issues before starting server.")
            sys.exit(1)
        else:
            print("✅ All chat tests passed!")
            print()

    start_server()


if __name__ == "__main__":
    main()
