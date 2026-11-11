#!/usr/bin/env bash
# 🔋 avisos cute de batería baja (15% y 5%), se reinicia al conectar el cargador
BAT=$(ls -d /sys/class/power_supply/BAT* 2>/dev/null | head -1)
[ -z "$BAT" ] && exit 0
warned=100
while sleep 60; do
  cap=$(<"$BAT/capacity"); st=$(<"$BAT/status")
  if [ "$st" != Discharging ]; then warned=100; continue; fi
  if [ "$cap" -le 5 ] && [ "$warned" -gt 5 ]; then
    notify-send -a angel -u critical -i battery-empty "🪫 ¡Batería al $cap%!" "Conéctame ya o me duermo… (╥﹏╥)"; warned=5
  elif [ "$cap" -le 15 ] && [ "$warned" -gt 15 ]; then
    notify-send -a angel -u normal -i battery-low "🔋 Batería al $cap%" "¿Me das cargador? ♡"; warned=15
  fi
done
