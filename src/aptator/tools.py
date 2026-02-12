import hashlib
import subprocess
from pathlib import Path


def run(cmd):
    """Run a command and return its output as a string."""
    return subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True).strip()


def verify_checksum(file_path: Path, expected_hash: str, hash_type: str = "sha256") -> bool:
    """Verify file checksum against expected hash."""
    hash_func = getattr(hashlib, hash_type)()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)

    computed = hash_func.hexdigest()
    return computed.lower() == expected_hash.lower()
