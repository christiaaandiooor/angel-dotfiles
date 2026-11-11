#!/usr/bin/env bash
# textos para hyprlock: música, batería y frase
case "$1" in
  music)
    st=$(playerctl status 2>/dev/null) || exit 0
    [ "$st" = Playing ] || [ "$st" = Paused ] || exit 0
    t=$(playerctl metadata title 2>/dev/null | cut -c1-40); a=$(playerctl metadata artist 2>/dev/null | cut -c1-30)
    ic=$([ "$st" = Playing ] && echo "󰎈" || echo "󰏤")
    echo "$ic  $t${a:+  ·  $a}" ;;
  battery)
    B=$(ls -d /sys/class/power_supply/BAT* 2>/dev/null | head -1); [ -z "$B" ] && exit 0
    c=$(<"$B/capacity"); s=$(<"$B/status")
    if [ "$s" = Charging ]; then ic="󰂄"; elif (( c > 80 )); then ic="󰁹"; elif (( c > 50 )); then ic="󰂀"; elif (( c > 20 )); then ic="󰁾"; else ic="󰂃"; fi
    echo "$ic  $c%" ;;
  frase)
    f=("Te estaba esperando ♡" "Qué bueno verte de vuelta ✧" "Un descansito y a seguir (˘ω˘)"
       "Todo bien guardadito aquí ♡" "Tu escritorio te extrañó ✧" "Respira, ya volviste (｡•ᴗ•｡)")
    echo "${f[$(( $(date +%j) % ${#f[@]} ))]}" ;;
esac
