"""
Tests for calculations and KPI API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient


class TestCalculationsEndpoints:
    """Test cases for calculations API."""

    def test_get_kpis(self, test_client: TestClient):
        """Test KPI retrieval endpoint."""
        response = test_client.get("/api/calculations/kpis")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "kpis" in data
        assert isinstance(data["kpis"], list)

    def test_get_kpis_with_category_filter(self, test_client: TestClient):
        """Test KPI retrieval with category filter."""
        response = test_client.get("/api/calculations/kpis?category=revenue")
        assert response.status_code == 200
        data = response.json()
        
        if data["kpis"]:  # If there are KPIs
            for kpi in data["kpis"]:
                # Check that if category is specified, it matches
                if "category" in kpi:
                    assert kpi["category"] == "revenue"

    def test_get_forecast(self, test_client: TestClient):
        """Test forecast calculation endpoint."""
        response = test_client.get("/api/calculations/forecast")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "forecast" in data
        
        forecast = data["forecast"]
        assert "months" in forecast
        assert "summary" in forecast
        assert isinstance(forecast["months"], list)

    def test_get_forecast_with_parameters(self, test_client: TestClient):
        """Test forecast with custom parameters."""
        params = {
            "months": 18,
            "scenario": "optimistic"
        }
        response = test_client.get("/api/calculations/forecast", params=params)
        assert response.status_code == 200
        data = response.json()
        
        forecast = data["forecast"]
        # Should have requested number of months or fewer
        assert len(forecast["months"]) <= 18

    def test_post_forecast_calculation(self, test_client: TestClient):
        """Test POST forecast calculation with parameters."""
        request_data = {
            "months": 12,
            "scenario": "baseline",
            "include_projections": True,
            "monte_carlo_iterations": 100
        }
        
        response = test_client.post("/api/calculations/forecast", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "forecast" in data

    def test_run_monte_carlo_analysis(self, test_client: TestClient):
        """Test Monte Carlo analysis endpoint."""
        request_data = {
            "iterations": 1000,
            "months": 12,
            "revenue_variance": 0.15,
            "expense_variance": 0.10
        }
        
        response = test_client.post("/api/calculations/monte-carlo", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "analysis" in data
        
        analysis = data["analysis"]
        assert "iterations" in analysis
        assert "percentiles" in analysis
        assert "statistics" in analysis

    def test_what_if_analysis(self, test_client: TestClient):
        """Test what-if scenario analysis."""
        request_data = {
            "scenario_name": "test_scenario",
            "changes": [
                {
                    "entity_type": "employee",
                    "field": "salary",
                    "change_type": "percentage",
                    "value": 0.10  # 10% increase
                }
            ],
            "months": 6
        }
        
        response = test_client.post("/api/calculations/what-if", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "analysis" in data

    def test_sensitivity_analysis(self, test_client: TestClient):
        """Test sensitivity analysis endpoint."""
        request_data = {
            "variable": "revenue_growth",
            "range_min": -0.20,
            "range_max": 0.30,
            "steps": 10,
            "months": 12
        }
        
        response = test_client.post("/api/calculations/sensitivity", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "analysis" in data

    def test_calculate_burn_rate(self, test_client: TestClient):
        """Test burn rate calculation."""
        response = test_client.get("/api/calculations/burn-rate")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "burn_rate" in data
        
        burn_rate = data["burn_rate"]
        assert "monthly_burn" in burn_rate
        assert "runway_months" in burn_rate
        assert isinstance(burn_rate["monthly_burn"], (int, float))

    def test_calculate_runway(self, test_client: TestClient):
        """Test runway calculation."""
        response = test_client.get("/api/calculations/runway")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "runway" in data

    def test_recalculate_all_kpis(self, test_client: TestClient):
        """Test KPI recalculation endpoint."""
        response = test_client.post("/api/calculations/kpis/recalculate")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data

    def test_get_calculation_history(self, test_client: TestClient):
        """Test calculation history endpoint."""
        response = test_client.get("/api/calculations/history")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "calculations" in data
        assert isinstance(data["calculations"], list)

    def test_get_kpi_trends(self, test_client: TestClient):
        """Test KPI trends analysis."""
        response = test_client.get("/api/calculations/kpis/trends?months=6")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "trends" in data


class TestScenarioEndpoints:
    """Test scenario management endpoints."""

    def test_list_scenarios(self, test_client: TestClient):
        """Test listing available scenarios."""
        response = test_client.get("/api/scenarios/")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "scenarios" in data
        assert isinstance(data["scenarios"], list)

    def test_get_scenario_by_name(self, test_client: TestClient):
        """Test retrieving a specific scenario."""
        response = test_client.get("/api/scenarios/baseline")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "scenario" in data

    def test_create_custom_scenario(self, test_client: TestClient):
        """Test creating a custom scenario."""
        scenario_data = {
            "name": "test_scenario",
            "description": "Test scenario for API testing",
            "overrides": {
                "revenue_growth": 0.15,
                "expense_growth": 0.05
            },
            "entity_modifications": []
        }
        
        response = test_client.post("/api/scenarios/", json=scenario_data)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "scenario" in data

    def test_update_scenario(self, test_client: TestClient):
        """Test updating an existing scenario."""
        # First create a scenario
        scenario_data = {
            "name": "update_test",
            "description": "Scenario for update testing",
            "overrides": {"revenue_growth": 0.10}
        }
        create_response = test_client.post("/api/scenarios/", json=scenario_data)
        assert create_response.status_code == 201

        # Then update it
        updated_data = {
            "description": "Updated description",
            "overrides": {"revenue_growth": 0.20}
        }
        response = test_client.put("/api/scenarios/update_test", json=updated_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_delete_scenario(self, test_client: TestClient):
        """Test deleting a custom scenario."""
        # Create scenario
        scenario_data = {
            "name": "delete_test",
            "description": "Scenario for deletion testing",
            "overrides": {}
        }
        test_client.post("/api/scenarios/", json=scenario_data)

        # Delete scenario
        response = test_client.delete("/api/scenarios/delete_test")
        assert response.status_code == 200
        
        # Verify it's deleted
        get_response = test_client.get("/api/scenarios/delete_test")
        assert get_response.status_code == 404

    def test_apply_scenario(self, test_client: TestClient):
        """Test applying a scenario to calculations."""
        request_data = {
            "scenario_name": "optimistic",
            "months": 12
        }
        
        response = test_client.post("/api/scenarios/apply", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_compare_scenarios(self, test_client: TestClient):
        """Test scenario comparison."""
        request_data = {
            "scenarios": ["baseline", "optimistic"],
            "months": 12,
            "metrics": ["revenue", "expenses", "cash_flow"]
        }
        
        response = test_client.post("/api/scenarios/compare", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "comparison" in data


class TestCalculationErrorHandling:
    """Test error handling in calculation endpoints."""

    def test_invalid_forecast_parameters(self, test_client: TestClient):
        """Test forecast with invalid parameters."""
        # Negative months
        response = test_client.get("/api/calculations/forecast?months=-1")
        assert response.status_code == 422

        # Too many months
        response = test_client.get("/api/calculations/forecast?months=1000")
        assert response.status_code == 422

    def test_invalid_monte_carlo_parameters(self, test_client: TestClient):
        """Test Monte Carlo with invalid parameters."""
        invalid_data = {
            "iterations": -100,  # Invalid: negative iterations
            "months": 0,  # Invalid: zero months
            "revenue_variance": 2.0  # Invalid: variance > 1
        }
        
        response = test_client.post("/api/calculations/monte-carlo", json=invalid_data)
        assert response.status_code == 422

    def test_nonexistent_scenario(self, test_client: TestClient):
        """Test applying a non-existent scenario."""
        response = test_client.get("/api/scenarios/nonexistent_scenario")
        assert response.status_code == 404

    def test_invalid_what_if_parameters(self, test_client: TestClient):
        """Test what-if analysis with invalid parameters."""
        invalid_data = {
            "scenario_name": "",  # Empty name
            "changes": [],  # Empty changes
            "months": 0  # Invalid months
        }
        
        response = test_client.post("/api/calculations/what-if", json=invalid_data)
        assert response.status_code == 422


@pytest.mark.asyncio
class TestAsyncCalculationEndpoints:
    """Test async calculation endpoints."""

    async def test_async_kpi_calculation(self, async_test_client: AsyncClient):
        """Test async KPI calculation."""
        response = await async_test_client.get("/api/calculations/kpis")
        assert response.status_code == 200
        data = response.json()
        assert "kpis" in data

    async def test_async_forecast_calculation(self, async_test_client: AsyncClient):
        """Test async forecast calculation."""
        response = await async_test_client.get("/api/calculations/forecast?months=6")
        assert response.status_code == 200
        data = response.json()
        assert "forecast" in data


class TestCalculationPerformance:
    """Performance tests for calculation endpoints."""

    def test_kpi_calculation_performance(self, test_client: TestClient):
        """Test KPI calculation performance."""
        import time
        
        start_time = time.time()
        response = test_client.get("/api/calculations/kpis")
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 3.0  # Should complete within 3 seconds

    def test_forecast_calculation_performance(self, test_client: TestClient):
        """Test forecast calculation performance."""
        import time
        
        start_time = time.time()
        response = test_client.get("/api/calculations/forecast?months=24")
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 5.0  # Should complete within 5 seconds

    def test_monte_carlo_performance(self, test_client: TestClient):
        """Test Monte Carlo analysis performance."""
        import time
        
        request_data = {
            "iterations": 100,  # Smaller number for performance test
            "months": 6,
            "revenue_variance": 0.10,
            "expense_variance": 0.05
        }
        
        start_time = time.time()
        response = test_client.post("/api/calculations/monte-carlo", json=request_data)
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 10.0  # Should complete within 10 seconds