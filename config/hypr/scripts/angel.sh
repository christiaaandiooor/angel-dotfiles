#!/usr/bin/env bash
# 🎀 angel.sh — utilidades cute para Hyprland
# uso: angel.sh {vol-up|vol-down|vol-mute|bri-up|bri-down|shot-area|shot-full|shot-edit|bar-reload|keys|wifi-toggle|bt-toggle}

SHOTS="$HOME/Pictures/Screenshots"
osd() { # $1 icono/título  $2 valor 0-100
    notify-send -a osd -u low -t 1200 \
        -h string:x-canonical-private-synchronous:angel-osd \
        -h int:value:"$2" "$1" "$2%"
}
vol() { wpctl get-volume @DEFAULT_AUDIO_SINK@ | awk '{print int($2*100)}'; }
muted() { wpctl get-volume @DEFAULT_AUDIO_SINK@ | grep -q MUTED; }
bri() { brightnessctl -m | awk -F, '{gsub("%","",$4); print $4}'; }

case "$1" in
    vol-up)   wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+; osd "󰕾  Volumen ♪" "$(vol)" ;;
    vol-down) wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-;      osd "󰖀  Volumen ♪" "$(vol)" ;;
    vol-mute) last="$HOME/.cache/angel-vol-last"
              echo "$(date '+%F %T') vol-mute llamado por: $(ps -o args= -p $PPID | cut -c1-80)" >> "$HOME/.cache/angel-mute.log"
              if muted; then
                  # al desmutear: regresa al volumen de antes (o 40% si no hay guardado y está al 100)
                  v=$(cat "$last" 2>/dev/null)
                  if [ -n "$v" ]; then wpctl set-volume @DEFAULT_AUDIO_SINK@ "$v"
                  elif [ "$(vol)" -ge 95 ]; then wpctl set-volume @DEFAULT_AUDIO_SINK@ 0.40; fi
                  wpctl set-mute @DEFAULT_AUDIO_SINK@ 0
              else
                  wpctl get-volume @DEFAULT_AUDIO_SINK@ | awk '{print $2}' > "$last"
                  wpctl set-mute @DEFAULT_AUDIO_SINK@ 1
              fi
              if muted; then notify-send -a osd -u low -t 1200 -h string:x-canonical-private-synchronous:angel-osd "󰝟  Shhh~" "Silenciado (˘ω˘)"
              else osd "󰕾  Volumen ♪" "$(vol)"; fi ;;
    bri-up)   brightnessctl -e4 -n2 set 5%+ >/dev/null; osd "󰃠  Brillo ☀" "$(bri)" ;;
    bri-down) brightnessctl -e4 -n2 set 5%- >/dev/null; osd "󰃞  Brillo ☀" "$(bri)" ;;
    shot-area|shot-full|shot-edit)
        mkdir -p "$SHOTS"; f="$SHOTS/$(date +%F_%H-%M-%S).png"
        if [ "$1" = shot-full ]; then grim "$f"; else
            g=$(slurp -b 'fff5fb55' -c 'ff8fc8ff' -s 'ff8fc822' -w 3) || exit 0
            grim -g "$g" "$f"
        fi
        wl-copy < "$f"
        [ "$1" = shot-edit ] && { swappy -f "$f" -o "$f"; exit; }
        notify-send -a screenshot -i "$f" "📸 ¡Click!" "Copiada al portapapeles ♡\n${f/#$HOME/\~}" ;;
    bar-reload-quiet) pkill -x waybar; sleep 0.4; hyprctl dispatch 'hl.dsp.exec_cmd("waybar")' >/dev/null ;;
    bar-reload) pkill waybar; sleep 0.3; setsid waybar >/dev/null 2>&1 &
                notify-send -a osd -u low "🎀 Waybar" "Recargada ✧" ;;
    keys) cat <<'EOF' | rofi -dmenu -i -p '󰌌 Atajos' -theme-str 'window {width: 600px;} listview {lines: 14;}' >/dev/null
SUPER + Q              Terminal (kitty)
SUPER + R              Lanzador de apps
SUPER + E              Archivos
SUPER + B              Firefox
SUPER + C              Cerrar ventana
SUPER + V              Flotar / acoplar
SUPER + F              Maximizar
SUPER + SHIFT + F      Pantalla completa
SUPER + J              Cambiar split
SUPER + 1..0           Ir a escritorio
SUPER + SHIFT + 1..0   Mover ventana a escritorio
3 dedos ← →            Cambiar de escritorio (touchpad)
4 dedos ↑              Vista general (touchpad)
SUPER + S              Scratchpad mágico ✨
SUPER + Tab            Vista general de ventanas
SUPER + H              Minimizar ventana
SUPER + SHIFT + H      Regresar minimizada
SUPER + N              Ventanas minimizadas
SUPER + D              Ver escritorio
SUPER + W              Elegir wallpaper
SUPER + SHIFT + A      Modo Ame / modo Angel ✧
SUPER + G              Modo showcase ✨
SUPER + SHIFT + D      Widgets del escritorio on/off
SUPER + SHIFT + P      Mascota on/off
SUPER + SHIFT + N      Luz nocturna on/off
SUPER + SHIFT + V      Historial del portapapeles
SUPER + PUNTO          Kaomojis (˘ω˘)
SUPER + SHIFT + C      Gotero de color (hyprpicker)
SUPER + L              Bloquear
SUPER + A              Centro de control ✧
SUPER + X              Menú de apagado
SUPER + SHIFT + W      Recargar waybar
Print                  Captura de área
SHIFT + Print          Captura completa
SUPER + SHIFT + Print  Captura + editar
SUPER + SHIFT + ←→↑↓   Mover ventana
SUPER + arrastrar      Mover con el mouse
SUPER + clic derecho   Cambiar tamaño
SUPER + /              Esta ayuda ♡
EOF
    ;;
    wifi-toggle)
        if [ "$(nmcli radio wifi)" = enabled ]; then nmcli radio wifi off; notify-send -a osd -u low -t 1500 "󰖪  Wifi apagado" "(˘ω˘) zzz"
        else nmcli radio wifi on; notify-send -a osd -u low -t 1500 "󰖩  Wifi prendido" "Buscando redes ✧"; fi ;;
    bt-toggle)
        if bluetoothctl show | grep -q "Powered: yes"; then bluetoothctl power off >/dev/null; notify-send -a osd -u low -t 1500 "󰂲  Bluetooth apagado" "(˘ω˘)"
        else rfkill unblock bluetooth 2>/dev/null; bluetoothctl power on >/dev/null; notify-send -a osd -u low -t 1500 "󰂯  Bluetooth prendido" "✧"; fi ;;
    *) echo "uso: $0 {vol-up|vol-down|vol-mute|bri-up|bri-down|shot-area|shot-full|shot-edit|bar-reload|keys|wifi-toggle|bt-toggle}"; exit 1 ;;
esac
