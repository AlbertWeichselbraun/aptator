# aptator

A lightweight Python utility to automatically check and install the latest releases of applications from GitHub repositories as Debian packages.

## Features

- **Automatic version checking**: Compares installed package versions against the latest GitHub release
- **Selective installation**: Uses regex patterns to match specific `.deb` assets from releases
- **XDG config directory support**: Stores configuration in `~/.config/aptator/aptator.toml`
- **TOML configuration**: Human-readable configuration format using Python's built-in `tomllib`
- **Standard library only**: No external dependencies (Python 3.11+)
- **Error handling**: Graceful error reporting for individual package failures

## Installation

1. Clone or download the repository
2. Make the script executable:
   ```bash
   chmod +x aptator.py
   ```
3. Optionally install as a system tool (requires root):
   ```bash
   sudo cp aptator.py /usr/local/bin/aptator
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
```

### Configuration Fields

- **name**: Human-readable name of the application
- **repo**: GitHub repository in the format `owner/repository`
- **asset_pattern**: Regular expression pattern to match the desired `.deb` asset filename
- **asset_version_pattern**: Regular expression pattern to extract the version from the asset filename. Should contain one capture group `()` for the version string. Defaults to `(.*)` (entire filename as version). Optional.
- **package_name**: Debian package name (as it appears in `dpkg`)
- **prerelease**: Boolean to allow pre-release versions. Defaults to `false`. Optional.

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
package_name = "freetube"
prerelease = false

# Add more packages as needed
[[packages]]
name = "Example App"
repo = "owner/repo"
asset_pattern = ".*\\.deb$"
asset_version_pattern = "([0-9.]+)"  # Extract semver
package_name = "example-app"
prerelease = false
```

## Usage

Run the script directly:

```bash
python3 aptator.py
```

Or if installed as a system tool:

```bash
aptator
```

The script will:
1. Read the configuration from `~/.config/aptator/aptator.toml`
2. Check each configured package for updates
3. Download and install new versions as needed
4. Report the status of each package

### Sample Output

```
Checking FreeTube (FreeTubeApp/FreeTube)
  updating from 0.19.1 to 0.20.0
  installing 0.20.0
Checking Example App (owner/repo)
  up to date (1.2.3)
```

## Requirements

- Python 3.11 or later
- Debian-based Linux distribution with `dpkg` and `sudo`
- Network access to GitHub API
