"""
backend/scripts/reset_dev_data.py
=================================
Safely clears development user-generated data without dropping tables
or deleting default seed data (crops, diseases, model_versions).

Usage:
    python scripts/reset_dev_data.py --confirm
"""

import asyncio
import os
import sys
import glob

# Ensure backend directory is in python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from database import AsyncSessionLocal
from sqlalchemy import text
from config import UPLOAD_DIR


async def reset_data():
    if "--confirm" not in sys.argv:
        print("[ERROR] Destructive operation aborted. Run with --confirm to execute.")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("  DEVELOPMENT DATA CLEANUP - PRESERVING DEFAULT SEED DATA")
    print("=" * 60)

    async with AsyncSessionLocal() as session:
        # Delete user-generated rows in reverse foreign key order
        tables_to_clear = [
            "reports",
            "weather_snapshots",
            "predictions",
            "scans",
            "farms",
            "users",
        ]

        for table in tables_to_clear:
            res = await session.execute(text(f"DELETE FROM {table};"))
            print(f"  [OK] Cleared table '{table}': {res.rowcount} rows deleted.")

        await session.commit()

        # Verify preserved default tables
        print("\nVerifying preserved default seed data:")
        for seed_table in ["crops", "diseases", "model_versions"]:
            count_res = await session.execute(text(f"SELECT count(*) FROM {seed_table};"))
            count = count_res.scalar()
            print(f"  [PRESERVED] '{seed_table}': {count} default rows remain intact.")

    # Clean up uploaded scan files in uploads/scans
    scans_dir = os.path.join(UPLOAD_DIR, "scans")
    if os.path.exists(scans_dir):
        files = glob.glob(os.path.join(scans_dir, "*"))
        removed_count = 0
        for f in files:
            if os.path.isfile(f):
                os.remove(f)
                removed_count += 1
        print(f"\n  [OK] Removed {removed_count} test scan images from {scans_dir}")

    print("\n" + "=" * 60)
    print("  DEVELOPMENT DATA CLEANUP COMPLETED SUCCESSFULLY")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(reset_data())
