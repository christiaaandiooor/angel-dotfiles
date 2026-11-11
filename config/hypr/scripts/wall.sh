#!/usr/bin/env bash
# 🎀 selector de wallpapers angel (SUPER+W)
# usa miniaturas en ~/.cache/angel-walls; aplica en pcmanfm-qt (escritorio) + hyprpaper
DIR="$HOME/Pictures/wallpapers"
CACHE="$HOME/.cache/angel-walls"
CONF="$HOME/.config/hypr/hyprpaper.conf"
mkdir -p "$CACHE"

# modo directo (lo usa el motor de temas): wall.sh --set RUTA
if [ "$1" = "--set" ] && [ -f "$2" ]; then SET="$2"; fi

mapfile -t walls < <(find "$DIR" -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.webp' \) | sort)
[ ${#walls[@]} -eq 0 ] && { notify-send "🎀 Wallpapers" "No encontré nada en $DIR"; exit 1; }

list() {
  for w in "${walls[@]}"; do
    t="$CACHE/$(printf '%s' "$w" | md5sum | cut -c1-16).png"
    [ -s "$t" ] && [ "$t" -nt "$w" ] || magick "$w[0]" -thumbnail 360x200^ -gravity center -extent 360x200 "$t" 2>/dev/null
    name="${w#$DIR/}"; name="${name%.*}"
    printf '%s\0icon\x1f%s\n' "$name" "$t"
  done
}

if [ -n "$SET" ]; then w="$SET"; else
auto=$(python3 -c "import json;print(json.load(open('$HOME/.config/angel-theme/state.json')).get('auto',False))" 2>/dev/null)
[ "$auto" = True ] && lbl="Colores del wallpaper: activados ✧" || lbl="Colores del wallpaper: desactivados"
ic="$CACHE/_auto.png"; [ -s "$ic" ] || magick -size 360x200 gradient:'#ff8fc8'-'#8fcff7' -rotate 90 -resize 360x200! "$ic"
i=$( { printf '%s\0icon\x1f%s\n' "$lbl" "$ic"; list; } | rofi -dmenu -i -show-icons -format i -p "󰸉" -theme ~/.config/rofi/angel-walls.rasi)
[ -z "$i" ] && exit 0
if [ "$i" = 0 ]; then exec ~/.config/angel-theme/theme.py auto; fi
w="${walls[$((i - 1))]}"
fi

# escritorio de pcmanfm-qt (por si algún día dibuja su propio fondo)
pgrep -x pcmanfm-qt >/dev/null && pcmanfm-qt --profile=default --set-wallpaper="$w" --wallpaper-mode=zoom
# hyprpaper (es el que se ve) — necesita el nombre del monitor; + que se quede al reiniciar
for m in $(hyprctl monitors -j | jq -r '.[].name'); do
  hyprctl hyprpaper wallpaper "$m,$w,cover" >/dev/null
done
sed -i "s|^\(\s*path\s*=\).*|\1 $w|" "$CONF"

[ -n "$SET" ] && exit 0
notify-send -i "$w" "🎀 Wallpaper nuevo" "$(basename "$w") ♡"
~/.config/angel-theme/theme.py wall "$w"   # recuerda el fondo del modo (y recolorea si está en automático)
