#!/usr/bin/env bash
# (˘ω˘) selector de kaomojis (SUPER + punto): elige uno y queda copiado
F=~/.config/hypr/kaomojis.txt
sel=$(awk -F'\t' '{printf "%s   <span alpha=\"55%%\" size=\"small\">%s</span>\n", $1, $2}' "$F" |
      rofi -dmenu -i -markup-rows -format i -p "(˘ω˘)" -theme ~/.config/rofi/angel-menu.rasi \
           -theme-str 'entry { placeholder: "Busca: feliz, gatito, abrazo… ♡"; } listview { lines: 10; } window { width: 520px; }')
[ -z "$sel" ] && exit 0
k=$(sed -n "$((sel + 1))p" "$F" | cut -f1)
printf '%s' "$k" | wl-copy
notify-send -a osd -u low -t 1500 "Kaomoji copiado ♡" "$k   (pégalo con Ctrl+V)"
