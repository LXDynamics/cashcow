"""
Tests for entity management API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient


class TestEntityEndpoints:
    """Test cases for entity CRUD operations."""

    def test_health_check(self, test_client: TestClient):
        """Test the health check endpoint."""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "cashcow-api"

    def test_api_root(self, test_client: TestClient):
        """Test the API root endpoint."""
        response = test_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "CashCow API"
        assert "api_endpoints" in data
        assert "websockets" in data

    def test_list_entities_empty(self, test_client: TestClient):
        """Test listing entities when none exist."""
        response = test_client.get("/api/entities/")
        assert response.status_code == 200
        data = response.json()
        assert "entities" in data
        assert isinstance(data["entities"], list)
        assert data["total"] >= 0

    def test_create_grant_entity(self, test_client: TestClient, sample_grant_data: dict):
        """Test creating a grant entity."""
        response = test_client.post(
            "/api/entities/",
            json={"entity": sample_grant_data}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "entity" in data
        
        entity = data["entity"]
        assert entity["type"] == "grant"
        assert entity["name"] == sample_grant_data["name"]
        assert entity["amount"] == sample_grant_data["amount"]
        assert "id" in entity

    def test_create_employee_entity(self, test_client: TestClient, sample_employee_data: dict):
        """Test creating an employee entity."""
        response = test_client.post(
            "/api/entities/",
            json={"entity": sample_employee_data}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        
        entity = data["entity"]
        assert entity["type"] == "employee"
        assert entity["name"] == sample_employee_data["name"]
        assert entity["salary"] == sample_employee_data["salary"]

    def test_get_entity_by_id(self, test_client: TestClient, sample_grant_data: dict):
        """Test retrieving a specific entity by ID."""
        # First create an entity
        create_response = test_client.post(
            "/api/entities/",
            json={"entity": sample_grant_data}
        )
        assert create_response.status_code == 201
        created_entity = create_response.json()["entity"]
        entity_id = created_entity["id"]

        # Then retrieve it
        get_response = test_client.get(f"/api/entities/{entity_id}")
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["success"] is True
        
        entity = data["entity"]
        assert entity["id"] == entity_id
        assert entity["name"] == sample_grant_data["name"]

    def test_update_entity(self, test_client: TestClient, sample_grant_data: dict):
        """Test updating an existing entity."""
        # Create entity
        create_response = test_client.post(
            "/api/entities/",
            json={"entity": sample_grant_data}
        )
        entity_id = create_response.json()["entity"]["id"]

        # Update entity
        updated_data = {"name": "Updated Grant Name", "amount": 600000}
        update_response = test_client.put(
            f"/api/entities/{entity_id}",
            json={"entity": updated_data}
        )
        assert update_response.status_code == 200
        
        updated_entity = update_response.json()["entity"]
        assert updated_entity["name"] == "Updated Grant Name"
        assert updated_entity["amount"] == 600000

    def test_delete_entity(self, test_client: TestClient, sample_grant_data: dict):
        """Test deleting an entity."""
        # Create entity
        create_response = test_client.post(
            "/api/entities/",
            json={"entity": sample_grant_data}
        )
        entity_id = create_response.json()["entity"]["id"]

        # Delete entity
        delete_response = test_client.delete(f"/api/entities/{entity_id}")
        assert delete_response.status_code == 200
        
        # Verify it's deleted
        get_response = test_client.get(f"/api/entities/{entity_id}")
        assert get_response.status_code == 404

    def test_list_entities_with_filters(self, test_client: TestClient, sample_grant_data: dict, sample_employee_data: dict):
        """Test listing entities with type filter."""
        # Create different types of entities
        test_client.post("/api/entities/", json={"entity": sample_grant_data})
        test_client.post("/api/entities/", json={"entity": sample_employee_data})

        # Filter by type
        response = test_client.get("/api/entities/?entity_type=grant")
        assert response.status_code == 200
        data = response.json()
        
        for entity in data["entities"]:
            assert entity["type"] == "grant"

    def test_list_entities_pagination(self, test_client: TestClient):
        """Test entity listing with pagination."""
        response = test_client.get("/api/entities/?page=1&page_size=5")
        assert response.status_code == 200
        data = response.json()
        
        assert "entities" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert data["page"] == 1
        assert data["per_page"] == 5

    def test_validate_entity(self, test_client: TestClient, sample_grant_data: dict):
        """Test entity validation endpoint."""
        response = test_client.post(
            "/api/entities/validate",
            json={"entity": sample_grant_data}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "validation" in data
        assert data["validation"]["valid"] is True

    def test_validate_invalid_entity(self, test_client: TestClient):
        """Test validation of invalid entity data."""
        invalid_data = {
            "type": "grant",
            "name": "",  # Invalid: empty name
            "start_date": "invalid-date",  # Invalid date format
            "amount": -1000  # Invalid: negative amount
        }
        
        response = test_client.post(
            "/api/entities/validate",
            json={"entity": invalid_data}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        validation = data["validation"]
        assert validation["valid"] is False
        assert len(validation["errors"]) > 0

    def test_bulk_delete_entities(self, test_client: TestClient, sample_grant_data: dict, sample_employee_data: dict):
        """Test bulk deletion of entities."""
        # Create multiple entities
        grant_response = test_client.post("/api/entities/", json={"entity": sample_grant_data})
        employee_response = test_client.post("/api/entities/", json={"entity": sample_employee_data})
        
        grant_id = grant_response.json()["entity"]["id"]
        employee_id = employee_response.json()["entity"]["id"]

        # Bulk delete
        response = test_client.post(
            "/api/entities/bulk-delete",
            json={"ids": [grant_id, employee_id]}
        )
        assert response.status_code == 200
        
        # Verify entities are deleted
        assert test_client.get(f"/api/entities/{grant_id}").status_code == 404
        assert test_client.get(f"/api/entities/{employee_id}").status_code == 404

    def test_entity_types_endpoint(self, test_client: TestClient):
        """Test the entity types information endpoint."""
        response = test_client.get("/api/entities/types")
        assert response.status_code == 200
        data = response.json()
        
        assert "entity_types" in data
        assert isinstance(data["entity_types"], list)
        assert len(data["entity_types"]) > 0
        
        # Check structure of entity type info
        entity_type = data["entity_types"][0]
        assert "name" in entity_type
        assert "category" in entity_type
        assert "required_fields" in entity_type

    def test_search_entities(self, test_client: TestClient, sample_grant_data: dict):
        """Test entity search functionality."""
        # Create entity with searchable content
        searchable_data = sample_grant_data.copy()
        searchable_data["name"] = "Searchable NASA Grant"
        searchable_data["notes"] = "This is a test grant for searching"
        
        test_client.post("/api/entities/", json={"entity": searchable_data})

        # Search by name
        response = test_client.post(
            "/api/entities/search",
            json={"query": "Searchable", "fields": ["name", "notes"]}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "entities" in data
        found_entities = [e for e in data["entities"] if "Searchable" in e["name"]]
        assert len(found_entities) > 0

    def test_entity_statistics(self, test_client: TestClient, sample_grant_data: dict, sample_employee_data: dict):
        """Test entity statistics endpoint."""
        # Create some entities
        test_client.post("/api/entities/", json={"entity": sample_grant_data})
        test_client.post("/api/entities/", json={"entity": sample_employee_data})

        response = test_client.get("/api/entities/statistics")
        assert response.status_code == 200
        data = response.json()
        
        assert "total_entities" in data
        assert "by_type" in data
        assert "by_category" in data
        assert isinstance(data["total_entities"], int)
        assert isinstance(data["by_type"], dict)


class TestEntityErrorHandling:
    """Test error handling in entity endpoints."""

    def test_get_nonexistent_entity(self, test_client: TestClient):
        """Test getting an entity that doesn't exist."""
        response = test_client.get("/api/entities/nonexistent-id")
        assert response.status_code == 404

    def test_update_nonexistent_entity(self, test_client: TestClient):
        """Test updating an entity that doesn't exist."""
        response = test_client.put(
            "/api/entities/nonexistent-id",
            json={"entity": {"name": "Updated"}}
        )
        assert response.status_code == 404

    def test_delete_nonexistent_entity(self, test_client: TestClient):
        """Test deleting an entity that doesn't exist."""
        response = test_client.delete("/api/entities/nonexistent-id")
        assert response.status_code == 404

    def test_create_entity_missing_required_fields(self, test_client: TestClient):
        """Test creating entity with missing required fields."""
        invalid_data = {
            "type": "grant"
            # Missing name, start_date, amount
        }
        
        response = test_client.post(
            "/api/entities/",
            json={"entity": invalid_data}
        )
        assert response.status_code == 422  # Validation error

    def test_create_entity_invalid_type(self, test_client: TestClient):
        """Test creating entity with invalid type."""
        invalid_data = {
            "type": "invalid_type",
            "name": "Test Entity",
            "start_date": "2024-01-01"
        }
        
        response = test_client.post(
            "/api/entities/",
            json={"entity": invalid_data}
        )
        assert response.status_code == 422

    def test_malformed_json_request(self, test_client: TestClient):
        """Test handling of malformed JSON requests."""
        response = test_client.post(
            "/api/entities/",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_invalid_pagination_parameters(self, test_client: TestClient):
        """Test invalid pagination parameters."""
        # Negative page
        response = test_client.get("/api/entities/?page=-1")
        assert response.status_code == 422
        
        # Zero page size
        response = test_client.get("/api/entities/?page_size=0")
        assert response.status_code == 422
        
        # Oversized page
        response = test_client.get("/api/entities/?page_size=1000")
        assert response.status_code == 422


@pytest.mark.asyncio
class TestAsyncEntityEndpoints:
    """Test async versions of entity endpoints."""

    async def test_async_list_entities(self, async_test_client: AsyncClient):
        """Test async entity listing."""
        response = await async_test_client.get("/api/entities/")
        assert response.status_code == 200
        data = response.json()
        assert "entities" in data

    async def test_async_create_entity(self, async_test_client: AsyncClient, sample_grant_data: dict):
        """Test async entity creation."""
        response = await async_test_client.post(
            "/api/entities/",
            json={"entity": sample_grant_data}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True


class TestEntityPerformance:
    """Performance tests for entity endpoints."""

    def test_list_many_entities_performance(self, test_client: TestClient, performance_test_entities: list):
        """Test performance when listing many entities."""
        import time
        
        start_time = time.time()
        response = test_client.get("/api/entities/?page_size=100")
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 2.0  # Should complete within 2 seconds

    def test_bulk_operations_performance(self, test_client: TestClient, performance_test_entities: list):
        """Test performance of bulk operations."""
        entity_ids = [entity.id for entity in performance_test_entities[:10]]
        
        import time
        start_time = time.time()
        response = test_client.post(
            "/api/entities/bulk-delete",
            json={"ids": entity_ids}
        )
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 5.0  # Should complete within 5 seconds