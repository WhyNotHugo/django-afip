# noqa: INP001
# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
# -- Path setup --------------------------------------------------------------
# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
from __future__ import annotations

import os
import sys
from os.path import abspath
from os.path import dirname
from os.path import join

import django

import django_afip

BASE_DIR = dirname(dirname(abspath(__file__)))

sys.path.insert(0, abspath(join(dirname(__file__), "_ext")))
sys.path.insert(0, abspath(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "testapp.settings")

django.setup()

# -- Project information -----------------------------------------------------

project = "django-afip"
copyright = "2015-2022, Hugo Osvaldo Barrera"  # noqa: A001
author = "Hugo Osvaldo Barrera"

# The short X.Y version.
version = django_afip.__version__
# The full version, including alpha/beta/rc tags
release = django_afip.__version__


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "django_models",
    "sphinx.ext.intersphinx",
]

intersphinx_mapping = {
    "django": (
        "https://docs.djangoproject.com/en/stable/",
        "https://docs.djangoproject.com/en/stable/_objects/",
    ),
    "weasyprint": (
        "https://doc.courtbouillon.org/weasyprint/stable/",
        None,
    ),
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]


# The master toctree document.
master_doc = "index"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
# html_theme_options = {}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
