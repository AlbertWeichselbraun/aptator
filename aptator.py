#!/usr/bin/env python3

import hashlib
import json
import re
import subprocess
import sys
import tempfile
import tomllib
import urllib.request
from os import getenv
from pathlib import Path

CONFIG_PATH = Path(getenv("XDG_CONFIG_HOME", Path.home() / ".config")) / "aptator" / "aptator.toml"
GITHUB_API = "https://api.github.com/repos/{repo}/releases"


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


def verify_checksum(file_path, expected_hash, hash_type="sha256"):
    """Verify file checksum against expected hash."""
    hash_func = getattr(hashlib, hash_type)()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)
    
    computed = hash_func.hexdigest()
    return computed.lower() == expected_hash.lower()


def parse_digest(digest_str):
    """Parse digest string in format 'algorithm:hash'."""
    if not digest_str or ":" not in digest_str:
        return None, None    
    return digest_str.split(":", 1)


def process_package(cfg):
    """Process a single package configuration."""
    name = cfg["name"]
    repo = cfg["repo"]
    asset_re = re.compile(cfg["asset_pattern"])
    asset_version_pattern = cfg.get("asset_version_pattern", "(.*)")
    asset_version_re = re.compile(asset_version_pattern)
    pkg_name = cfg["package_name"]
    allow_prerelease = cfg.get("prerelease", False)

    print(f"Checking {name} ({repo})")

    # Get releases based on prerelease preference
    if allow_prerelease:
        # Get all releases to include pre-releases
        with urllib.request.urlopen(GITHUB_API.format(repo=repo), timeout=15) as response:
            releases = json.loads(response.read().decode("utf-8"))
        release = releases[0] if releases else {}
    else:
        # Get only the latest non-prerelease
        with urllib.request.urlopen(GITHUB_API.format(repo=repo) + "/latest", timeout=15) as response:
            release = json.loads(response.read().decode("utf-8"))

    if not release:
        print("  no releases found")
        return

    asset = next((a for a in release.get("assets", []) if asset_re.search(a["name"])), None)
    if not asset:
        print("  no matching .deb asset found")
        return

    # Extract version from asset filename
    version_match = asset_version_re.search(asset["name"])
    if not version_match:
        print(f"  unable to extract version from {asset['name']}")
        return
    
    asset_version = version_match.group(1)
    installed = get_installed_version(pkg_name)

    if installed == asset_version:
        print(f"  up to date ({installed})")
        return

    print("  updating from", installed or "not installed", "to", asset_version)
    print(f"  installing {asset_version}")
    
    with tempfile.TemporaryDirectory() as tmp:
        deb_path = Path(tmp) / asset["name"]
        with urllib.request.urlopen(asset["browser_download_url"]) as response:
            deb_path.write_bytes(response.read())

        # Verify checksum if available in asset digest
        digest = asset.get("digest")
        if digest:
            hash_type, expected_hash = parse_digest(digest)
            if hash_type and expected_hash:
                print(f"  verifying {hash_type} checksum...")
                if verify_checksum(deb_path, expected_hash, hash_type):
                    print(f"  checksum verified.")
                else:
                    print(f"  checksum verification failed! Download may be corrupted.", file=sys.stderr)
                    return
        else:
            print("  no digest available, skipping verification")

        install_deb(str(deb_path))


def main():
    with CONFIG_PATH.open("rb") as f:
        config = tomllib.load(f)

    for pkg in config.get("packages", []):
        try:
            process_package(pkg)
        except Exception as e:
            print(f"Error processing {pkg.get('name')}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
