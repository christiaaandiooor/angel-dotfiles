#!/bin/sh
# Ejecuta el comando solo si la lap SÍ está conectada a la corriente.
for f in /sys/class/power_supply/*/online; do
    [ "$(cat "$f" 2>/dev/null)" = 1 ] && case "$f" in *ADP*|*AC*) exec sh -c "$*";; esac
done
exit 0
