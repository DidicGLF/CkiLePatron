#!/usr/bin/env bash
export LD_LIBRARY_PATH="/nix/store/ybp235ps7m4yd85v0pgvqkhd4xmxf6jq-gcc-14.3.0-lib/lib"
exec /home/didic/.venv-ckilepatron/bin/python "$(dirname "$0")/app.py" "$@"
