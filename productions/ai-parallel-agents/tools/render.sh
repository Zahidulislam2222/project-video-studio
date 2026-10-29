#!/usr/bin/env bash
# Render one composition: tools/render.sh LongVideo out/long-landscape.mp4
set -euo pipefail
BX="${REMOTION_BROWSER:-/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell}"
npx remotion render src/index.ts "$1" "$2" --gl=swangle --concurrency="${CONCURRENCY:-4}" --crf=18 --codec=h264 --audio-codec=aac --audio-bitrate=192k --browser-executable="$BX" --log=error
