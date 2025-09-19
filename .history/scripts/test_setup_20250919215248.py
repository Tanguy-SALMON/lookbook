
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
