#!/usr/bin/env python3

import argparse
import re
import sys
import shutil
import tarfile
import tempfile
import tomllib
import zipfile

from pathlib import Path

from urllib import urlopen

from aptator import CONFIG_PATH
from aptator.actions.deb import install_deb
from aptator.actions.exec import exec_command
from aptator.actions.extract_and_link import extract_and_link
from aptator.source.github import GitHub
from aptator.state import get_installed_version, set_installed_version

TAR_TYPES = ("application/gzip", "application/x-gzip", "application/x-tar", "application/x-gtar", 
             "application/x-bzip2", "application/x-xz", "application/x-compress", "application/x-lzma")
ZIP_TYPES = ("application/zip", "application/x-zip-compressed", "application/x-zip", "application/x-compressed")

def download_file(url: str) -> tuple[Path, str]:
    """Download a file to a temporary location and return its path."""
    tmp_dir = tempfile.mkdtemp()
    dest_file = tmp_dir / "archive"

    with urlopen(url) as src, dest_file.open("wb"), dest_file.open("wb") as dest:
        content_type = src.headers.get("Content-Type", "").split(";")[0].strip()
        shutil.copyfileobj(src, dest)

    return dest_file, content_type


def extract_archive(archive_path: Path, archive_content_type, target_dir: Path):
    """Extract archive into target_dir."""
    if target_dir.exists():
        shutil.rmtree(target_dir)

    target_dir.mkdir(parents=True, exist_ok=True)

    if archive_content_type in TAR_TYPES:
        with tarfile.open(archive_path) as tar:
            tar.extractall(target_dir)

    elif archive_content_type == "zip":
        with zipfile.ZipFile(archive_path) as zipf:
            zipf.extractall(target_dir)

    else:
        raise ValueError(f"Unsupported archive content type: {archive_content_type}")


def process_package(cfg, force_packages):
    """Process a single package configuration."""
    name = cfg["name"]
    repo = cfg["repo"]
    asset_re = re.compile(cfg["asset_pattern"])
    asset_version_re = re.compile(cfg.get("asset_version_pattern", "(.*)"))
    allow_prerelease = cfg.get("prerelease", False)
    use_tag = cfg.get("use_tag", False)
    action = cfg.get("action", {})
    action_type = action.get("type") if isinstance(action, dict) else None

    print(f"Checking {name} ({repo})")

    # Get currently installed version
    installed_version = get_installed_version(name)
    print("... Installed version:", installed_version)

    # Get latest release or tag from GitHub
    gh = GitHub(repo, asset_version_re, asset_re)

    if use_tag:
        downloadable = gh.get_latest_tag()
        if not downloadable:
            print("No tag found...")
            return
        release_version = (
            asset_version_re.search(downloadable.data["name"]).group(1)
            if asset_version_re.search(downloadable.data["name"])
            else downloadable.data["name"]
        )
    else:
        downloadable = gh.get_latest_release_asset(allow_prerelease=allow_prerelease)
        if not downloadable:
            print("No release asset found...")
            return
        release_version = gh.get_asset_version(downloadable.data)

    print("... Latest release:", release_version if release_version else "none")
    print()

    # skip packages that have already the latest version installed
    if installed_version == release_version and name not in force_packages:
        return

    if name in force_packages:
        print(f"...Forcing reinstallation of {name} with version {release_version}")
    else:
        print(f"...Updating {name} to version {release_version}")

    # Handle deb-install action
    if action_type == "deb-install":
        if gh.perform_action(downloadable, action=install_deb):
            set_installed_version(name, release_version)
            print(f"{name} updated successfully.")
        else:
            print(f"{name} update failed.")

    # Handle exec action
    elif action_type == "exec":
        command = action.get("command")
        if command:
            exec_command(command)
            set_installed_version(name, release_version)
            print(f"{name} updated successfully.")
        else:
            print(f"{name} update failed: no command specified.")

    # Handle extract-and-link action
    elif action_type == "extract-and-link":
        extract_to = action.get("extract_to") + f"/{name}-{release_version}"
        link_to = action.get("link_to")
        if extract_to and link_to:
            if gh.perform_action(downloadable, action=lambda path: extract_and_link(str(path), extract_to, link_to)):
                set_installed_version(name, release_version)
                print(f"{name} updated successfully.")
            else:
                print(f"{name} update failed.")
        else:
            print(f"{name} update failed: extract_to and link_to must be specified.")


def main():
    """Main entry point for the aptator CLI."""
    parser = argparse.ArgumentParser(
        description="Manage GitHub release-based package installations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--force",
        nargs="+",
        metavar="PACKAGE",
        default=[],
        help="Force update/install for specified package names (e.g., --force FreeTube Zotero)",
    )
    args = parser.parse_args()

    with CONFIG_PATH.open("rb") as f:
        config = tomllib.load(f)

    for pkg in config.get("packages", []):
        try:
            process_package(pkg, force_packages=args.force)
        except Exception as e:
            print(f"Error processing {pkg.get('name')}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
