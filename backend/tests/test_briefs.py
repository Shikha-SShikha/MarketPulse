"""Tests for brief generation and endpoints."""

import pytest
from datetime import date


class TestBriefEndpoints:
    """Test brief retrieval endpoints."""

    def test_get_current_brief_empty(self, client):
        """Test getting current brief when none exists."""
        response = client.get("/briefs/current")
        # Should return 204 No Content when no brief exists
        assert response.status_code == 204

    def test_get_brief_not_found(self, client):
        """Test getting non-existent brief returns 404."""
        response = client.get("/briefs/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404

    def test_generate_brief_no_signals(self, client, auth_headers):
        """Test generating brief with no signals."""
        response = client.post("/admin/generate-brief", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "No signals found" in data["message"]
        assert data["themes_created"] == 0

    def test_generate_brief_with_signals(self, client, auth_headers, sample_signal):
        """Test generating brief with signals."""
        # Create signals
        client.post("/signals", json=sample_signal, headers=auth_headers)

        sample_signal["entity"] = "Another Publisher"
        sample_signal["topic"] = "Different Topic"
        client.post("/signals", json=sample_signal, headers=auth_headers)

        # Generate brief
        response = client.post("/admin/generate-brief", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["signals_processed"] == 2
        assert data["themes_created"] >= 1
        assert data["brief_id"] is not None

    def test_generate_brief_idempotent(self, client, auth_headers, sample_signal):
        """Test that generating brief twice returns same brief."""
        # Create a signal
        client.post("/signals", json=sample_signal, headers=auth_headers)

        # Generate brief twice
        response1 = client.post("/admin/generate-brief", headers=auth_headers)
        response2 = client.post("/admin/generate-brief", headers=auth_headers)

        # Should return same brief ID
        assert response1.json()["brief_id"] == response2.json()["brief_id"]

    def test_generate_brief_unauthorized(self, client):
        """Test generating brief without auth fails."""
        response = client.post("/admin/generate-brief")
        assert response.status_code == 403

    def test_get_current_brief_after_generate(self, client, auth_headers, sample_signal):
        """Test getting current brief after generation."""
        # Create signal and generate brief
        client.post("/signals", json=sample_signal, headers=auth_headers)
        gen_response = client.post("/admin/generate-brief", headers=auth_headers)
        brief_id = gen_response.json()["brief_id"]

        # Get current brief
        response = client.get("/briefs/current")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == brief_id
        assert len(data["themes"]) >= 1
        assert "week_start" in data
        assert "week_end" in data

    def test_get_brief_by_id(self, client, auth_headers, sample_signal):
        """Test getting brief by specific ID."""
        # Create signal and generate brief
        client.post("/signals", json=sample_signal, headers=auth_headers)
        gen_response = client.post("/admin/generate-brief", headers=auth_headers)
        brief_id = gen_response.json()["brief_id"]

        # Get brief by ID
        response = client.get(f"/briefs/{brief_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == brief_id


class TestThemeSynthesis:
    """Test theme synthesis logic."""

    def test_signals_cluster_by_topic(self, client, auth_headers, sample_signal):
        """Test that signals with same topic are clustered."""
        # Create two signals with same topic
        client.post("/signals", json=sample_signal, headers=auth_headers)

        sample_signal["entity"] = "Second Publisher"
        client.post("/signals", json=sample_signal, headers=auth_headers)

        # Generate brief
        client.post("/admin/generate-brief", headers=auth_headers)

        # Get brief
        response = client.get("/briefs/current")
        data = response.json()

        # Should have one theme with two signals
        topic_theme = next(
            (t for t in data["themes"] if "Test Topic" in t["title"].lower() or len(t["signals"]) == 2),
            None
        )
        assert topic_theme is not None
        assert len(topic_theme["signals"]) == 2

    def test_different_topics_create_different_themes(self, client, auth_headers, sample_signal):
        """Test that different topics create separate themes."""
        # Create signals with different topics
        client.post("/signals", json=sample_signal, headers=auth_headers)

        sample_signal["topic"] = "Different Topic"
        client.post("/signals", json=sample_signal, headers=auth_headers)

        # Generate brief
        client.post("/admin/generate-brief", headers=auth_headers)

        # Get brief
        response = client.get("/briefs/current")
        data = response.json()

        # Should have two themes
        assert len(data["themes"]) == 2

    def test_theme_has_so_what_and_now_what(self, client, auth_headers, sample_signal):
        """Test that themes have So What and Now What content."""
        # Create signal and generate brief
        client.post("/signals", json=sample_signal, headers=auth_headers)
        client.post("/admin/generate-brief", headers=auth_headers)

        # Get brief
        response = client.get("/briefs/current")
        data = response.json()

        theme = data["themes"][0]
        assert theme["so_what"] != ""
        assert len(theme["now_what"]) >= 2

    def test_theme_confidence_aggregation(self, client, auth_headers, sample_signal):
        """Test that theme confidence is aggregated from signals."""
        # Create two High confidence signals
        sample_signal["confidence"] = "High"
        client.post("/signals", json=sample_signal, headers=auth_headers)

        sample_signal["entity"] = "Second Publisher"
        client.post("/signals", json=sample_signal, headers=auth_headers)

        # Generate brief
        client.post("/admin/generate-brief", headers=auth_headers)

        # Get brief
        response = client.get("/briefs/current")
        data = response.json()

        # Theme should have High confidence
        theme = data["themes"][0]
        assert theme["aggregate_confidence"] == "High"

    def test_themes_ranked_by_impact(self, client, auth_headers, sample_signal):
        """Test that themes are ranked by impact area coverage."""
        # Create signal with more impact areas
        sample_signal["impact_areas"] = ["Ops", "Tech", "Integrity", "Procurement"]
        client.post("/signals", json=sample_signal, headers=auth_headers)

        # Create signal with fewer impact areas
        sample_signal["topic"] = "Other Topic"
        sample_signal["impact_areas"] = ["Ops"]
        client.post("/signals", json=sample_signal, headers=auth_headers)

        # Generate brief
        client.post("/admin/generate-brief", headers=auth_headers)

        # Get brief
        response = client.get("/briefs/current")
        data = response.json()

        # First theme should have more impact areas
        assert len(data["themes"]) == 2
        assert len(data["themes"][0]["impact_areas"]) >= len(data["themes"][1]["impact_areas"])
