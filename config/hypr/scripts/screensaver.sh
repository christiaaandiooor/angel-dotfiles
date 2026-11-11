#!/usr/bin/env bash
# ✧ protector de pantalla: screensaver.sh {start|stop}
PIDF="${XDG_RUNTIME_DIR:-/tmp}/angel-screensaver.pid"
case "$1" in
  start) [ -f "$PIDF" ] && kill -0 "$(cat "$PIDF")" 2>/dev/null && exit 0
         python3 ~/.config/hypr/widgets/angel-screensaver.py & echo $! > "$PIDF" ;;
  stop)  [ -f "$PIDF" ] && kill "$(cat "$PIDF")" 2>/dev/null; rm -f "$PIDF" ;;
esac
