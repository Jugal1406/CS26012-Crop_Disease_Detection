# Database Schema & Relational Models

The project uses PostgreSQL with SQLAlchemy 2.0 Async ORM and Alembic migrations.

## Relational Tables Overview

```
users (id, auth_provider, auth_provider_user_id, display_name, email, phone_number, preferred_language, is_active)
  ├── 1:N ── farms (id, user_id, farm_name, village, district, state, total_area_hectares, latitude, longitude, is_primary)
  │            └── 1:N ── weather_snapshots (id, farm_id, temperature_c, humidity_pct, rainfall_mm, wind_speed_kmh, weather_condition)
  ├── 1:N ── scans (id, user_id, farm_id, crop_id, disease_id, model_id, image_path, confidence, status, is_flagged)
  │            └── 1:1 ── reports (id, scan_id, user_id, immediate_management, prevention_steps, escalation_triggers, disclaimer, language)
  └── 1:N ── audit_logs (id, user_id, event_type, payload, ip_address, created_at)

crops (id, name, slug, scientific_name, is_active)
  ├── 1:N ── disease_classes (id, crop_id, name, slug, local_name_hi, local_name_gu, is_healthy)
  └── 1:N ── models (id, crop_id, name, version, architecture, file_path, input_size, threshold, is_active)
```

## Migration Management

Migrations are located in `backend/alembic/versions/`:
- `40143822dc19_initial_schema_all_9_tables.py`: Creates all 9 tables with foreign keys and check constraints.
- `d6a9eecc88cf_clerk_auth_identity_mapping.py`: Supports Clerk session user mapping.

### Migration Commands:
```powershell
# Apply migrations:
alembic upgrade head

# Rollback one migration:
alembic downgrade -1
```
