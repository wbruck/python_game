"""
Configuration module for the ecosystem simulation game.

This module handles loading, validating, and providing access to game configuration settings.
It supports JSON-based configuration files with default values and runtime reloading.
"""

import json
import os
import copy
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

class Config:
    """Schema defining valid configuration values and their constraints."""
    SCHEMA = {
        "board": {
            "width": {"type": int, "min": 5, "max": 100},
            "height": {"type": int, "min": 5, "max": 100},
            "allow_diagonal_movement": {"type": bool}
        },
        "game": {
            "max_turns": {"type": int, "min": 1, "max": 10000},
            "turn_delay": {"type": float, "min": 0.0, "max": 5.0},
            "visualization_update_frequency": {"type": int, "min": 0, "max": 100},
            "unit_stats_print_frequency": {"type": int, "min": 0, "max": 100}
        },
        "units": {
            "initial_count": {
                "predator": {"type": int, "min": 0, "max": 50},
                "scavenger": {"type": int, "min": 0, "max": 50},
                "grazer": {"type": int, "min": 0, "max": 50}
            },
            "energy_consumption": {
                "move": {"type": int, "min": 0, "max": 10},
                "attack": {"type": int, "min": 0, "max": 10},
                "look": {"type": int, "min": 0, "max": 10},
                "move_hunt": {"type": int, "min": 0, "max": 10},
                "move_flee": {"type": int, "min": 0, "max": 10},
                "move_graze": {"type": int, "min": 0, "max": 10}
            },
            "decay_rate": {"type": float, "min": 0.0, "max": 1.0}
        },
        "plants": {
            "initial_count": {"type": int, "min": 0, "max": 100},
            "growth_rate": {"type": float, "min": 0.0, "max": 1.0},
            "max_count": {"type": int, "min": 1, "max": 200}
        },
        "environment": {
            "day_night_cycle": {"type": bool},
            "cycle_length": {"type": int, "min": 1, "max": 100}
        }
    }
    """
    Configuration manager for the ecosystem simulation game.
    
    This class handles loading configuration from a JSON file,
    providing default values, and allowing access to configuration settings.
    """
    
    # Default configuration values
    DEFAULT_CONFIG = {
        "board": {
            "width": 20,
            "height": 20,
            "allow_diagonal_movement": True
        },
        "game": {
            "max_turns": 1000,
            "turn_delay": 0.1,  # seconds between turns
            "visualization_update_frequency": 1,
            "unit_stats_print_frequency": 5
        },
        "units": {
            "initial_count": {
                "predator": 3,
                "scavenger": 5,
                "grazer": 8
            },
            "energy_consumption": {
                "move": 1,
                "attack": 2,
                "look": 0,
                "move_hunt": 2,
                "move_flee": 3,
                "move_graze": 1
            },
            "decay_rate": 0.1  # how quickly dead units decay
        },
        "plants": {
            "initial_count": 15,
            "growth_rate": 0.05,  # chance of new plant per turn
            "max_count": 30
        },
        "environment": {
            "day_night_cycle": True,
            "cycle_length": 20  # turns per day/night cycle
        }
    }
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the configuration manager.
        
        Args:
            config_path (str): Path to the configuration file.
        """
        self.config_path = config_path
        self.config = copy.deepcopy(self.DEFAULT_CONFIG)  # Deep copy to ensure no shared references
        self.change_listeners: List[Callable[[str, str, Any], None]] = []
        self.load_config()
        
    def load_config(self) -> None:
        """
        Load configuration from the config file.
        
        If the file doesn't exist or can't be loaded, default values are used.
        Validates all loaded values against the schema.
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    file_config = json.load(f)
                    # Validate and update config with values from file
                    self._validate_config(file_config)
                    # Update each section separately to maintain proper section tracking
                    for section in file_config:
                        if section in self.config:
                            self._update_config(self.config[section], file_config[section], section)
                    print(f"Configuration loaded from {self.config_path}")
            else:
                print(f"Config file {self.config_path} not found. Using default values.")
        except ValueError as e:
            print(f"Invalid configuration: {e}. Using default values.")
        except Exception as e:
            print(f"Error loading config: {e}. Using default values.")
    
    def _validate_config(self, config: Dict) -> None:
        """
        Validate an entire configuration dictionary against the schema.
        
        Args:
            config: Configuration dictionary to validate.
            
        Raises:
            ValueError: If any validation fails.
        """
        for section, values in config.items():
            if section not in self.SCHEMA:
                raise ValueError(f"Unknown section: {section}")
            
            if isinstance(self.SCHEMA[section], dict):
                for key, value in values.items():
                    if isinstance(value, dict) and isinstance(self.SCHEMA[section][key], dict):
                        # Recursively validate nested dictionaries
                        for subkey, subvalue in value.items():
                            self._validate_value(section, f"{key}.{subkey}", subvalue)
                    else:
                        self._validate_value(section, key, value)

    def _validate_value(self, section: str, key: str, value: Any) -> None:
        """
        Validate a single configuration value against the schema.
        
        Args:
            section: Configuration section name.
            key: Configuration key name.
            value: Value to validate.
            
        Raises:
            ValueError: If validation fails.
        """
        # Handle nested keys (e.g., "initial_count.predator")
        schema_ref = self.SCHEMA
        for part in [section] + key.split('.'):
            if part not in schema_ref:
                raise ValueError(f"Unknown key: {section}.{key}")
            schema_ref = schema_ref[part]

        if not isinstance(value, schema_ref["type"]):
            raise ValueError(f"Invalid type for {section}.{key}: expected {schema_ref['type'].__name__}, got {type(value).__name__}")

        if schema_ref["type"] in (int, float):
            if "min" in schema_ref and value < schema_ref["min"]:
                raise ValueError(f"Value for {section}.{key} below minimum: {value} < {schema_ref['min']}")
            if "max" in schema_ref and value > schema_ref["max"]:
                raise ValueError(f"Value for {section}.{key} above maximum: {value} > {schema_ref['max']}")

    def _update_config(self, target: Dict, source: Dict, section: str = None) -> None:
        """
        Recursively update nested dictionaries.
        
        Args:
            target: The target dictionary to update.
            source: The source dictionary with new values.
            section: Current configuration section being updated.
        """
        for key, value in source.items():
            if section is None:
                # Top level - key is the section
                current_section = key
            else:
                current_section = section

            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._update_config(target[key], value, current_section)
            else:
                target[key] = value
                # Notify listeners if this is a leaf value
                if not isinstance(value, dict):
                    self._notify_change(current_section, key, value)

    def add_change_listener(self, listener: Callable[[str, str, Any], None]) -> None:
        """
        Add a listener to be notified of configuration changes.
        
        Args:
            listener: Callback function taking (section, key, value) arguments.
        """
        self.change_listeners.append(listener)

    def remove_change_listener(self, listener: Callable[[str, str, Any], None]) -> None:
        """
        Remove a previously added change listener.
        
        Args:
            listener: The listener to remove.
        """
        if listener in self.change_listeners:
            self.change_listeners.remove(listener)

    def _notify_change(self, section: str, key: str, value: Any) -> None:
        """
        Notify all listeners of a configuration change.
        
        Args:
            section: Configuration section that changed.
            key: Configuration key that changed.
            value: New value.
        """
        if not key:  # Don't notify for empty keys
            return
            
        # For nested keys, notify with full path
        full_key = key
        if '.' in key:
            parts = key.split('.')
            value = self.get(section, key)  # Get actual nested value
            
        for listener in self.change_listeners:
            try:
                listener(section, full_key, value)
            except Exception as e:
                print(f"Error in config change listener: {e}")
    
    def save_config(self) -> bool:
        """
        Save the current configuration to the config file.
        
        Returns:
            bool: True if the configuration was saved successfully, False otherwise.
        """
        try:
            # Validate current config before saving
            self._validate_config(self.config)
            
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            print(f"Configuration saved to {self.config_path}")
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def get(self, section: str, key: Optional[str] = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            section: The configuration section.
            key: The specific key within the section.
                 If None, returns the entire section.
        
        Returns:
            The configuration value, or None if not found.
            
        Raises:
            ValueError: If the section or key is invalid.
        """
        if section not in self.SCHEMA:
            raise ValueError(f"Unknown section: {section}")
        
        if section not in self.config:
            return None
        
        if key is None:
            return self.config[section]
        
        # Handle nested keys
        value = self.config[section]
        for part in key.split('.'):
            if not isinstance(value, dict) or part not in value:
                return None
            value = value[part]
        return value
    
    def set(self, section: str, key: str, value: Any) -> bool:
        """
        Set a configuration value.
        
        Args:
            section: The configuration section.
            key: The specific key within the section.
            value: The value to set.
        
        Returns:
            bool: True if the value was set successfully.
            
        Raises:
            ValueError: If the value is invalid according to the schema.
        """
        if section not in self.SCHEMA:
            raise ValueError(f"Unknown section: {section}")
            
        # Validate the value before setting
        self._validate_value(section, key, value)
        
        # Ensure section exists
        if section not in self.config:
            self.config[section] = {}
            
        # Handle nested keys
        config_ref = self.config[section]
        parts = key.split('.')
        
        # Navigate to the correct nested location
        for part in parts[:-1]:
            if part not in config_ref:
                config_ref[part] = {}
            config_ref = config_ref[part]
            
        # Set the value and notify
        config_ref[parts[-1]] = value
        self._notify_change(section, key, value)
        return True
    
    def reload(self) -> bool:
        """
        Reload configuration from the config file.
        
        Returns:
            bool: True if the configuration was reloaded successfully.
        """
        try:
            old_config = dict(self.config)
            self.config = dict(self.DEFAULT_CONFIG)
            self.load_config()
            
            # Notify about all changes
            self._notify_changes_between(old_config, self.config)
            return True
        except Exception as e:
            print(f"Error reloading config: {e}")
            return False
            
    def _notify_changes_between(self, old: Dict, new: Dict, prefix: str = "") -> None:
        """
        Recursively detect and notify about changes between two config versions.
        
        Args:
            old: Old configuration dictionary
            new: New configuration dictionary
            prefix: Current key prefix for nested dictionaries
        """
        for key, new_value in new.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if key not in old:
                if not isinstance(new_value, dict):
                    self._notify_change(full_key, "", new_value)
            elif isinstance(new_value, dict):
                if isinstance(old[key], dict):
                    self._notify_changes_between(old[key], new_value, full_key)
            elif new_value != old[key]:
                self._notify_change(full_key, "", new_value)
