#!/usr/bin/env python3
"""Script to run the synthetic data generator and export snapshots."""
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.sim.generator import SyntheticDataGenerator


def main() -> int:
    print("=" * 60)
    print("HippoGrid — Synthetic Data Generation Engine (Seed: 42)")
    print("=" * 60)

    generator = SyntheticDataGenerator(seed=42)
    print("[1/3] Generating multi-dependency synthetic network & telemetry...")
    datasets = generator.generate_all()

    print("[2/3] Exporting CSV and Parquet snapshots to data/raw/...")
    exported_files = generator.export_snapshots(datasets)
    print(f"  Successfully exported {len(exported_files)} files:")
    for f in exported_files:
        print(f"    - {Path(f).name}")

    print("[3/3] Telemetry Summary:")
    print(f"  States:     {len(datasets['states'])}")
    print(f"  Districts:  {len(datasets['districts'])}")
    print(f"  PHCs:       {len(datasets['phcs'])}")
    print(f"  Warehouses: {len(datasets['warehouses'])}")
    print(f"  Weather rows:   {len(datasets['weather'])}")
    print(f"  Patient rows:   {len(datasets['patient'])}")
    print(f"  Workforce rows: {len(datasets['workforce'])}")
    print(f"  Bed rows:       {len(datasets['beds'])}")
    print(f"  Power rows:     {len(datasets['power'])}")
    print(f"  Inventory rows: {len(datasets['inventory'])}")
    print(f"  Road rows:      {len(datasets['roads'])}")

    print("\n[SUCCESS] Phase 2 synthetic generation completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
