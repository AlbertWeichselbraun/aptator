import json
import re
import sys
import urllib.request
from pathlib import Path
from tempfile import TemporaryDirectory

from aptator.tools import verify_checksum

GITHUB_API = "https://api.github.com/repos/{repo}/releases"


class GitHub:
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

    def get_latest_release_asset(self, allow_prerelease: bool = False) -> dict:
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

        return next((a for a in release.get("assets", []) if self.asset_re.search(a["name"])), None)

    def get_asset_version(self, asset):
        # Extract version from asset filename
        version_match = self.asset_version_re.search(asset["name"])
        if not version_match:
            print(f"  unable to extract version from {asset['name']}")
            return None
        return version_match.group(1)

    def download_and_verify_asset(self, asset: dict) -> Path:
        with TemporaryDirectory() as tmp, urllib.request.urlopen(asset["browser_download_url"]) as response:
            deb_path = Path(tmp) / asset["name"]
            deb_path.write_bytes(response.read())

            # Verify checksum if available in asset digest
            digest = asset.get("digest")
            if digest:
                hash_type, expected_hash = self.parse_digest(digest)
                if hash_type and expected_hash:
                    print(f"  verifying {hash_type} checksum...")
                    if verify_checksum(deb_path, expected_hash, hash_type):
                        print("  checksum verified.")
                        return deb_path
                    print("  checksum verification failed! Download may be corrupted.", file=sys.stderr)
                    sys.exit(1)
            else:
                print("  no digest available, skipping verification")
            return deb_path
