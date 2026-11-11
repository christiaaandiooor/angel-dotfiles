#!/usr/bin/env bash
# 🎀 historial del portapapeles (SUPER+SHIFT+V)
WIPE="󰆴  Borrar todo el historial"
sel=$( { cliphist list; printf '%s\n' "$WIPE"; } | rofi -dmenu -i -p "󰅌" -display-columns 2 -display-column-separator "\t" \
       -theme ~/.config/rofi/angel-menu.rasi -theme-str 'entry { placeholder: "¿Qué pegamos? ♡"; } window { width: 560px; }' )
[ -z "$sel" ] && exit 0
if [ "$sel" = "$WIPE" ]; then
  cliphist wipe && notify-send "🎀 Portapapeles" "Historial borrado ♡"
else
  printf '%s' "$sel" | cliphist decode | wl-copy
fi
