#!/bin/sh
set -e

apk add \
	alpine-sdk \
	font-dejavu \
	ghostscript \
	git \
	libxslt-dev \
	mariadb-dev \
	pango
pip install tox

# Ownership in the host and container don't match.
git config --global --add safe.directory /src

export CI=true
tox --colored=yes "$@"
