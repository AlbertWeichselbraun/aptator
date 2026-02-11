from aptator.actions.deb import install_deb


def run(source, cfg, installed_version):
    """Install a .deb package from the given source."""

    latest_asset = source.get_latest_release_asset(allow_prerelease=cfg.get("prerelease", False))
    release_version = source.get_asset_version(latest_asset)
    if installed_version == release_version:
        print(f"  already installed (version {installed_version})")
        return

    deb_path = source.download_and_verify_asset(latest_asset)
    install_deb(deb_path)
