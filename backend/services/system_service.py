"""
backend/services/system_service.py
==================================
System service for connection diagnostics and database status verification.
"""

from typing import Dict, Any
from database import check_db_connection


class SystemService:
    @staticmethod
    async def get_database_status() -> Dict[str, Any]:
        """
        Check connectivity to the PostgreSQL database and return health metrics.
        """
        return await check_db_connection()
