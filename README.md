# aptator

A lightweight Python utility to automatically check and install the latest releases of applications from GitHub repositories as Debian packages.

## Features

- **Automatic version checking**: Compares installed package versions against the latest GitHub release
- **Selective installation**: Uses regex patterns to match specific `.deb` assets from releases
- **XDG config directory support**: Stores configuration in `~/.config/aptator/aptator.toml`
- **TOML configuration**: Human-readable configuration format using Python's built-in `tomllib`
- **Standard library only**: No external dependencies (Python 3.11+)
- **Error handling**: Graceful error reporting for individual package failures

## Requirements

- Python 3.11 or later
- Debian-based Linux distribution with `dpkg` and `sudo`
- Network access to GitHub API

## Installation

```bash
pipx install aptator
```

## Configuration

Configuration is stored in `~/.config/aptator/aptator.toml` and uses TOML format.

### Configuration Format

```toml
[[packages]]
name = "Display Name"
repo = "owner/repository"
asset_pattern = ".*_amd64\\.deb$"
package_name = "debian-package-name"
action = { type = "deb-install" }
```

### Configuration Fields

- **name**: Human-readable name of the application
- **repo**: GitHub repository in the format `owner/repository`
- **asset_pattern**: Regular expression pattern to match the desired `.deb` asset filename
- **asset_version_pattern**: Regular expression pattern to extract the version from the asset filename. Should contain one capture group `()` for the version string. Defaults to `(.*)` (entire filename as version). Optional.
- **prerelease**: Boolean to allow pre-release versions. Defaults to `false`. Optional.
- **action**: The `action` option specifies what should be done with the downloaded asset. It determines how the asset is processed, installed, or linked. Below are the supported `action` types and their descriptions:
  - Depending on the `type`, additional fields may be required (e.g., `command` for `exec`, `url` for `download-extract-and-link`).
  - This modular approach allows `aptator` to support a wide range of installation and setup workflows.

#### Supported Action Types

1. **`deb-install`**
   - Installs the downloaded `.deb` package using `dpkg`.
   - Example:
     ```toml
     action = { type = "deb-install" }
     ```

2. **`exec`**
   - Executes a custom shell command.
   - Example:
     ```toml
     action = { type = "exec", command = "sudo apt update && sudo apt install -y example" }
     ```

3. **`download-extract-and-link`**
   - Downloads an asset, extracts it to a specified directory, and creates a symbolic link.
   - Fields:
     - `url`: The URL to download the asset from.
     - `extract_to`: The directory where the asset will be extracted.
     - `link_to`: The target location for the symbolic link.
   - Example:
     ```toml
     action = { type = "download-extract-and-link", url = "https://example.com/app.tar.gz", extract_to = "/opt", link_to = "/usr/local/bin/app" }
     ```

### Asset Version Pattern Examples

The `asset_version_pattern` uses regex capture groups to extract the version from the asset filename:

```toml
# Extract version from "freetube-0.19.1_amd64.deb"
# Result: 0.19.1
asset_version_pattern = "freetube-([0-9.]+)"

# Extract version from "app-v1.2.3-beta_amd64.deb"
# Result: v1.2.3-beta
asset_version_pattern = "app-(v[0-9.]+-beta)"

# Use entire filename as version (default)
# Result: app_1.0.0_amd64.deb
asset_version_pattern = "(.*)"
```

### Example Configuration

```toml
# FreeTube - Privacy-focused YouTube client
[[packages]]
name = "FreeTube"
repo = "FreeTubeApp/FreeTube"
asset_pattern = ".*_amd64\\.deb$"
asset_version_pattern = "FreeTube-([0-9.]+)"
prerelease = false
action = { type = "deb-install" }

# Add more packages as needed
[[packages]]
name = "Example App"
repo = "owner/repo"
asset_pattern = ".*\\.deb$"
asset_version_pattern = "([0-9.]+)"  # Extract semver
prerelease = false
action = { type = "deb-install" }
```

### Example: Zotero Configuration

The following example demonstrates how to configure Zotero using the `download-extract-and-link` action:

```toml
[[packages]]
name = "Zotero"
repo = "zotero/zotero"
asset_pattern = "\\.tar.gz$"
asset_version_pattern = "(.*).tar.gz"
use_tag = true
action = { type = "download-extract-and-link", url = "https://www.zotero.org/download/client/dl?channel=release&platform=linux-x86_64", extract_to = "/opt", link_to = "/opt/zotero" }
```

This configuration will:
1. Download the Zotero tarball from the specified URL.
2. Extract it to `/opt`.
3. Create a symbolic link to `/opt/zotero` for easier access.

