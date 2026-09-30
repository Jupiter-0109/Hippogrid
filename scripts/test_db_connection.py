#!/usr/bin/env python3
"""Script to verify Supabase PostgreSQL database connectivity."""
import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.core.config import get_settings
from backend.db.session import check_db_connection


def main() -> int:
    settings = get_settings()
    print("=" * 60)
    print("HippoGrid — Supabase PostgreSQL Connectivity Diagnostic")
    print("=" * 60)
    print(f"Target Database URL: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'configured'}")

    result = check_db_connection()
    if result.get("connected"):
        print("[SUCCESS] Connected to Supabase PostgreSQL database!")
        print(f"  Status: {result.get('status')}")
        print(f"  Latency: {result.get('latency_ms')} ms")
        return 0
    else:
        print("[WARNING / OFFLINE] Could not establish connection to PostgreSQL.")
        print(f"  Status: {result.get('status')}")
        print(f"  Error: {result.get('error')}")
        print(f"  Latency: {result.get('latency_ms')} ms")
        print("\nPlease ensure your DATABASE_URL in .env has valid credentials.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
