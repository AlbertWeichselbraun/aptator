from os import getenv
from pathlib import Path

LOCAL_CONFIG_PATH = Path(getenv("XDG_CONFIG_HOME", Path.home() / ".config")) / "aptator" / "aptator.toml"
GLOBAL_CONFIG_PATH = Path("/etc/aptator/aptator.toml")

if not (GLOBAL_CONFIG_PATH.exists() or LOCAL_CONFIG_PATH.exists()):
    raise FileNotFoundError("No configuration file found for aptator.")

CONFIG_PATH = LOCAL_CONFIG_PATH if LOCAL_CONFIG_PATH.exists() else GLOBAL_CONFIG_PATH
