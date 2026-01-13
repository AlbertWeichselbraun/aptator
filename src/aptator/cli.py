#!/usr/bin/env python3

import re
import sys
import tomllib
from os import getenv
from pathlib import Path

from aptator import CONFIG_PATH
from aptator.state import get_installed_version, set_installed_version



def process_package(cfg):
    """Process a single package configuration."""
    name = cfg["name"]
    repo = cfg["repo"]
    asset_re = re.compile(cfg["asset_pattern"])
    asset_version_re = re.compile(cfg.get("asset_version_pattern", "(.*)"))
    pkg_name = cfg["package_name"]
    allow_prerelease = cfg.get("prerelease", False)

    print(f"Checking {name} ({repo})")


def main():
    """Main entry point for the aptator CLI."""
    with CONFIG_PATH.open("rb") as f:
        config = tomllib.load(f)

    for pkg in config.get("packages", []):
        print("X")
        try:
            process_package(pkg)
        except Exception as e:
            print(f"Error processing {pkg.get('name')}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
