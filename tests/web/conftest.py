"""
Test configuration for CashCow Web API tests.
"""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Import the web application
from cashcow.web.api import create_app
from cashcow.web.api.main import app as main_app
from cashcow.storage.yaml_loader import YamlEntityLoader
from cashcow.models import create_entity


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_entities_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test entities."""
    with tempfile.TemporaryDirectory() as temp_dir:
        entities_path = Path(temp_dir)
        
        # Create subdirectories for entity types
        for category in ["revenue", "expenses", "projects"]:
            (entities_path / category).mkdir(exist_ok=True)
            
        for entity_type in ["grants", "investments", "sales", "services"]:
            (entities_path / "revenue" / entity_type).mkdir(exist_ok=True)
            
        for entity_type in ["employees", "facilities", "operations", "software", "equipment"]:
            (entities_path / "expenses" / entity_type).mkdir(exist_ok=True)
            
        yield entities_path


@pytest.fixture
def sample_entities(temp_entities_dir: Path) -> dict:
    """Create sample entities for testing."""
    loader = YamlEntityLoader(temp_entities_dir)
    
    # Create sample entities
    entities = {}
    
    # Grant entity
    grant = create_entity({
        'type': 'grant',
        'name': 'Test NASA SBIR',
        'start_date': '2024-01-01',
        'amount': 500000,
        'agency': 'NASA',
        'program': 'SBIR',
        'tags': ['test', 'grant']
    })
    entities['grant'] = loader.save_entity(grant)
    
    # Employee entity
    employee = create_entity({
        'type': 'employee',
        'name': 'Test Engineer',
        'start_date': '2024-01-01',
        'salary': 100000,
        'position': 'Software Engineer',
        'department': 'Engineering',
        'tags': ['test', 'employee']
    })
    entities['employee'] = loader.save_entity(employee)
    
    # Investment entity
    investment = create_entity({
        'type': 'investment',
        'name': 'Test Series A',
        'start_date': '2024-02-01',
        'amount': 1000000,
        'investor': 'Test Ventures',
        'round_type': 'series_a',
        'tags': ['test', 'investment']
    })
    entities['investment'] = loader.save_entity(investment)
    
    return entities


@pytest.fixture
def test_app():
    """Create a test FastAPI application."""
    # Set test environment variables
    os.environ["DEVELOPMENT_MODE"] = "true"
    os.environ["CASHCOW_ENTITIES_DIR"] = "./test_entities"
    
    # Use the main app which includes all routes
    from cashcow.web.api.main import app
    return app


@pytest.fixture
def test_client(test_app) -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI application."""
    with TestClient(test_app) as client:
        yield client


@pytest_asyncio.fixture
async def async_test_client(test_app) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for the FastAPI application."""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        yield client


@pytest.fixture
def auth_headers() -> dict:
    """Create authentication headers for test requests."""
    return {
        "Authorization": "Bearer test-token",
        "Content-Type": "application/json"
    }


@pytest.fixture
def mock_user() -> dict:
    """Create a mock user for testing."""
    return {
        "user_id": "test-user-123",
        "username": "testuser",
        "permissions": [
            "READ_ENTITIES",
            "WRITE_ENTITIES", 
            "DELETE_ENTITIES",
            "READ_REPORTS",
            "RUN_CALCULATIONS"
        ],
        "is_admin": True
    }


# Test data fixtures
@pytest.fixture
def sample_grant_data() -> dict:
    """Sample grant entity data for testing."""
    return {
        "type": "grant",
        "name": "Test Grant API",
        "start_date": "2024-01-01",
        "amount": 750000,
        "agency": "NASA",
        "program": "SBIR",
        "grant_number": "TEST123",
        "indirect_cost_rate": 0.25,
        "tags": ["api-test", "grant"]
    }


@pytest.fixture
def sample_employee_data() -> dict:
    """Sample employee entity data for testing."""
    return {
        "type": "employee",
        "name": "Test Employee API",
        "start_date": "2024-01-01",
        "salary": 120000,
        "position": "Senior Engineer",
        "department": "Engineering",
        "overhead_multiplier": 1.4,
        "equity_eligible": True,
        "tags": ["api-test", "employee"]
    }


@pytest.fixture
def sample_kpi_data() -> list:
    """Sample KPI data for testing."""
    return [
        {
            "name": "Total Revenue",
            "value": 1500000,
            "unit": "$",
            "category": "revenue",
            "trend": "up",
            "change": 0.15
        },
        {
            "name": "Monthly Burn Rate",
            "value": 85000,
            "unit": "$/month",
            "category": "cash_flow",
            "trend": "down",
            "change": -0.08
        },
        {
            "name": "Employee Count",
            "value": 12,
            "unit": "count",
            "category": "operations",
            "trend": "up",
            "change": 0.20
        }
    ]


@pytest.fixture
def sample_forecast_data() -> dict:
    """Sample forecast data for testing."""
    return {
        "months": [
            {
                "month": "2024-01",
                "revenue": 100000,
                "expenses": 120000,
                "net_cash_flow": -20000,
                "cumulative_cash_flow": -20000,
                "burn_rate": 20000
            },
            {
                "month": "2024-02",
                "revenue": 110000,
                "expenses": 125000,
                "net_cash_flow": -15000,
                "cumulative_cash_flow": -35000,
                "burn_rate": 15000
            },
            {
                "month": "2024-03",
                "revenue": 150000,
                "expenses": 130000,
                "net_cash_flow": 20000,
                "cumulative_cash_flow": -15000,
                "burn_rate": 0
            }
        ],
        "summary": {
            "total_revenue": 360000,
            "total_expenses": 375000,
            "net_cash_flow": -15000,
            "average_burn_rate": 11667,
            "runway_months": 18
        }
    }


# Performance test helpers
@pytest.fixture
def performance_test_entities(temp_entities_dir: Path) -> list:
    """Create multiple entities for performance testing."""
    loader = YamlEntityLoader(temp_entities_dir)
    entities = []
    
    # Create 50 test entities
    for i in range(50):
        entity = create_entity({
            'type': 'employee',
            'name': f'Performance Test Employee {i}',
            'start_date': '2024-01-01',
            'salary': 80000 + (i * 1000),
            'position': f'Engineer {i}',
            'department': 'Engineering',
            'tags': ['performance-test']
        })
        saved_entity = loader.save_entity(entity)
        entities.append(saved_entity)
    
    return entities