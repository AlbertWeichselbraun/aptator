import tarfile
import tempfile
from pathlib import Path
from urllib.request import urlopen

from aptator import AptatorConfig
from aptator.actions.tar_extraction_filter import rename

SUDO = AptatorConfig.settings.sudo

def download_extract_and_link(url, extract_to, link_to, archive_root_dir=None):
    """Download an archive, extract it, and create a symlink.

    Args:
        url: The URL of the archive to download.
        extract_to: Path to which the archive should be extracted (e.g., /opt).
        archive_root_dir: Root directory name of the extracted archive (e.g. ./Zotero-8.0.2)
        link_to: Symlink path (e.g., /opt/zotero -> /opt/Zotero-8.0.2).
        
    Raises:
        ValueError: If the content type is unsupported.
    """
    extract_to = Path(extract_to)
    link_to = Path(link_to)

    # Download the file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        with urlopen(url) as response:
            content_type = response.headers.get("Content-Type", "")
            temp_file.write(response.read())
        temp_file_path = Path(temp_file.name)

    if "tar" in content_type.lower():
        with tarfile.open(temp_file_path) as tar:
            tar_filter = rename(archive_root_dir) if archive_root_dir else "data"
            tar.extractall(path=extract_to, filter=tar_filter)
    else:
        raise ValueError(f"Unsupported content type: {content_type}")

    # Remove existing symlink if it exists
    if link_to.exists():
        link_to.unlink()

    # Create symlink
    link_to.symlink_to(extract_to, target_is_directory=True)

    # Clean up temporary file
    temp_file_path.unlink()
