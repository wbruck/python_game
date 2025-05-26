"""Tests for the configuration system."""

import json
import os
import pytest
from game.config import Config

@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file for testing."""
    config_path = tmp_path / "test_config.json"
    test_config = {
        "board": {
            "width": 30,
            "height": 25,
            "allow_diagonal_movement": False
        },
        "units": {
            "initial_count": {
                "predator": 5,
                "grazer": 10
            }
        }
    }
    with open(config_path, "w") as f:
        json.dump(test_config, f)
    return str(config_path)

def test_load_default_config():
    """Test loading default configuration when file doesn't exist."""
    config = Config("nonexistent.json")
    assert config.get("board", "width") == 20
    assert config.get("board", "height") == 20
    assert config.get("board", "allow_diagonal_movement") is True
    assert config.get("units", "initial_count.predator") == 3

def test_load_custom_config(temp_config_file):
    """Test loading custom configuration from file."""
    config = Config(temp_config_file)
    assert config.get("board", "width") == 30
    assert config.get("board", "height") == 25
    assert config.get("board", "allow_diagonal_movement") is False
    assert config.get("units", "initial_count.predator") == 5
    # Default values should be preserved for unspecified settings
    assert config.get("game", "max_turns") == 1000

def test_validate_config():
    """Test configuration validation rules."""
    config = Config()
    
    # Test invalid values
    with pytest.raises(ValueError, match="below minimum"):
        config._validate_value("board", "width", -5)
    with pytest.raises(ValueError, match="below minimum"):
        config._validate_value("board", "height", 0)
    with pytest.raises(ValueError, match="Invalid type"):
        config._validate_value("board", "allow_diagonal_movement", "maybe")
    with pytest.raises(ValueError, match="above maximum"):
        config._validate_value("board", "width", 101)
    
    # Test valid values
    config._validate_value("board", "width", 50)
    config._validate_value("board", "height", 50)
    config._validate_value("board", "allow_diagonal_movement", True)

def test_nested_config_access():
    """Test accessing nested configuration values."""
    config = Config()
    assert isinstance(config.get("units", "initial_count"), dict)
    assert config.get("units", "initial_count.predator") == 3
    assert config.get("units", "energy_consumption.move") == 1

def test_set_config_values():
    """Test setting configuration values."""
    config = Config()
    
    # Test setting simple values
    config.set("board", "width", 40)
    assert config.get("board", "width") == 40
    
    # Test setting nested values
    config.set("units", "initial_count.predator", 7)
    assert config.get("units", "initial_count.predator") == 7

def test_reload_config(temp_config_file):
    """Test configuration reloading."""
    config = Config(temp_config_file)
    original_width = config.get("board", "width")
    
    # Modify the config file
    new_config = {
        "board": {
            "width": 40,
            "height": 35,
            "allow_diagonal_movement": True
        }
    }
    with open(temp_config_file, "w") as f:
        json.dump(new_config, f)
    
    # Test reload
    assert config.reload() is True
    assert config.get("board", "width") == 40
    assert config.get("board", "height") == 35
    assert config.get("board", "allow_diagonal_movement") is True

def test_config_change_notification():
    """Test configuration change notifications."""
    config = Config()
    changes = []
    
    def on_config_change(section, key, value):
        changes.append((section, key, value))
    
    config.add_change_listener(on_config_change)
    
    # Test simple value change
    config.set("board", "width", 50)
    assert len(changes) == 1
    assert changes[0] == ("board", "width", 50)
    
    # Test nested value change
    config.set("units", "initial_count.predator", 8)
    assert len(changes) == 2
    assert changes[1] == ("units", "initial_count.predator", 8)

def test_save_config(temp_config_file):
    """Test saving configuration to file."""
    config = Config(temp_config_file)
    config.set("board", "width", 45)
    config.set("units", "initial_count.predator", 6)
    
    assert config.save_config() is True
    
    # Load config again to verify save
    new_config = Config(temp_config_file)
    assert new_config.get("board", "width") == 45
    assert new_config.get("units", "initial_count.predator") == 6

def test_invalid_section_key():
    """Test handling of invalid section and key access."""
    config = Config()
    
    with pytest.raises(ValueError, match="Unknown section"):
        config.get("invalid_section")
        
    assert config.get("board", "invalid_key") is None
