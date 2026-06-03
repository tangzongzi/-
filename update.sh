#!/bin/bash
# 项目根的 update.sh - 转发到 scripts/update.sh
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
bash "$SCRIPT_DIR/scripts/update.sh" "$@"
