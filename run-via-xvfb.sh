#!/bin/bash
xvfb-run --auto-servernum -s '-screen 0 1920x1080x24' python -u ./demo.py 2>&1
