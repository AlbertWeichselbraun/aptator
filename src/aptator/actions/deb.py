from subprocess import CalledProcessError

from aptator.tools import run


def install_deb(path):
    """Install a .deb package using dpkg."""
    run(["/usr/bin/sudo", "/usr/bin/dpkg", "-i", path])


def get_installed_version(pkg):
    """Get the installed version of a package, or None if not installed."""
    try:
        return run(["dpkg-query", "-W", "-f=${Version}", pkg])
    except CalledProcessError:
        return None
