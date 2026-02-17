#!/bin/sh
set -e

apk add git \
	alpine-sdk \
	font-dejavu \
	ghostscript \
	libpq-dev \
	mariadb-dev \
	pango \
	py3-tox \
	python3-dev

tox "$@"
