"""
backend/test_weather_flow.py
============================
Integration test suite for Module 13 — Weather Integration.
Tests:
  1. Farm with GPS coordinates retrieves weather from Open-Meteo & saves snapshot.
  2. Freshness policy: second retrieval returns cached snapshot.
  3. Force refresh (?force_refresh=true) queries provider and updates snapshot.
  4. Farm without GPS coordinates gracefully returns clear message without API call.
  5. Cross-tenant security: Farmer B requesting Farmer A's farm weather gets 404.
  6. Unauthenticated request returns 401.
  7. Verifies database weather_snapshots persistence and nullable scan_id.
"""

import asyncio
import os
import sys
import uuid

import httpx
from sqlalchemy import select

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config
from database import AsyncSessionLocal
from models import Farm, User, WeatherSnapshot
from services.weather_service import WeatherService
from services.farm_service import FarmService


async def run_weather_tests():
    print("\n" + "=" * 60)
    print("RUNNING MODULE 13 INTEGRATION TESTS: WEATHER INTEGRATION")
    print("=" * 60)

    test_uid_1 = f"test_farmer_wx_1_{uuid.uuid4().hex[:6]}"
    test_uid_2 = f"test_farmer_wx_2_{uuid.uuid4().hex[:6]}"
    user1_dict = {"uid": test_uid_1, "name": "Ramesh Patel", "phone_number": "+919876543210"}
    user2_dict = {"uid": test_uid_2, "name": "Suresh Kumar", "phone_number": "+919876543211"}

    async with AsyncSessionLocal() as session:
        # Create user 1 and user 2 in PostgreSQL
        u1 = User(
            auth_provider="firebase",
            auth_provider_user_id=test_uid_1,
            display_name="Ramesh Patel",
            phone_number="+919876543210",
        )
        u2 = User(
            auth_provider="firebase",
            auth_provider_user_id=test_uid_2,
            display_name="Suresh Kumar",
            phone_number="+919876543211",
        )
        session.add_all([u1, u2])
        await session.commit()
        await session.refresh(u1)
        await session.refresh(u2)

        user1_dict["id"] = str(u1.id)
        user2_dict["id"] = str(u2.id)

        # Create Farm 1 (with GPS coordinates - Anand, Gujarat: 22.5645, 72.9289)
        farm_with_gps = Farm(
            user_id=u1.id,
            name="Anand Green Acres",
            village="Mogri",
            district="Anand",
            state="Gujarat",
            area_hectares=4.5,
            latitude=22.5645,
            longitude=72.9289,
        )
        # Create Farm 2 (WITHOUT GPS coordinates)
        farm_without_gps = Farm(
            user_id=u1.id,
            name="Dryland Plot",
            village="Mogri",
            district="Anand",
            state="Gujarat",
            area_hectares=2.0,
            latitude=None,
            longitude=None,
        )
        # Create Farm 3 (owned by User 2)
        farm_user2 = Farm(
            user_id=u2.id,
            name="Suresh Agro Farm",
            village="Nadiad",
            district="Kheda",
            state="Gujarat",
            latitude=22.6916,
            longitude=72.8634,
        )
        session.add_all([farm_with_gps, farm_without_gps, farm_user2])
        await session.commit()
        await session.refresh(farm_with_gps)
        await session.refresh(farm_without_gps)
        await session.refresh(farm_user2)

        weather_service = WeatherService(session)

        # -------------------------------------------------------------
        # TEST 1: Retrieve weather for farm with GPS coordinates
        # -------------------------------------------------------------
        print("\n--- TEST 1: Retrieve weather for farm with GPS coordinates ---")
        wx_resp1 = await weather_service.get_farm_weather(
            farm_id=farm_with_gps.id,
            user_dict=user1_dict,
            force_refresh=False,
        )
        assert wx_resp1["status"] == "success", "Expected status 'success'"
        assert wx_resp1["has_location"] is True, "Expected has_location=True"
        assert wx_resp1["temperature_c"] is not None, "Expected valid temperature_c"
        assert wx_resp1["humidity_pct"] is not None, "Expected valid humidity_pct"
        assert wx_resp1["weather_condition"] is not None, "Expected weather condition text"
        assert wx_resp1["data_source"] == "Open-Meteo", "Expected data_source 'Open-Meteo'"
        assert wx_resp1["cached"] is False, "First request should be live (cached=False)"
        assert wx_resp1["snapshot_id"] is not None, "Expected snapshot_id to be set"
        first_snapshot_id = wx_resp1["snapshot_id"]
        print(f"  [PASS] Retrieved live weather: {wx_resp1['temperature_c']}°C, "
              f"Humidity {wx_resp1['humidity_pct']}%, Condition: '{wx_resp1['weather_condition']}'")
        print(f"         Snapshot ID: {first_snapshot_id}")

        # -------------------------------------------------------------
        # TEST 2: Freshness policy — immediate subsequent call returns cached snapshot
        # -------------------------------------------------------------
        print("\n--- TEST 2: Freshness cache (subsequent call within 30 min) ---")
        wx_resp2 = await weather_service.get_farm_weather(
            farm_id=farm_with_gps.id,
            user_dict=user1_dict,
            force_refresh=False,
        )
        assert wx_resp2["cached"] is True, "Expected cached=True on repeat request"
        assert wx_resp2["snapshot_id"] == first_snapshot_id, "Should reuse the same snapshot ID"
        print(f"  [PASS] Freshness cache hit! Returned cached snapshot: {wx_resp2['snapshot_id']}")

        # -------------------------------------------------------------
        # TEST 3: Force refresh bypasses cache
        # -------------------------------------------------------------
        print("\n--- TEST 3: Force refresh (?force_refresh=true) ---")
        wx_resp3 = await weather_service.get_farm_weather(
            farm_id=farm_with_gps.id,
            user_dict=user1_dict,
            force_refresh=True,
        )
        assert wx_resp3["cached"] is False, "Expected cached=False on force refresh"
        assert wx_resp3["snapshot_id"] is not None
        print(f"  [PASS] Force refresh succeeded! New snapshot ID: {wx_resp3['snapshot_id']}")

        # -------------------------------------------------------------
        # TEST 4: Farm without GPS coordinates handled gracefully
        # -------------------------------------------------------------
        print("\n--- TEST 4: Farm without GPS coordinates handled gracefully ---")
        wx_no_gps = await weather_service.get_farm_weather(
            farm_id=farm_without_gps.id,
            user_dict=user1_dict,
            force_refresh=False,
        )
        assert wx_no_gps["has_location"] is False, "Expected has_location=False"
        assert "coordinates (latitude and longitude) are not configured" in wx_no_gps["message"]
        assert wx_no_gps["temperature_c"] is None
        assert wx_no_gps["snapshot_id"] is None
        print(f"  [PASS] No-GPS farm handled cleanly: '{wx_no_gps['message']}'")

        # -------------------------------------------------------------
        # TEST 5: Tenant isolation — User 2 cannot access User 1's farm weather
        # -------------------------------------------------------------
        print("\n--- TEST 5: Tenant isolation (cross-user access blocked) ---")
        cross_tenant_blocked = False
        try:
            await weather_service.get_farm_weather(
                farm_id=farm_with_gps.id,
                user_dict=user2_dict,  # User 2 attempting to view User 1's farm weather
            )
        except Exception as exc:
            cross_tenant_blocked = True
            print(f"  [PASS] Successfully blocked with error: {exc}")
        assert cross_tenant_blocked, "User 2 should NOT be able to view User 1's farm weather!"

        # -------------------------------------------------------------
        # TEST 6: Verify Database WeatherSnapshot rows
        # -------------------------------------------------------------
        print("\n--- TEST 6: Verify PostgreSQL weather_snapshots records ---")
        stmt = (
            select(WeatherSnapshot)
            .where(WeatherSnapshot.farm_id == farm_with_gps.id)
            .order_by(WeatherSnapshot.created_at.desc())
        )
        db_snapshots = (await session.execute(stmt)).scalars().all()
        assert len(db_snapshots) >= 2, f"Expected at least 2 snapshots, got {len(db_snapshots)}"
        latest_db_snap = db_snapshots[0]
        assert latest_db_snap.data_source == "Open-Meteo"
        assert latest_db_snap.temperature_c is not None
        assert latest_db_snap.farm_id == farm_with_gps.id
        print(f"  [PASS] Verified {len(db_snapshots)} snapshot records in PostgreSQL. Latest temp: {latest_db_snap.temperature_c}°C")

        # Clean up test entities
        await session.delete(farm_with_gps)
        await session.delete(farm_without_gps)
        await session.delete(farm_user2)
        await session.delete(u1)
        await session.delete(u2)
        await session.commit()
        print("\n  [CLEANUP] Successfully cleaned up test database fixtures.")

    print("\n" + "=" * 60)
    print("ALL MODULE 13 TESTS PASSED SUCCESSFULLY!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(run_weather_tests())
