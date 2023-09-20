from __future__ import annotations

from . import version  # type: ignore # noqa: PGH003

__version__ = version.version

default_app_config = "django_afip.apps.AfipConfig"
