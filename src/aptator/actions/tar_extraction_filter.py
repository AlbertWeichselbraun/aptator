"""Custom tar extraction filters for archive manipulation."""

import tarfile


def rename(root_dir: str, base_filter: str | None = "data_filter"):
    """Create a tar data filter that renames the root directory during extraction.

    Args:
        root_dir: The new name for the root directory (e.g., "zotero-7.0.1")
        base_filter: The base filter to apply (default: "data" for security)

    Returns:
        A filter function compatible with tarfile.extractall(filter=...)

    Example:
        >>> import tarfile
        >>> tar_filter = rename("zotero-7.0.1")
        >>> with tarfile.open("archive.tar.gz", "r:gz") as tar:
        ...     tar.extractall(path="/extract/path", filter=tar_filter)
    """
    # Get the base filter from tarfile
    if base_filter:
        base = getattr(tarfile, base_filter)

    def rename_root_filter(tarinfo: tarfile.TarInfo, path: str) -> tarfile.TarInfo:
        """Filter that renames the root directory of the archive."""
        # Find the original root directory from the first component of the path
        if "/" in tarinfo.name:
            tarinfo.name = "/".join((root_dir, tarinfo.name.split("/", 1)[1]))
        else:
            tarinfo.name = root_dir

        # Apply base filter if specified
        if base is not None:
            tarinfo = base(tarinfo, path)
        return tarinfo

    return rename_root_filter
