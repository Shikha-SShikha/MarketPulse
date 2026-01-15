"""Tests for signal endpoints."""

import pytest


class TestSignalEndpoints:
    """Test signal CRUD operations."""

    def test_health_check(self, client):
        """Test health endpoint returns ok."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_create_signal_success(self, client, auth_headers, sample_signal):
        """Test creating a valid signal."""
        response = client.post("/signals", json=sample_signal, headers=auth_headers)
        assert response.status_code == 201

        data = response.json()
        assert data["entity"] == sample_signal["entity"]
        assert data["topic"] == sample_signal["topic"]
        assert data["confidence"] == sample_signal["confidence"]
        assert "id" in data
        assert "created_at" in data

    def test_create_signal_unauthorized(self, client, sample_signal):
        """Test creating signal without auth token fails."""
        response = client.post("/signals", json=sample_signal)
        assert response.status_code == 403

    def test_create_signal_invalid_token(self, client, sample_signal):
        """Test creating signal with invalid token fails."""
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.post("/signals", json=sample_signal, headers=headers)
        assert response.status_code == 403

    def test_create_signal_invalid_url(self, client, auth_headers, sample_signal):
        """Test creating signal with invalid URL fails."""
        sample_signal["source_url"] = "not-a-url"
        response = client.post("/signals", json=sample_signal, headers=auth_headers)
        assert response.status_code == 422

    def test_create_signal_missing_field(self, client, auth_headers):
        """Test creating signal with missing required field fails."""
        incomplete_signal = {
            "entity": "Test",
            "event_type": "announcement",
        }
        response = client.post("/signals", json=incomplete_signal, headers=auth_headers)
        assert response.status_code == 422

    def test_create_signal_short_evidence(self, client, auth_headers, sample_signal):
        """Test creating signal with too short evidence fails."""
        sample_signal["evidence_snippet"] = "Too short"
        response = client.post("/signals", json=sample_signal, headers=auth_headers)
        assert response.status_code == 422

    def test_create_signal_invalid_event_type(self, client, auth_headers, sample_signal):
        """Test creating signal with invalid event type fails."""
        sample_signal["event_type"] = "invalid_type"
        response = client.post("/signals", json=sample_signal, headers=auth_headers)
        assert response.status_code == 422

    def test_create_signal_invalid_confidence(self, client, auth_headers, sample_signal):
        """Test creating signal with invalid confidence fails."""
        sample_signal["confidence"] = "Invalid"
        response = client.post("/signals", json=sample_signal, headers=auth_headers)
        assert response.status_code == 422

    def test_create_signal_empty_impact_areas(self, client, auth_headers, sample_signal):
        """Test creating signal with empty impact areas fails."""
        sample_signal["impact_areas"] = []
        response = client.post("/signals", json=sample_signal, headers=auth_headers)
        assert response.status_code == 422

    def test_list_signals_empty(self, client):
        """Test listing signals when none exist."""
        response = client.get("/signals")
        assert response.status_code == 200

        data = response.json()
        assert data["signals"] == []
        assert data["total"] == 0

    def test_list_signals_after_create(self, client, auth_headers, sample_signal):
        """Test listing signals after creating one."""
        # Create a signal
        client.post("/signals", json=sample_signal, headers=auth_headers)

        # List signals
        response = client.get("/signals")
        assert response.status_code == 200

        data = response.json()
        assert len(data["signals"]) == 1
        assert data["total"] == 1

    def test_list_signals_filter_by_entity(self, client, auth_headers, sample_signal):
        """Test filtering signals by entity."""
        # Create signals
        client.post("/signals", json=sample_signal, headers=auth_headers)

        sample_signal["entity"] = "Other Publisher"
        client.post("/signals", json=sample_signal, headers=auth_headers)

        # Filter by entity
        response = client.get("/signals?entity=Test")
        data = response.json()
        assert len(data["signals"]) == 1
        assert data["signals"][0]["entity"] == "Test Publisher"

    def test_get_signal_by_id(self, client, auth_headers, sample_signal):
        """Test getting a single signal by ID."""
        # Create a signal
        create_response = client.post("/signals", json=sample_signal, headers=auth_headers)
        signal_id = create_response.json()["id"]

        # Get signal
        response = client.get(f"/signals/{signal_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == signal_id
        assert data["entity"] == sample_signal["entity"]

    def test_get_signal_not_found(self, client):
        """Test getting non-existent signal returns 404."""
        response = client.get("/signals/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404

    def test_delete_signal(self, client, auth_headers, sample_signal):
        """Test soft deleting a signal."""
        # Create a signal
        create_response = client.post("/signals", json=sample_signal, headers=auth_headers)
        signal_id = create_response.json()["id"]

        # Delete signal
        response = client.delete(f"/signals/{signal_id}", headers=auth_headers)
        assert response.status_code == 204

        # Verify signal is no longer in list
        list_response = client.get("/signals")
        assert list_response.json()["total"] == 0

    def test_delete_signal_unauthorized(self, client, auth_headers, sample_signal):
        """Test deleting signal without auth fails."""
        # Create a signal
        create_response = client.post("/signals", json=sample_signal, headers=auth_headers)
        signal_id = create_response.json()["id"]

        # Try to delete without auth
        response = client.delete(f"/signals/{signal_id}")
        assert response.status_code == 403

    def test_delete_signal_not_found(self, client, auth_headers):
        """Test deleting non-existent signal returns 404."""
        response = client.delete(
            "/signals/00000000-0000-0000-0000-000000000000",
            headers=auth_headers
        )
        assert response.status_code == 404
