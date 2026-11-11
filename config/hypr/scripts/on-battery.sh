#!/bin/sh
# Ejecuta el comando solo si la lap NO está conectada a la corriente.
for f in /sys/class/power_supply/*/online; do
    [ "$(cat "$f" 2>/dev/null)" = 1 ] && case "$f" in *ADP*|*AC*) exit 0;; esac
done
exec sh -c "$*"
