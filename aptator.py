#!/usr/bin/env python3

import json
import re
import subprocess
import sys
import tempfile
import tomllib
import urllib.request
from pathlib import Path

CONFIG_PATH = Path("/etc/github-deb-watcher.toml")
GITHUB_API = "https://api.github.com/repos/{repo}/releases/latest"


def run(cmd):
    """Run a command and return its output as a string."""
    return subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True).strip()


def get_installed_version(pkg):
    """Get the installed version of a package, or None if not installed."""
    try:
        return run(["dpkg-query", "-W", "-f=${Version}", pkg])
    except subprocess.CalledProcessError:
        return None


def install_deb(path):
    """Install a .deb package using dpkg."""
    subprocess.run(["/usr/bin/sudo", "/usr/bin/dpkg", "-i", path], check=True)


def process_package(cfg):
    """Process a single package configuration."""
    name = cfg["name"]
    repo = cfg["repo"]
    asset_re = re.compile(cfg["asset_pattern"])
    pkg_name = cfg["package_name"]

    print(f"Checking {name} ({repo})")

    with urllib.request.urlopen(GITHUB_API.format(repo=repo), timeout=15) as response:
        release = json.loads(response.read().decode("utf-8"))

    tag = release["tag_name"]
    installed = get_installed_version(pkg_name)

    if installed == tag:
        print(f"  up to date ({installed})")
        return

    asset = None
    for a in release.get("assets", []):
        if asset_re.search(a["name"]):
            asset = a
            break

    if not asset:
        print("  no matching .deb asset found")
        return

    print(f"  installing {tag}")

    with tempfile.TemporaryDirectory() as tmp:
        deb_path = Path(tmp) / asset["name"]
        with urllib.request.urlopen(asset["browser_download_url"]) as response:
            deb_path.write_bytes(response.read())

        install_deb(str(deb_path))


def main():
    with CONFIG_PATH.open() as f:
        config = tomllib.load(f)

    for pkg in config.get("packages", []):
        try:
            process_package(pkg)
        except Exception as e:
            print(f"Error processing {pkg.get('name')}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
