"""Tests for configuration module."""
import os
import pytest
import config


def test_config_mongo_uri():
    """Test that MongoDB URI is configured."""
    assert hasattr(config, 'MONGO_URI')
    assert config.MONGO_URI is not None


def test_config_secret_key():
    """Test that secret key is configured."""
    assert hasattr(config, 'SECRET_KEY')
    assert config.SECRET_KEY is not None


def test_config_embedding_model():
    """Test that embedding model is configured."""
    assert hasattr(config, 'EMBEDDING_MODEL')
    assert config.EMBEDDING_MODEL == "sentence-transformers/all-MiniLM-L6-v2"


def test_config_search_k():
    """Test that search k parameter is set."""
    assert hasattr(config, 'SEARCH_K')
    assert config.SEARCH_K == 25
    assert isinstance(config.SEARCH_K, int)


def test_config_temperature():
    """Test that temperature is configured."""
    assert hasattr(config, 'TEMPERATURE')
    assert config.TEMPERATURE == 0.7
    assert isinstance(config.TEMPERATURE, float)


def test_config_gemini_model():
    """Test that Gemini model is configured."""
    assert hasattr(config, 'GEMINI_MODEL')
    assert config.GEMINI_MODEL == "gemini-2.5-flash"
