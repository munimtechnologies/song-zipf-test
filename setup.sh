#!/bin/sh
# Setup for the song-zipf OCR + analysis job (Debian-based python:3.12 image).
# MV2, Munim, Inc.; made with AI agents. Apache-2.0.
set -e
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends tesseract-ocr tesseract-ocr-eng >/dev/null
tesseract --version
pip install --no-cache-dir -r requirements.txt
