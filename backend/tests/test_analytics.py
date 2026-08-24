"""
Tests for Analytics API Endpoints
"""

import pytest
from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


class TestAnalyticsEndpoints:
    """Test cases for analytics API endpoints"""

    def test_get_analytics_overview(self):
        """Test analytics overview endpoint"""
        response = client.get("/api/analytics/overview")

        assert response.status_code == 200
        data = response.json()
        assert "total_scripts" in data
        assert "total_claims" in data
        assert "verified_claims" in data
        assert "flagged_claims" in data
        assert "average_risk_score" in data
        assert "risk_distribution" in data
        assert "top_issues" in data

    def test_get_analytics_trends_week(self):
        """Test analytics trends endpoint with week timeframe"""
        response = client.get("/api/analytics/trends?timeframe=week")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

        for trend in data:
            assert "labels" in trend
            assert "values" in trend
            assert "metric" in trend

    def test_get_analytics_trends_month(self):
        """Test analytics trends endpoint with month timeframe"""
        response = client.get("/api/analytics/trends?timeframe=month")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_comparative_analysis(self):
        """Test comparative analysis endpoint"""
        response = client.get("/api/analytics/comparative?timeframe=month")

        assert response.status_code == 200
        data = response.json()
        assert "period" in data
        assert "current_scripts" in data
        assert "previous_scripts" in data
        assert "current_avg_risk" in data
        assert "previous_avg_risk" in data
        assert "risk_trend" in data
        assert data["risk_trend"] in ["improving", "worsening", "stable"]

    def test_get_project_comparison(self):
        """Test project comparison endpoint"""
        response = client.get("/api/analytics/projects?limit=5&sort_by=risk_score")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5

        for project in data:
            assert "project_id" in project
            assert "title" in project
            assert "risk_score" in project
            assert "claims_count" in project
            assert "status" in project

    def test_generate_analytics_report(self):
        """Test full analytics report generation"""
        response = client.get("/api/analytics/report?timeframe=month")

        assert response.status_code == 200
        data = response.json()
        assert "generated_at" in data
        assert "timeframe" in data
        assert "overview" in data
        assert "risk_trend" in data
        assert "scripts_trend" in data
        assert "comparative" in data
        assert "top_projects" in data
        assert "insights" in data
        assert isinstance(data["insights"], list)

    def test_get_performance_metrics(self):
        """Test performance metrics endpoint"""
        response = client.get("/api/analytics/performance")

        assert response.status_code == 200
        data = response.json()
        assert "api_calls_today" in data
        assert "average_response_time_ms" in data
        assert "uptime_percentage" in data
        assert "success_rate" in data

    def test_invalid_timeframe(self):
        """Test analytics trends with invalid timeframe"""
        response = client.get("/api/analytics/trends?timeframe=invalid")

        assert response.status_code == 422  # Validation error


class TestHealthEndpoint:
    """Test cases for health check endpoint"""

    def test_health_check(self):
        """Test health endpoint"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Greenlit AI Backend"
        assert "version" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
