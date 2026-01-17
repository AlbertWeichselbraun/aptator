import subprocess
import tarfile
from pathlib import Path


def extract_and_link(tar_gz_path, extract_to, link_to):
    """Extract a tar.gz file, rename it to extract_to, and create a symlink to it.
    
    Args:
        tar_gz_path: Path to the tar.gz file
        extract_to: Final path for the extracted directory (e.g., /opt/Zotero-1.1.1)
        link_to: Path where to create the symlink (e.g., /opt/zotero)
        
    Raises:
        FileNotFoundError: If the tar.gz file doesn't exist
        subprocess.CalledProcessError: If extraction or linking fails
    """
    tar_gz_path = Path(tar_gz_path)
    extract_to = Path(extract_to)
    link_to = Path(link_to)
    
    if not tar_gz_path.exists():
        raise FileNotFoundError(f"Archive not found: {tar_gz_path}")
    
    # Get the top-level directory name from the archive (without extracting)
    with tarfile.open(tar_gz_path, 'r:gz') as tar:
        members = tar.getmembers()
        if not members:
            raise ValueError("Archive is empty")
        top_level = members[0].name.split('/')[0]
    
    # Extract to parent directory
    extract_parent = extract_to.parent
    extracted_dir = extract_parent / top_level
    
    # Extract the tar.gz file using sudo
    print(f"  extracting to {extract_parent}...")
    subprocess.run(
        ["sudo", "tar", "-xzf", str(tar_gz_path), "-C", str(extract_parent)],
        check=True,
        capture_output=True
    )
    
    # Rename the extracted directory to the desired name
    if extracted_dir != extract_to:
        print(f"  renaming {extracted_dir} to {extract_to}...")
        # Remove extract_to if it already exists
        subprocess.run(
            ["sudo", "rm", "-rf", str(extract_to)],
            check=True,
            capture_output=True
        )
        subprocess.run(
            ["sudo", "mv", str(extracted_dir), str(extract_to)],
            check=True,
            capture_output=True
        )
    
    # Remove existing symlink if it exists (using sudo)
    print(f"  removing existing link/directory at {link_to}...")
    subprocess.run(
        ["sudo", "rm", "-f", str(link_to)],
        check=True,
        capture_output=True
    )
    
    # Create symlink using sudo
    print(f"  creating symlink {link_to} -> {extract_to}...")
    subprocess.run(
        ["sudo", "ln", "-sf", str(extract_to), str(link_to)],
        check=True,
        capture_output=True
    )
    
    print(f"  extraction and linking complete.")
