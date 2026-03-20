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

export CI=true
tox --colored=yes "$@"
