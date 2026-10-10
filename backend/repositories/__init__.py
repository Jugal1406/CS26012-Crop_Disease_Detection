"""
backend/repositories/__init__.py
================================
Repository layer providing data access objects for database entities.
Decouples business logic and HTTP routing from direct SQLAlchemy queries.
"""

from .base import BaseRepository
from .crop_repository import CropRepository
from .farm_repository import FarmRepository
from .scan_repository import ScanRepository
from .user_repository import UserRepository
from .weather_repository import WeatherRepository
from .report_repository import ReportRepository

__all__ = [
    "BaseRepository",
    "CropRepository",
    "FarmRepository",
    "ScanRepository",
    "UserRepository",
    "WeatherRepository",
    "ReportRepository",
]


