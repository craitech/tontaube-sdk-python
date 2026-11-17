class OutdatedSDKError(Exception):
    """Raised when the API returns HTTP 426 Upgrade Required."""
