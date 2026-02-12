import tomllib
from os import getenv
from pathlib import Path

LOCAL_CONFIG_PATH = Path(getenv("XDG_CONFIG_HOME", Path.home() / ".config")) / "aptator" / "aptator.toml"
GLOBAL_CONFIG_PATH = Path("/etc/aptator/aptator.toml")

if not (GLOBAL_CONFIG_PATH.exists() or LOCAL_CONFIG_PATH.exists()):
    raise FileNotFoundError("No configuration file found for aptator.")

CONFIG_PATH = LOCAL_CONFIG_PATH if LOCAL_CONFIG_PATH.exists() else GLOBAL_CONFIG_PATH


class ConfigSection:
    """Dynamic container for a configuration section."""

    def __init__(self, data):
        """Initialize with configuration data."""
        for key, value in data.items() if isinstance(data, dict) else []:
            setattr(self, key, value)


class AptatorConfigMeta(type):
    """Metaclass for dynamic configuration management."""

    _sections = None

    def __getattr__(cls, name):
        """Dynamically access config sections and parameters."""
        if cls._sections is None:
            with open(CONFIG_PATH, "rb") as f:
                config_dict = tomllib.load(f)
                cls._sections = {
                    section_name: ConfigSection(section_data) for section_name, section_data in config_dict.items()
                }

        return cls._sections.get(name)


class AptatorConfig(metaclass=AptatorConfigMeta):
    """Global configuration manager for aptator."""
