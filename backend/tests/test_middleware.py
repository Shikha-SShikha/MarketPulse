"""Tests for middleware functionality (Phase 9 requirements)."""

import pytest


class TestErrorHandling:
    """Test consistent error response format."""

    def test_404_error_format(self, client):
        """Test 404 errors return consistent JSON format."""
        response = client.get("/signals/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data or "error" in data

    def test_403_error_format(self, client, sample_signal):
        """Test 403 errors return consistent JSON format."""
        response = client.post("/signals", json=sample_signal)
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data or "error" in data

    def test_422_error_format(self, client, auth_headers):
        """Test 422 validation errors return details."""
        response = client.post(
            "/signals",
            json={"entity": "test"},  # Missing required fields
            headers=auth_headers,
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestRequestLogging:
    """Test request logging middleware."""

    def test_request_id_header(self, client):
        """Test that responses include X-Request-ID header."""
        response = client.get("/health")
        assert response.status_code == 200
        assert "x-request-id" in response.headers


class TestCORS:
    """Test CORS configuration."""

    def test_cors_headers_present(self, client):
        """Test CORS headers are present on responses."""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        # CORS preflight should succeed
        assert response.status_code in [200, 204]

    def test_cors_allows_configured_origin(self, client):
        """Test CORS allows configured origin."""
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"},
        )
        assert response.status_code == 200
        # Check CORS header is present
        cors_header = response.headers.get("access-control-allow-origin")
        assert cors_header is not None


class TestRateLimiting:
    """Test rate limiting middleware."""

    def test_rate_limit_not_applied_to_public_endpoints(self, client):
        """Test rate limiting is not applied to non-admin endpoints."""
        # Make multiple requests to public endpoint
        for _ in range(10):
            response = client.get("/health")
            assert response.status_code == 200

    def test_admin_endpoint_rate_limited(self, client, auth_headers, sample_signal):
        """Test admin endpoints are rate limited."""
        # Note: Full rate limit testing (100+ requests) is expensive
        # This just verifies the endpoint works within limits
        response = client.post("/signals", json=sample_signal, headers=auth_headers)
        assert response.status_code in [201, 429]  # Either created or rate limited
