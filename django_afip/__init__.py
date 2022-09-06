try:
    from . import version  # type: ignore

    __version__ = version.version
except:
    pass

default_app_config = "django_afip.apps.AfipConfig"
