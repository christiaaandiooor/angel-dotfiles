#!/usr/bin/env bash
# 🪟 vista general (SUPER+Tab): miniaturas en vivo de todas las ventanas, de todos los escritorios
C="${XDG_RUNTIME_DIR:-/tmp}/angel-overview"; rm -rf "$C"; mkdir -p "$C"
mapfile -t rows < <(hyprctl clients -j | jq -r '
  sort_by(.workspace.id, .at[0]) | .[] | select(.mapped and (.class|startswith("showcase-")|not))
  | [.address, .stableId, (.workspace.name), .class, (.title|gsub("[\t\n]";" "))] | @tsv')
[ ${#rows[@]} -eq 0 ] && { notify-send -a angel "🪟 Vista general" "No hay ventanas abiertas ♡"; exit 0; }

# capturas en paralelo (funciona aunque la ventana esté en otro escritorio)
for r in "${rows[@]}"; do
  IFS=$'\t' read -r addr sid ws cls title <<<"$r"
  ( grim -T "$sid" -s 0.35 "$C/$sid.png" 2>/dev/null \
      && magick "$C/$sid.png" -resize 320x200 -background none -gravity center -extent 320x200 "$C/$sid.png" ) &
done; wait

pick=$(for r in "${rows[@]}"; do
  IFS=$'\t' read -r addr sid ws cls title <<<"$r"
  [[ "$ws" == special:minimized ]] && ws="minimizada" || ws="${ws#special:}"
  icon="$C/$sid.png"; [ -s "$icon" ] || icon="$(tr '[:upper:]' '[:lower:]' <<<"$cls")"
  t="${title:0:28}"; printf '%s  ·  %s\0icon\x1f%s\n' "$ws" "${t:-$cls}" "$icon"
done | rofi -dmenu -i -show-icons -format i -p "󰕰" -theme ~/.config/rofi/angel-overview.rasi)
[ -z "$pick" ] && exit 0
IFS=$'\t' read -r addr sid ws _ <<<"${rows[$pick]}"
if [[ "$ws" == special:* ]]; then   # minimizada / escondida: la traigo al escritorio actual
  cur=$(hyprctl activeworkspace -j | jq -r .id)
  hyprctl dispatch "hl.dsp.window.move({ workspace = \"$cur\", window = \"address:$addr\" })" >/dev/null
fi
hyprctl dispatch "hl.dsp.focus({ window = \"address:$addr\" })" >/dev/null
