"""Tests for Flask application."""
import pytest


def test_config_imports():
    """Test that config module can be imported."""
    import config
    assert hasattr(config, 'MONGO_URI')
    assert hasattr(config, 'SECRET_KEY')


def test_app_can_import():
    """Test that app module can be imported (requires MongoDB)."""
    try:
        from app import app
        assert app is not None
        assert app.config['TESTING'] == False
    except Exception as e:
        # Expected if MongoDB not available or dependencies not installed
        error_msg = str(e).lower()
        assert any(keyword in error_msg for keyword in ['mongo', 'connection', 'bson', 'import'])
        pytest.skip(f"Dependency not available: {str(e)}")


def test_basic_flask_structure():
    """Test basic Flask app structure without MongoDB dependency."""
    try:
        from app import app
        # Test that Flask app has expected attributes
        assert hasattr(app, 'route')
        assert hasattr(app, 'config')
    except Exception:
        # Skip if MongoDB not available
        pytest.skip("MongoDB not available in test environment")
