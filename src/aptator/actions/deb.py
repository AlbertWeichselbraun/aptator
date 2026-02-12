
from aptator import AptatorConfig
from aptator.tools import run

SUDO = AptatorConfig.paths.sudo


def install_deb(path):
    """Install a .deb package using dpkg."""
    run([SUDO, "/usr/bin/dpkg", "-i", path])
