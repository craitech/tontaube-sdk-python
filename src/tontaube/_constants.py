import platform
from .version import __version__

DEFAULT_BASE_URL = "https://api.tontaube.ai/v1"

DEFAULT_USER_AGENT = (
    f"tontaube-python/{__version__} (Python/{platform.python_version()})"
)

DEFAULT_TIMEOUT = 600.0
VERSION_CHECK_TIMEOUT = 2.0