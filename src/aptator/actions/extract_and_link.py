import subprocess
import tarfile
from pathlib import Path


def extract_and_link(tar_gz_path, extract_to, link_to):
    """Extract a tar.gz file and create a symlink to the extracted directory.
    
    Args:
        tar_gz_path: Path to the tar.gz file
        extract_to: Directory where to extract the archive
        link_to: Path where to create the symlink
        
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
    
    extracted_dir = extract_to / top_level
    
    # Extract the tar.gz file using sudo
    print(f"  extracting to {extract_to}...")
    subprocess.run(
        ["sudo", "tar", "-xzf", str(tar_gz_path), "-C", str(extract_to)],
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
    print(f"  creating symlink {link_to} -> {extracted_dir}...")
    subprocess.run(
        ["sudo", "ln", "-sf", str(extracted_dir), str(link_to)],
        check=True,
        capture_output=True
    )
    
    print(f"  extraction and linking complete.")
