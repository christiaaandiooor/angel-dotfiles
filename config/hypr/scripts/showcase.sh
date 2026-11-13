#!/usr/bin/env bash
# ✨ modo showcase (SUPER+G): abre terminales acomodadas en un escritorio vacío para presumir el rice.
# Si ya está abierto, lo cierra y te regresa a donde estabas.
STATE="${XDG_RUNTIME_DIR:-/tmp}/angel-showcase.ws"
addrs=$(hyprctl clients -j | jq -r '.[] | select(.class|startswith("showcase-")) | .address')

if [ -n "$addrs" ]; then
  for a in $addrs; do hyprctl dispatch "hl.dsp.window.close({ window = \"address:$a\" })" >/dev/null; done
  [ -f "$STATE" ] && hyprctl dispatch "hl.dsp.focus({ workspace = \"$(cat "$STATE")\" })" >/dev/null
  rm -f "$STATE"; exit 0
fi

hyprctl activeworkspace -j | jq -r .id > "$STATE"
used=$(hyprctl workspaces -j | jq -r '.[] | select(.windows > 0) | .id')
ws=1; while grep -qx "$ws" <<<"$used"; do ws=$((ws + 1)); done

# medidas pensadas para 1920x1080 con la barra de arriba, el dock y hyprbars (26px)
hyprctl dispatch "hl.dsp.focus({ workspace = \"$ws\" })" >/dev/null
open() { # clase  x y w h  comando...  (van saliendo una por una ✧)
  local cls=$1 x=$2 y=$3 w=$4 h=$5; shift 5
  hyprctl dispatch "hl.dsp.exec_cmd(\"[workspace $ws silent; float; size $w $h; move $x $y] kitty --class showcase-$cls -o font_size=10 $*\")" >/dev/null
  sleep 0.15
}

# el lugar sorpresa: cada vez sale algo distinto
juguetes=(
  "cbonsai -l -i -w 1.5 -L 40"
  "lavat -g -c ff8fc8 -k c3a6f5 -s 3 -b 12 -r 4"
  "asciiquarium"
)
juguete=${juguetes[RANDOM % ${#juguetes[@]}]}

open ff     24   90  820 480  --hold sh -c "'sleep 0.5; ~/.config/fastfetch/centrado.py'"
open btop   858  90 1038 480  btop
open musica 24   610 400 380  ~/.config/hypr/scripts/showcase-musica.py
open cava   438  610 406 380  cava
open juguete 858 610 512 380  $juguete
open pipes  1384 610 512 170  pipes-rs --palette pastel -k curved -r 0.6 -p 3
open clock  1384 820 512 170  tty-clock -c -C 5 -s

# foto opcional: botón en la notificación
(
  sleep 1.5
  r=$(notify-send -a showcase -t 8000 -A foto="Tomar foto ♡" "Showcase listo ✧˖°" "¿Le tomo foto? (≧◡≦)")
  if [ "$r" = foto ]; then
    sleep 0.8
    mkdir -p ~/Pictures/showcase
    f=~/Pictures/showcase/showcase-$(date +%F_%H%M%S).png
    grim -o eDP-1 "$f" && wl-copy < "$f" && notify-send -a showcase -i "$f" "Foto guardada ♡" "Pictures/showcase (también en el portapapeles)"
  fi
) >/dev/null 2>&1 &
disown
