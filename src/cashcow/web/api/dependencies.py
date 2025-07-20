"""
CashCow Web API - Dependency injection providers.
"""

import os
from pathlib import Path
from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status
from cashcow.storage.yaml_loader import YamlEntityLoader
from cashcow.storage.database import EntityStore
from cashcow.engine.cashflow import CashFlowEngine
from cashcow.engine.kpis import KPICalculator

# Import authentication system
from .auth import get_current_user as auth_get_current_user, TokenData, require_permission, Permission


def get_entity_loader():
    """
    Dependency to provide entity loader for API endpoints.
    
    Returns:
        YamlEntityLoader instance
    """
    # Get entities directory path (default to current working directory + entities)
    entities_dir = os.environ.get('CASHCOW_ENTITIES_DIR', './entities')
    entities_path = Path(entities_dir)
    
    # Create directory if it doesn't exist
    entities_path.mkdir(exist_ok=True)
    
    return YamlEntityLoader(entities_path)


# Global instances for singleton dependencies
_entity_store: Optional[EntityStore] = None
_cash_flow_engine: Optional[CashFlowEngine] = None
_kpi_calculator: Optional[KPICalculator] = None


def get_store() -> EntityStore:
    """
    Dependency to provide entity store for API endpoints.
    
    Returns:
        EntityStore instance
    """
    global _entity_store
    if _entity_store is None:
        # Initialize with default database path
        db_path = os.environ.get('CASHCOW_DB_PATH', 'cashcow.db')
        _entity_store = EntityStore(db_path)
    return _entity_store


def get_engine() -> CashFlowEngine:
    """
    Dependency to provide cash flow engine for API endpoints.
    
    Returns:
        CashFlowEngine instance
    """
    global _cash_flow_engine
    if _cash_flow_engine is None:
        # Initialize cash flow engine
        _cash_flow_engine = CashFlowEngine()
    return _cash_flow_engine


def get_kpi_calculator() -> KPICalculator:
    """
    Dependency to provide KPI calculator for API endpoints.
    
    Returns:
        KPICalculator instance
    """
    global _kpi_calculator
    if _kpi_calculator is None:
        # Initialize KPI calculator
        _kpi_calculator = KPICalculator()
    return _kpi_calculator


# Authentication dependencies that can be used by other routers
def get_current_user():
    """
    Development version that bypasses authentication for testing.
    In production, this should use the real authentication system.
    """
    # For development, return a mock user
    if os.environ.get("DEVELOPMENT_MODE", "true").lower() == "true":
        return {
            "user_id": "dev-user",
            "username": "developer",
            "permissions": ["READ_ENTITIES", "WRITE_ENTITIES", "DELETE_ENTITIES", "READ_REPORTS", "RUN_CALCULATIONS"],
            "is_admin": True
        }
    else:
        # Use real authentication in production
        return auth_get_current_user()

def require_entity_read():
    """Dependency for entity read access."""
    return require_permission(Permission.READ_ENTITIES)

def require_entity_write():
    """Dependency for entity write access.""" 
    return require_permission(Permission.WRITE_ENTITIES)

def require_entity_delete():
    """Dependency for entity delete access."""
    return require_permission(Permission.DELETE_ENTITIES)

def require_report_access():
    """Dependency for report access."""
    return require_permission(Permission.READ_REPORTS)

def require_calculation_access():
    """Dependency for calculation access."""
    return require_permission(Permission.RUN_CALCULATIONS)