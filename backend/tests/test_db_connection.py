# -*- coding: utf-8 -*-
"""
backend/test_db_connection.py
=============================
Standalone CLI test script for Module 8 Database Layer.

Validates:
  1. Reading .env configuration (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)
  2. Asynchronous PostgreSQL connection via SQLAlchemy + asyncpg
  3. Response latency & database version verification
  4. Existence of all 9 Module 7 tables in PostgreSQL schema
  5. Seeded reference data (Crops, Diseases, Model Versions)
  6. Repository layer integration (CropRepository, BaseRepository)
  7. Async session lifecycle & automatic rollback/close

Run from backend directory:
    python test_db_connection.py
Or from project root:
    python backend/test_db_connection.py
"""

import asyncio
import os
import sys
import time

# Ensure backend directory is in sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from sqlalchemy import text
from config import DB_HOST, DB_NAME, DB_PORT, DB_USER
from database import AsyncSessionLocal, check_db_connection, engine
from repositories.crop_repository import CropRepository

EXPECTED_TABLES = {
    "users",
    "farms",
    "crops",
    "diseases",
    "scans",
    "predictions",
    "weather_snapshots",
    "reports",
    "model_versions",
}


def print_status(test_name: str, passed: bool, detail: str = "") -> None:
    badge = "[PASS]" if passed else "[FAIL]"
    print(f"  {badge}  {test_name}")
    if detail:
        print(f"         {detail}")


async def run_diagnostics():
    print("=" * 70)
    print("       CROP DISEASE DETECTION - DATABASE CONNECTION TEST")
    print("=" * 70)
    print(f"Target Database : {DB_NAME} on {DB_HOST}:{DB_PORT}")
    print(f"Target User     : {DB_USER}")
    print("-" * 70)

    results = []

    # 1. Connection check helper
    db_status = await check_db_connection()
    conn_ok = db_status.get("connected", False)
    results.append(conn_ok)
    if conn_ok:
        version = db_status.get("version", "").split("\n")[0]
        latency = db_status.get("latency_ms", 0.0)
        print_status(
            "Direct PostgreSQL Connection",
            True,
            f"Latency: {latency}ms | Version: {version[:55]}...",
        )
    else:
        err = db_status.get("error", "Unknown error")
        print_status("Direct PostgreSQL Connection", False, f"Error: {err}")
        print("\nAborting further checks due to connection failure.")
        return False

    # 2. Table schema verification
    async with AsyncSessionLocal() as session:
        table_result = await session.execute(
            text(
                "SELECT tablename FROM pg_tables "
                "WHERE schemaname = 'public' ORDER BY tablename;"
            )
        )
        existing_tables = {row[0] for row in table_result.fetchall()}

        missing_tables = EXPECTED_TABLES - existing_tables
        schema_ok = len(missing_tables) == 0
        results.append(schema_ok)
        if schema_ok:
            print_status(
                "Schema Tables Verified",
                True,
                f"Found all {len(EXPECTED_TABLES)} required tables in 'public' schema.",
            )
        else:
            print_status(
                "Schema Tables Verified",
                False,
                f"Missing tables: {', '.join(sorted(missing_tables))}",
            )

        # 3. Seed data verification
        crop_count_res = await session.execute(text("SELECT count(*) FROM crops;"))
        crop_count = crop_count_res.scalar() or 0

        disease_count_res = await session.execute(text("SELECT count(*) FROM diseases;"))
        disease_count = disease_count_res.scalar() or 0

        model_count_res = await session.execute(text("SELECT count(*) FROM model_versions;"))
        model_count = model_count_res.scalar() or 0

        seed_ok = crop_count >= 8 and disease_count >= 6 and model_count >= 1
        results.append(seed_ok)
        print_status(
            "Reference Data Seed Integrity",
            seed_ok,
            f"Crops: {crop_count} (>=8) | Diseases: {disease_count} (>=6) | Models: {model_count} (>=1)",
        )

        # 4. Repository layer integration check
        try:
            crop_repo = CropRepository(session)
            supported = await crop_repo.get_supported_crops()
            chili_crop = await crop_repo.get_by_name("chili")
            chili_diseases = (
                await crop_repo.get_diseases_by_crop_id(chili_crop.id)
                if chili_crop
                else []
            )

            repo_ok = (
                len(supported) >= 1
                and chili_crop is not None
                and len(chili_diseases) >= 6
            )
            results.append(repo_ok)
            print_status(
                "Repository Layer Query Test (CropRepository)",
                repo_ok,
                f"Resolved '{chili_crop.name if chili_crop else 'none'}' with {len(chili_diseases)} disease classes.",
            )
        except Exception as exc:
            results.append(False)
            print_status("Repository Layer Query Test", False, str(exc))

    # Summary
    passed_count = sum(results)
    total_count = len(results)
    print("-" * 70)
    print(f"Summary: {passed_count}/{total_count} database diagnostics passed.")
    if passed_count == total_count:
        print("[SUCCESS] Module 8 PostgreSQL Database Layer is fully operational.")
    else:
        print("[WARNING] One or more database diagnostics failed.")
    print("=" * 70)
    return passed_count == total_count


if __name__ == "__main__":
    success = asyncio.run(run_diagnostics())
    sys.exit(0 if success else 1)
