#!/usr/bin/env bash
# 🎀 toggles del centro de control (swaync): cc.sh {wifi|bt} [status]
wifi_on() { [ "$(nmcli radio wifi)" = enabled ]; }
night_on() { pgrep -x hyprsunset >/dev/null; }
bt_on()   { bluetoothctl show 2>/dev/null | grep -q 'Powered: yes'; }
case "$1" in
  wifi) if [ "$2" = status ]; then wifi_on && echo true || echo false
        elif wifi_on; then nmcli radio wifi off; else nmcli radio wifi on; fi ;;
  bt)   if [ "$2" = status ]; then bt_on && echo true || echo false
        elif bt_on; then bluetoothctl power off >/dev/null; else bluetoothctl power on >/dev/null; fi ;;
  night) if [ "$2" = status ]; then night_on && echo true || echo false
        elif night_on; then pkill -x hyprsunset; notify-send -a angel "☀️ Luz normal" "Filtro nocturno apagado"
        elif command -v hyprsunset >/dev/null; then
          hyprctl dispatch 'hl.dsp.exec_cmd("hyprsunset -t 4300")' >/dev/null; notify-send -a angel "🌙 Luz cálida" "Filtro nocturno prendido ♡"
        else notify-send -a angel "🌙 Falta hyprsunset" "Corre: sudo pacman -S hyprsunset"; fi ;;
  ame)   if [ "$2" = status ]; then python3 -c "import json;print(str(json.load(open('$HOME/.config/angel-theme/state.json')).get('dark',False)).lower())" 2>/dev/null || echo false
        else ~/.config/angel-theme/theme.py toggle; fi ;;
esac
