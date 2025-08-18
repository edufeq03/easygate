"""Top-level package for FAB CoreUI Theme."""

__author__ = """Jillian Rowe"""
__email__ = "jillian@dabbleofdevops.com"
__version__ = "0.1.0"

from . import _version

__version__ = _version.get_versions()["version"]

from .fab_coreui_theme import (
    TEMPLATE_FOLDER,
    STATIC_FOLDER,
    STATIC_URL_PATH,
    coreui_bp,
    CoreUIBaseView,
    CoreUIModelView,
    CoreUISimpleFormView,
)
