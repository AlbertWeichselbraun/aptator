from pathlib import Path

class Source:

    def get_latest_release_asset(self, allow_prerelease: bool = False) -> dict:
        raise NotImplementedError
    
    def get_asset_version(self, asset):
        raise NotImplementedError
    
    def download_and_verify_asset(self, asset: dict) -> Path:
        raise NotImplementedError