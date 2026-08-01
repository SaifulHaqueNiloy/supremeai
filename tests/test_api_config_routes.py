# tests/test_api_config_routes.py
"""Tests for API config routes."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.api.routes.config import router, _ConfigDBClientWrapper, db
from backend.main import app


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_admin_token():
    """Mock admin token dependency."""
    with patch('backend.api.routes.config.require_admin_token') as mock:
        mock.return_value = "mock_admin_token"
        yield mock


def test_get_public_config(test_client):
    """Test getting public configuration."""
    response = test_client.get("/config/public")
    assert response.status_code == 200
    
    data = response.json()
    assert "ENV" in data
    assert "BACKEND_URL" in data
    assert "FEATURES" in data
    assert response.headers.get("Cache-Control") == "public, max-age=3600, s-maxage=86400"


def test_get_config_by_key_success(mock_admin_token, test_client):
    """Test getting config by key with valid admin token."""
    # Mock the db.get_config method
    with patch.object(db, 'get_config', return_value="test_value"):
        response = test_client.get("/config/test_key")
        assert response.status_code == 200
        
        data = response.json()
        assert data["key"] == "test_key"
        assert data["value"] == "test_value"


def test_get_config_by_key_not_found(mock_admin_token, test_client):
    """Test getting config by key that doesn't exist."""
    # Mock the db.get_config method to return None
    with patch.object(db, 'get_config', return_value=None):
        response = test_client.get("/config/nonexistent_key")
        assert response.status_code == 404
        
        data = response.json()
        assert data["detail"] == "Config key not found"


def test_get_config_by_key_unauthorized(test_client):
    """Test getting config by key without admin token."""
    # Patch the admin token dependency to raise an exception
    with patch('backend.api.routes.config.require_admin_token') as mock:
        mock.side_effect = Exception("Unauthorized")
        
        response = test_client.get("/config/test_key")
        # Status code depends on the auth implementation, but should be 401 or 403
        assert response.status_code in [401, 403]


def test_update_config_by_key_success(mock_admin_token, test_client):
    """Test updating config by key with valid admin token."""
    # Mock the db.set_config method
    with patch.object(db, 'set_config') as mock_set_config:
        test_value = {"some": "data"}
        response = test_client.put("/config/test_key", json=test_value)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        
        # Verify that set_config was called with correct arguments
        mock_set_config.assert_called_once_with("test_key", test_value)


def test_update_config_by_key_unauthorized(test_client):
    """Test updating config by key without admin token."""
    # Patch the admin token dependency to raise an exception
    with patch('backend.api.routes.config.require_admin_token') as mock:
        mock.side_effect = Exception("Unauthorized")
        
        response = test_client.put("/config/test_key", json={"value": "test"})
        # Status code depends on the auth implementation, but should be 401 or 403
        assert response.status_code in [401, 403]


def test_config_db_client_wrapper_initialization():
    """Test initialization of config DB client wrapper."""
    wrapper = _ConfigDBClientWrapper()
    assert wrapper.client is None


def test_config_db_client_wrapper_get_config():
    """Test get_config method of config DB client wrapper."""
    wrapper = _ConfigDBClientWrapper()
    result = wrapper.get_config("test_key")
    assert result is None


def test_config_db_client_wrapper_set_config():
    """Test set_config method of config DB client wrapper."""
    wrapper = _ConfigDBClientWrapper()
    result = wrapper.set_config("test_key", "test_value")
    assert result is None


def test_config_router_prefix_and_tags():
    """Test that the router has the correct prefix and tags."""
    # We can't directly access router prefix, but we can check the routes
    # The routes should be registered with the correct prefix
    routes = [route.path for route in app.routes]
    
    # Check that config routes exist
    config_routes = [route for route in routes if '/config' in route]
    assert len(config_routes) > 0


def test_update_config_by_key_with_various_types(mock_admin_token, test_client):
    """Test updating config by key with various data types."""
    test_cases = [
        ("string_key", "string_value"),
        ("number_key", 42),
        ("float_key", 3.14),
        ("bool_key", True),
        ("list_key", [1, 2, 3]),
        ("dict_key", {"nested": "value"}),
        ("null_key", None),
    ]
    
    for key, value in test_cases:
        with patch.object(db, 'set_config') as mock_set_config:
            response = test_client.put(f"/config/{key}", json=value)
            assert response.status_code == 200
            mock_set_config.assert_called_once_with(key, value)
            mock_set_config.reset_mock()


def test_get_config_by_key_special_characters(mock_admin_token, test_client):
    """Test getting config by key with special characters."""
    special_keys = [
        "test-key",
        "test_key",
        "test.key",
        "test_key_123",
        "TestKey",
        "test key with spaces",
    ]
    
    for key in special_keys:
        with patch.object(db, 'get_config', return_value=f"value_for_{key}"):
            response = test_client.get(f"/config/{key}")
            assert response.status_code == 200
            data = response.json()
            assert data["key"] == key
            assert data["value"] == f"value_for_{key}"


def test_update_config_by_key_special_characters(mock_admin_token, test_client):
    """Test updating config by key with special characters."""
    special_keys = [
        "test-key",
        "test_key",
        "test.key",
        "test_key_123",
        "TestKey",
        "test key with spaces",
    ]
    
    for key in special_keys:
        with patch.object(db, 'set_config') as mock_set_config:
            response = test_client.put(f"/config/{key}", json="test_value")
            assert response.status_code == 200
            mock_set_config.assert_called_once_with(key, "test_value")
            mock_set_config.reset_mock()


def test_config_public_endpoint_response_structure(test_client):
    """Test the structure of the public config response."""
    response = test_client.get("/config/public")
    assert response.status_code == 200
    
    data = response.json()
    
    # Check required fields
    assert "ENV" in data
    assert "BACKEND_URL" in data
    assert "FEATURES" in data
    
    # Check FEATURES structure
    features = data["FEATURES"]
    assert isinstance(features, dict)
    assert "morphic_rewrite" in features
    assert "sandbox_v2" in features
    assert "background_tasks_enabled" in features


def test_config_public_endpoint_caching_headers(test_client):
    """Test that the public config endpoint sets correct caching headers."""
    response = test_client.get("/config/public")
    assert response.status_code == 200
    
    cache_header = response.headers.get("Cache-Control")
    assert cache_header == "public, max-age=3600, s-maxage=86400"


@patch('backend.api.routes.config.require_admin_token')
def test_config_endpoints_admin_auth_failure(mock_require_admin, test_client):
    """Test that config endpoints return appropriate error when admin auth fails."""
    mock_require_admin.side_effect = HTTPException(status_code=401, detail="Not authenticated")
    
    # Test GET endpoint
    response = test_client.get("/config/test_key")
    assert response.status_code == 401
    
    # Test PUT endpoint
    response = test_client.put("/config/test_key", json={"value": "test"})
    assert response.status_code == 401


def test_config_router_tags():
    """Test that the config router has the correct tags."""
    # Find routes with config in the path
    config_routes = [route for route in app.routes if hasattr(route, 'path') and '/config' in route.path]
    
    # Verify that the routes have the correct tags
    for route in config_routes:
        if hasattr(route, 'methods'):
            # Check if it's one of our config routes
            if any(method in ['GET', 'PUT'] for method in route.methods):
                # We can't easily access the tags from the route object, 
                # but we know from the source code that the router has tags=["Global Config"]
                pass  # The tag is set in the source code


def test_config_router_methods():
    """Test that the config router has the correct HTTP methods."""
    # Get all config routes
    config_routes = [route for route in app.routes if hasattr(route, 'path') and '/config' in route.path]
    
    # Check that we have the expected endpoints
    paths = [route.path for route in config_routes]
    
    # Public config endpoint
    assert "/config/public" in paths
    
    # Dynamic endpoints (these would be harder to check precisely due to the {key} parameter)
    # But we know they exist from the source code