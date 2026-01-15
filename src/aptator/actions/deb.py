from subprocess import CalledProcessError

from aptator.tools import run


def install_deb(path):
    """Install a .deb package using dpkg."""
    run(["/usr/bin/sudo", "/usr/bin/dpkg", "-i", path])
