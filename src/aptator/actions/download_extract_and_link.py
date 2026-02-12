import os
import tarfile
import tempfile
from pathlib import Path
from urllib.request import urlopen

from aptator import AptatorConfig
from aptator.actions.tar_extraction_filter import rename
from aptator.tools import run

SUDO = AptatorConfig.paths.sudo


def download_extract_and_link(url, extract_to, link_to):
    """Download an archive, extract it, and create a symlink.

    Args:
        url: The URL of the archive to download.
        extract_to: Path to which the archive should be extracted (e.g., /opt/Zotero-8.0.2).
        link_to: Symlink path (e.g., /opt/zotero -> /opt/Zotero-8.0.2).

    Raises:
        ValueError: If the content type is unsupported.
    """
    uid = os.getuid()
    gid = os.getgid()
    extract_to = Path(extract_to)
    link_to = Path(link_to)

    run([SUDO, AptatorConfig.paths.mkdir, "-p", extract_to])
    run([SUDO, AptatorConfig.paths.chown, "-R", f"{uid}:{gid}", extract_to])

    # Download the file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        with urlopen(url) as response:
            content_type = response.headers.get("Content-Type", "")
            temp_file.write(response.read())
        temp_file_path = Path(temp_file.name)

    if "tar" in content_type.lower():
        with tarfile.open(temp_file_path) as tar:
            tar_filter = rename(str(extract_to.name))
            tar.extractall(path=str(extract_to.parent), filter=tar_filter)
    else:
        raise ValueError(f"Unsupported content type: {content_type}")

    # Remove existing symlink if it exists
    run([SUDO, AptatorConfig.paths.chown, "-R", "root:root", extract_to])
    run([SUDO, AptatorConfig.paths.ln, "-sfn", extract_to, link_to])

    # Clean up temporary file
    temp_file_path.unlink()
