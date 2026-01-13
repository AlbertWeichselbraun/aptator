#!/usr/bin/env python3

import re
import sys
import tomllib
from os import getenv
from pathlib import Path

from aptator import CONFIG_PATH
from aptator.state import get_installed_version, set_installed_version
from aptator.source.github import GitHub
from aptator.actions.deb import install_deb


def process_package(cfg):
    """Process a single package configuration."""
    name = cfg["name"]
    repo = cfg["repo"]
    asset_re = re.compile(cfg["asset_pattern"])
    asset_version_re = re.compile(cfg.get("asset_version_pattern", "(.*)"))
    allow_prerelease = cfg.get("prerelease", False)
    action = cfg.get("action", {})
    action_type = action.get("type") if isinstance(action, dict) else None

    print(f"Checking {name} ({repo})")

    # Get currently installed version
    installed_version = get_installed_version(name)
    print("... Installed version:", installed_version)

    # Get latest release from GitHub
    gh = GitHub(repo, asset_version_re, asset_re)
    release_asset = gh.get_latest_release_asset(allow_prerelease=allow_prerelease)
    release_version = gh.get_asset_version(release_asset) if release_asset else None
    print("... Latest release:", release_version if release_version else "none")
    print()

    if installed_version != release_version and release_asset:
        print(f"...Updating {name} to version {release_version}")
        
        # Handle deb-install action
        if action_type == "deb-install":
            if gh.perform_asset_action(release_asset, action=install_deb):
                set_installed_version(name, release_version)
                print(f"{name} updated successfully.")
            else:
                print(f"{name} update failed.")            

    

def main():
    """Main entry point for the aptator CLI."""
    with CONFIG_PATH.open("rb") as f:
        config = tomllib.load(f)

    for pkg in config.get("packages", []):
        try:
            process_package(pkg)
        except IOException as e:
            print(f"Error processing {pkg.get('name')}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
