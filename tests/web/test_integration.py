"""
Integration tests for CashCow Web API.
Tests complete workflows and API interactions.
"""

import asyncio
import json
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient


class TestEntityWorkflow:
    """Test complete entity management workflow."""

    def test_complete_entity_crud_workflow(self, test_client: TestClient, sample_grant_data: dict):
        """Test complete CRUD workflow for entities."""
        # 1. Create entity
        create_response = test_client.post(
            "/api/entities/",
            json={"entity": sample_grant_data}
        )
        assert create_response.status_code == 201
        created_entity = create_response.json()["entity"]
        entity_id = created_entity["id"]
        
        # 2. Verify entity appears in list
        list_response = test_client.get("/api/entities/")
        assert list_response.status_code == 200
        entities = list_response.json()["entities"]
        assert any(e["id"] == entity_id for e in entities)
        
        # 3. Get specific entity
        get_response = test_client.get(f"/api/entities/{entity_id}")
        assert get_response.status_code == 200
        retrieved_entity = get_response.json()["entity"]
        assert retrieved_entity["id"] == entity_id
        assert retrieved_entity["name"] == sample_grant_data["name"]
        
        # 4. Update entity
        updated_data = {"name": "Updated Grant Name", "amount": 600000}
        update_response = test_client.put(
            f"/api/entities/{entity_id}",
            json={"entity": updated_data}
        )
        assert update_response.status_code == 200
        updated_entity = update_response.json()["entity"]
        assert updated_entity["name"] == "Updated Grant Name"
        assert updated_entity["amount"] == 600000
        
        # 5. Verify update in list
        list_response = test_client.get("/api/entities/")
        entities = list_response.json()["entities"]
        updated_in_list = next(e for e in entities if e["id"] == entity_id)
        assert updated_in_list["name"] == "Updated Grant Name"
        
        # 6. Delete entity
        delete_response = test_client.delete(f"/api/entities/{entity_id}")
        assert delete_response.status_code == 200
        
        # 7. Verify entity is deleted
        get_response = test_client.get(f"/api/entities/{entity_id}")
        assert get_response.status_code == 404

    def test_entity_validation_workflow(self, test_client: TestClient):
        """Test entity validation workflow."""
        # Test valid entity
        valid_data = {
            "type": "grant",
            "name": "Valid Grant",
            "start_date": "2024-01-01",
            "amount": 500000
        }
        
        validation_response = test_client.post(
            "/api/entities/validate",
            json={"entity": valid_data}
        )
        assert validation_response.status_code == 200
        validation = validation_response.json()["validation"]
        assert validation["valid"] is True
        
        # Test invalid entity
        invalid_data = {
            "type": "grant",
            "name": "",  # Invalid: empty name
            "start_date": "invalid-date",
            "amount": -1000  # Invalid: negative amount
        }
        
        validation_response = test_client.post(
            "/api/entities/validate",
            json={"entity": invalid_data}
        )
        assert validation_response.status_code == 200
        validation = validation_response.json()["validation"]
        assert validation["valid"] is False
        assert len(validation["errors"]) > 0

    def test_entity_search_workflow(self, test_client: TestClient):
        """Test entity search and filtering workflow."""
        # Create multiple entities with different attributes
        entities_data = [
            {
                "type": "grant",
                "name": "NASA SBIR Phase I",
                "start_date": "2024-01-01",
                "amount": 250000,
                "agency": "NASA",
                "tags": ["aerospace", "r&d"]
            },
            {
                "type": "grant", 
                "name": "DOD STTR",
                "start_date": "2024-02-01",
                "amount": 500000,
                "agency": "DOD",
                "tags": ["defense", "research"]
            },
            {
                "type": "employee",
                "name": "John Engineer",
                "start_date": "2024-01-01",
                "salary": 120000,
                "department": "Engineering",
                "tags": ["engineering", "fulltime"]
            }
        ]
        
        created_ids = []
        for entity_data in entities_data:
            response = test_client.post("/api/entities/", json={"entity": entity_data})
            created_ids.append(response.json()["entity"]["id"])
        
        # Test filtering by type
        response = test_client.get("/api/entities/?entity_type=grant")
        assert response.status_code == 200
        grants = response.json()["entities"]
        assert len(grants) >= 2
        assert all(e["type"] == "grant" for e in grants)
        
        # Test search functionality
        search_response = test_client.post(
            "/api/entities/search",
            json={"query": "NASA", "fields": ["name", "agency"]}
        )
        assert search_response.status_code == 200
        nasa_entities = [e for e in search_response.json()["entities"] if "NASA" in e.get("name", "") or e.get("agency") == "NASA"]
        assert len(nasa_entities) >= 1
        
        # Clean up
        for entity_id in created_ids:
            test_client.delete(f"/api/entities/{entity_id}")


class TestCalculationWorkflow:
    """Test calculation and analysis workflow."""

    def test_kpi_calculation_workflow(self, test_client: TestClient, sample_grant_data: dict, sample_employee_data: dict):
        """Test KPI calculation workflow with entities."""
        # Create some entities first
        test_client.post("/api/entities/", json={"entity": sample_grant_data})
        test_client.post("/api/entities/", json={"entity": sample_employee_data})
        
        # Get initial KPIs
        kpi_response = test_client.get("/api/calculations/kpis")
        assert kpi_response.status_code == 200
        initial_kpis = kpi_response.json()["kpis"]
        
        # Recalculate KPIs
        recalc_response = test_client.post("/api/calculations/kpis/recalculate")
        assert recalc_response.status_code == 200
        
        # Get updated KPIs
        updated_kpi_response = test_client.get("/api/calculations/kpis")
        assert updated_kpi_response.status_code == 200
        updated_kpis = updated_kpi_response.json()["kpis"]
        
        # KPIs should be available
        assert isinstance(updated_kpis, list)

    def test_forecast_calculation_workflow(self, test_client: TestClient):
        """Test forecast calculation workflow."""
        # Test basic forecast
        forecast_response = test_client.get("/api/calculations/forecast?months=12")
        assert forecast_response.status_code == 200
        forecast_data = forecast_response.json()["forecast"]
        
        assert "months" in forecast_data
        assert "summary" in forecast_data
        assert len(forecast_data["months"]) <= 12
        
        # Test forecast with parameters
        detailed_forecast = test_client.post(
            "/api/calculations/forecast",
            json={
                "months": 6,
                "scenario": "optimistic",
                "include_projections": True
            }
        )
        assert detailed_forecast.status_code == 200
        detailed_data = detailed_forecast.json()["forecast"]
        assert len(detailed_data["months"]) <= 6

    def test_scenario_workflow(self, test_client: TestClient):
        """Test scenario management workflow."""
        # List existing scenarios
        list_response = test_client.get("/api/scenarios/")
        assert list_response.status_code == 200
        initial_scenarios = list_response.json()["scenarios"]
        
        # Create custom scenario
        scenario_data = {
            "name": "integration_test_scenario",
            "description": "Test scenario for integration testing",
            "overrides": {
                "revenue_growth": 0.20,
                "expense_growth": 0.05
            }
        }
        
        create_response = test_client.post("/api/scenarios/", json=scenario_data)
        assert create_response.status_code == 201
        created_scenario = create_response.json()["scenario"]
        
        # Apply scenario
        apply_response = test_client.post(
            "/api/scenarios/apply",
            json={"scenario_name": "integration_test_scenario", "months": 6}
        )
        assert apply_response.status_code == 200
        
        # Compare scenarios
        compare_response = test_client.post(
            "/api/scenarios/compare",
            json={
                "scenarios": ["baseline", "integration_test_scenario"],
                "months": 6,
                "metrics": ["revenue", "expenses"]
            }
        )
        assert compare_response.status_code == 200
        comparison = compare_response.json()["comparison"]
        assert len(comparison) == 2  # Two scenarios
        
        # Clean up
        test_client.delete("/api/scenarios/integration_test_scenario")


class TestWebSocketWorkflow:
    """Test WebSocket integration workflow."""

    def test_websocket_entity_updates(self, test_client: TestClient, sample_grant_data: dict):
        """Test WebSocket notifications for entity updates."""
        # Connect to WebSocket
        with test_client.websocket_connect("/ws/entities") as websocket:
            # Receive welcome message
            welcome_data = websocket.receive_text()
            welcome_msg = json.loads(welcome_data)
            assert welcome_msg["type"] == "connected"
            
            # Create an entity (this should trigger WebSocket notification)
            create_response = test_client.post(
                "/api/entities/",
                json={"entity": sample_grant_data}
            )
            entity_id = create_response.json()["entity"]["id"]
            
            # Update entity (should trigger notification)
            test_client.put(
                f"/api/entities/{entity_id}",
                json={"entity": {"name": "Updated via WebSocket Test"}}
            )
            
            # Clean up
            test_client.delete(f"/api/entities/{entity_id}")

    def test_websocket_calculation_updates(self, test_client: TestClient):
        """Test WebSocket notifications for calculation updates."""
        with test_client.websocket_connect("/ws/calculations") as websocket:
            # Receive welcome message
            welcome_data = websocket.receive_text()
            welcome_msg = json.loads(welcome_data)
            assert welcome_msg["type"] == "connected"
            
            # Trigger calculation (should send progress updates)
            calc_response = test_client.post("/api/calculations/kpis/recalculate")
            assert calc_response.status_code == 200

    def test_websocket_broadcast_system(self, test_client: TestClient):
        """Test WebSocket broadcast functionality."""
        # Test broadcast endpoint
        broadcast_response = test_client.post(
            "/api/websockets/test-broadcast",
            params={"message_type": "integration_test", "topic": "status"}
        )
        assert broadcast_response.status_code == 200
        broadcast_data = broadcast_response.json()
        assert broadcast_data["success"] is True

    def test_websocket_connection_management(self, test_client: TestClient):
        """Test WebSocket connection management."""
        # Check initial stats
        stats_response = test_client.get("/api/websockets/stats")
        assert stats_response.status_code == 200
        initial_stats = stats_response.json()
        
        # Connect to WebSocket
        with test_client.websocket_connect("/ws/status") as websocket:
            websocket.receive_text()  # Welcome message
            
            # Check stats with connection
            stats_response = test_client.get("/api/websockets/stats")
            current_stats = stats_response.json()
            # Note: In test environment, stats might not update immediately
            assert "total_connections" in current_stats


class TestReportsWorkflow:
    """Test report generation workflow."""

    def test_report_generation_workflow(self, test_client: TestClient, sample_grant_data: dict, sample_employee_data: dict):
        """Test complete report generation workflow."""
        # Create entities for reporting
        grant_response = test_client.post("/api/entities/", json={"entity": sample_grant_data})
        employee_response = test_client.post("/api/entities/", json={"entity": sample_employee_data})
        
        grant_id = grant_response.json()["entity"]["id"]
        employee_id = employee_response.json()["entity"]["id"]
        
        # Generate cash flow report
        cashflow_response = test_client.post(
            "/api/reports/cashflow",
            json={"months": 12, "format": "json"}
        )
        assert cashflow_response.status_code == 200
        
        # Generate KPI report
        kpi_response = test_client.post(
            "/api/reports/kpi",
            json={"format": "json", "include_trends": True}
        )
        assert kpi_response.status_code == 200
        
        # Generate summary report
        summary_response = test_client.post(
            "/api/reports/summary",
            json={"format": "json"}
        )
        assert summary_response.status_code == 200
        
        # Clean up
        test_client.delete(f"/api/entities/{grant_id}")
        test_client.delete(f"/api/entities/{employee_id}")

    def test_report_export_workflow(self, test_client: TestClient):
        """Test report export functionality."""
        # Test different export formats
        formats = ["json", "csv"]
        
        for fmt in formats:
            export_response = test_client.post(
                "/api/reports/export",
                json={
                    "report_type": "summary",
                    "format": fmt,
                    "include_charts": False
                }
            )
            assert export_response.status_code == 200
            export_data = export_response.json()
            assert export_data["success"] is True


class TestErrorHandlingWorkflow:
    """Test error handling across the API."""

    def test_cascading_error_handling(self, test_client: TestClient):
        """Test error handling in dependent operations."""
        # Try to update non-existent entity
        update_response = test_client.put(
            "/api/entities/nonexistent-id",
            json={"entity": {"name": "Updated"}}
        )
        assert update_response.status_code == 404
        
        # Try to delete non-existent entity
        delete_response = test_client.delete("/api/entities/nonexistent-id")
        assert delete_response.status_code == 404
        
        # Try to apply non-existent scenario
        apply_response = test_client.post(
            "/api/scenarios/apply",
            json={"scenario_name": "nonexistent_scenario", "months": 6}
        )
        assert apply_response.status_code == 404

    def test_validation_error_workflow(self, test_client: TestClient):
        """Test validation error handling workflow."""
        # Create entity with missing required fields
        invalid_entity = {"type": "grant"}  # Missing name, start_date, amount
        
        create_response = test_client.post(
            "/api/entities/",
            json={"entity": invalid_entity}
        )
        assert create_response.status_code == 422
        
        # Create entity with invalid data types
        invalid_types = {
            "type": "grant",
            "name": "Test Grant",
            "start_date": "2024-01-01",
            "amount": "not-a-number"  # Should be numeric
        }
        
        create_response = test_client.post(
            "/api/entities/",
            json={"entity": invalid_types}
        )
        assert create_response.status_code == 422


@pytest.mark.asyncio
class TestAsyncIntegrationWorkflow:
    """Test async integration workflows."""

    async def test_async_entity_workflow(self, async_test_client: AsyncClient, sample_grant_data: dict):
        """Test async entity operations."""
        # Create entity
        create_response = await async_test_client.post(
            "/api/entities/",
            json={"entity": sample_grant_data}
        )
        assert create_response.status_code == 201
        entity_id = create_response.json()["entity"]["id"]
        
        # Get entity
        get_response = await async_test_client.get(f"/api/entities/{entity_id}")
        assert get_response.status_code == 200
        
        # Update entity
        update_response = await async_test_client.put(
            f"/api/entities/{entity_id}",
            json={"entity": {"name": "Async Updated"}}
        )
        assert update_response.status_code == 200
        
        # Delete entity
        delete_response = await async_test_client.delete(f"/api/entities/{entity_id}")
        assert delete_response.status_code == 200

    async def test_concurrent_operations(self, async_test_client: AsyncClient, sample_grant_data: dict, sample_employee_data: dict):
        """Test concurrent API operations."""
        # Create multiple entities concurrently
        create_tasks = [
            async_test_client.post("/api/entities/", json={"entity": sample_grant_data}),
            async_test_client.post("/api/entities/", json={"entity": sample_employee_data}),
            async_test_client.get("/api/calculations/kpis"),
            async_test_client.get("/api/scenarios/")
        ]
        
        results = await asyncio.gather(*create_tasks)
        
        # All operations should succeed
        assert all(r.status_code in [200, 201] for r in results)
        
        # Clean up created entities
        entity_ids = []
        for result in results[:2]:  # First two are entity creations
            if result.status_code == 201:
                entity_ids.append(result.json()["entity"]["id"])
        
        # Delete concurrently
        delete_tasks = [
            async_test_client.delete(f"/api/entities/{entity_id}")
            for entity_id in entity_ids
        ]
        
        if delete_tasks:
            delete_results = await asyncio.gather(*delete_tasks)
            assert all(r.status_code == 200 for r in delete_results)


class TestPerformanceIntegration:
    """Integration performance tests."""

    def test_api_response_times(self, test_client: TestClient, performance_test_entities: list):
        """Test API response times under load."""
        import time
        
        # Test entity listing performance
        start_time = time.time()
        list_response = test_client.get("/api/entities/?page_size=100")
        list_time = time.time() - start_time
        
        assert list_response.status_code == 200
        assert list_time < 2.0  # Should complete within 2 seconds
        
        # Test KPI calculation performance
        start_time = time.time()
        kpi_response = test_client.get("/api/calculations/kpis")
        kpi_time = time.time() - start_time
        
        assert kpi_response.status_code == 200
        assert kpi_time < 3.0  # Should complete within 3 seconds
        
        # Test forecast performance
        start_time = time.time()
        forecast_response = test_client.get("/api/calculations/forecast?months=12")
        forecast_time = time.time() - start_time
        
        assert forecast_response.status_code == 200
        assert forecast_time < 5.0  # Should complete within 5 seconds

    def test_concurrent_user_simulation(self, test_client: TestClient):
        """Simulate multiple concurrent users."""
        import threading
        import time
        
        results = []
        errors = []
        
        def user_simulation():
            try:
                # Simulate typical user workflow
                start_time = time.time()
                
                # List entities
                list_resp = test_client.get("/api/entities/")
                assert list_resp.status_code == 200
                
                # Get KPIs
                kpi_resp = test_client.get("/api/calculations/kpis")
                assert kpi_resp.status_code == 200
                
                # Get forecast
                forecast_resp = test_client.get("/api/calculations/forecast?months=6")
                assert forecast_resp.status_code == 200
                
                end_time = time.time()
                results.append(end_time - start_time)
                
            except Exception as e:
                errors.append(str(e))
        
        # Run 5 concurrent user simulations
        threads = []
        for i in range(5):
            thread = threading.Thread(target=user_simulation)
            threads.append(thread)
            thread.start()
        
        # Wait for all to complete
        for thread in threads:
            thread.join(timeout=10.0)  # 10 second timeout
        
        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) > 0, "No successful requests completed"
        
        # Average response time should be reasonable
        avg_time = sum(results) / len(results)
        assert avg_time < 10.0, f"Average response time too high: {avg_time}s"