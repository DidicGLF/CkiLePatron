#!/usr/bin/env bash
export LD_LIBRARY_PATH="/nix/store/ba1mvpjflnmy15qhb3jpjzjgdyvq51yp-gcc-14.3.0-lib/lib"
exec /home/didic/.venv-ckilepatron/bin/python "$(dirname "$0")/app.py" "$@"
