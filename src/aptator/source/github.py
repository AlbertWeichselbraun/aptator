import json
import re
import sys
import urllib.request
from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path
from tempfile import TemporaryDirectory

from aptator.source import Source
from aptator.tools import verify_checksum

GITHUB_API = "https://api.github.com/repos/{repo}/releases"


class Downloadable(ABC):
    """Abstract base class for downloadable GitHub objects (assets or tags)."""

    @abstractmethod
    def get_download_url(self) -> str:
        """Return the URL to download the object."""

    @abstractmethod
    def get_filename(self) -> str:
        """Return the filename to save as."""

    @abstractmethod
    def get_digest(self) -> str | None:
        """Return the digest string (algorithm:hash), or None if not available."""


class Asset(Downloadable):
    """Represents a GitHub release asset."""

    def __init__(self, asset_data: dict):
        self.data = asset_data

    def get_download_url(self) -> str:
        return self.data["browser_download_url"]

    def get_filename(self) -> str:
        return re.sub(
            r"https://api\.github\.com/repos/([^/]+)/([^/]+)/tarball/refs/tags/([^/]+)",
            r"https://github.com/\1/\2/archive/refs/tags/\3.tar.gz",
            self.data["name"],
        )

    def get_digest(self) -> str | None:
        return self.data.get("digest")


class Tag(Downloadable):
    """Represents a GitHub tag."""

    def __init__(self, tag_data: dict):
        self.data = tag_data

    def get_download_url(self) -> str:
        return self.data["tarball_url"]

    def get_filename(self) -> str:
        return f"{self.data['name']}.tar.gz"

    def get_digest(self) -> str | None:
        # Tags don't have digest information
        return None


class GitHub(Source):
    def __init__(self, repo: str, asset_version_re: str, asset_re: str):
        self.repo = repo
        self.asset_version_re = re.compile(asset_version_re)
        self.asset_re = re.compile(asset_re)

    @staticmethod
    def parse_digest(digest_str):
        """Parse digest string in format 'algorithm:hash'."""
        if not digest_str or ":" not in digest_str:
            return None, None
        return digest_str.split(":", 1)

    def get_latest_tag(self) -> Tag | None:
        """Get the latest tag from the repository.

        Returns:
            dict: JSON object representing the latest tag, or None if no tags found.
        """
        tags_url = f"https://api.github.com/repos/{self.repo}/tags"
        try:
            with urllib.request.urlopen(tags_url, timeout=15) as response:
                tags = json.loads(response.read().decode("utf-8"))

            if not tags:
                print("  no tags found")
                return None

            return Tag(tags[0])
        except urllib.error.HTTPError as e:
            print(f"  error fetching tags: {e}")
            return None

    def get_latest_release_asset(self, allow_prerelease: bool = False) -> Asset | None:
        # Get releases based on prerelease preference
        if allow_prerelease:
            # Get all releases to include pre-releases
            with urllib.request.urlopen(GITHUB_API.format(repo=self.repo), timeout=15) as response:
                releases = json.loads(response.read().decode("utf-8"))
            release = releases[0] if releases else {}
        else:
            # Get only the latest non-prerelease
            with urllib.request.urlopen(GITHUB_API.format(repo=self.repo) + "/latest", timeout=15) as response:
                release = json.loads(response.read().decode("utf-8"))

        if not release:
            print("  no releases found")
            return None

        return Asset(next((a for a in release.get("assets", []) if self.asset_re.search(a["name"])), None))

    def get_asset_version(self, asset):
        # Extract version from asset filename
        version_match = self.asset_version_re.search(asset["name"])
        if not version_match:
            print(f"  unable to extract version from {asset['name']}")
            return None
        return version_match.group(1)

    def perform_action(self, downloadable: Downloadable, action: Callable) -> bool:
        """Download and verify a Downloadable object, then perform an action on it.

        Args:
            downloadable: A Downloadable object (Asset or Tag)
            action: Callable that takes the file path as argument

        Returns:
            bool: True if successful, False otherwise
        """
        with TemporaryDirectory() as tmp, urllib.request.urlopen(downloadable.get_download_url()) as response:
            file_path = Path(tmp) / downloadable.get_filename()
            file_path.write_bytes(response.read())

            # Verify checksum if available
            digest = downloadable.get_digest()
            if digest:
                hash_type, expected_hash = self.parse_digest(digest)
                if hash_type and expected_hash:
                    print(f"  verifying {hash_type} checksum...")
                    if verify_checksum(file_path, expected_hash, hash_type):
                        print("  checksum verified.")
                        action(file_path)
                        return True
                    print("  checksum verification failed! Download may be corrupted.", file=sys.stderr)
                    print("  aborting installation.", file=sys.stderr)
                    return False
            else:
                print("  no digest available, skipping verification")
            action(file_path)
            return True
