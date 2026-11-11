#!/usr/bin/env bash
# 🎀 minimizar ventanas en Hyprland (usa el workspace especial "minimized")
# uso: minimize.sh {hide|restore|restore-all|desktop|status}
THEME="$HOME/.config/rofi/angel-menu.rasi"
d() { hyprctl dispatch "$1" >/dev/null; }
cur() { hyprctl activeworkspace -j | jq -r .id; }
refresh() { pkill -RTMIN+9 waybar; }
mins() { hyprctl clients -j | jq -r '.[] | select(.workspace.name=="special:minimized") | "\(.address)\t\(.class)\t\(.title)"'; }
bring() { local w; w=$(cur); d "hl.dsp.window.move({ workspace = \"$w\", window = \"address:$1\" })"; d "hl.dsp.focus({ window = \"address:$1\" })"; }
esc() { sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g' <<<"$1"; }

case "$1" in
  hide)
    a=$(hyprctl activewindow -j | jq -r '.address // empty')
    [ -n "$a" ] && [ "$a" != null ] && d "hl.dsp.window.move({ workspace = \"special:minimized\", follow = false, window = \"address:$a\" })"
    refresh ;;
  restore)
    pkill -x rofi && exit 0
    mapfile -t L < <(mins)
    if (( ${#L[@]} == 0 )); then notify-send -a osd -u low -t 1500 "󰖯  No hay ventanas minimizadas" "(｡•ᴗ•｡)"; exit; fi
    rows=()
    for l in "${L[@]}"; do IFS=$'\t' read -r a c t <<<"$l"; rows+=("󰖯  <b>$(esc "$c")</b>  <span alpha='60%' size='small'>$(esc "${t:0:40}")</span>"); done
    rows+=("<span alpha='70%'>󰁜  regresar todas</span>")
    sel=$(printf '%s\n' "${rows[@]}" | rofi -dmenu -i -markup-rows -format i -p "󰖯" -theme "$THEME" \
          -mesg "<b>Ventanas minimizadas</b>  ${#L[@]}") || exit
    if (( sel == ${#L[@]} )); then "$0" restore-all; exit; fi
    bring "$(cut -f1 <<<"${L[sel]}")"; refresh ;;
  restore-all)
    mins | cut -f1 | while read -r a; do bring "$a"; done; refresh ;;
  desktop)  # mostrar escritorio: esconde todo lo del workspace actual / lo regresa
    w=$(cur); s="special:escritorio-$w"
    hidden=$(hyprctl clients -j | jq -r --arg s "$s" '.[] | select(.workspace.name==$s) | .address')
    if [ -n "$hidden" ]; then
        for a in $hidden; do d "hl.dsp.window.move({ workspace = \"$w\", window = \"address:$a\" })"; done
    else
        for a in $(hyprctl clients -j | jq -r --argjson w "$w" '.[] | select(.workspace.id==$w) | .address'); do
            d "hl.dsp.window.move({ workspace = \"$s\", follow = false, window = \"address:$a\" })"; done
    fi
    refresh ;;
  status)
    n=$(mins | grep -c .)
    w=$(cur); desk=$(hyprctl clients -j | jq --arg s "special:escritorio-$w" '[.[]|select(.workspace.name==$s)]|length')
    if (( n > 0 )); then printf '{"text":"󰖯 %s","class":"has","tooltip":"%s minimizada(s) ♡\\nClick: elegir cuál regresar\\nClick der: regresar todas"}\n' "$n" "$n"
    else printf '{"text":"󰖯","class":"none","tooltip":"No hay ventanas minimizadas\\n(SUPER+H para minimizar)"}\n'; fi ;;
  *) echo "uso: $0 {hide|restore|restore-all|desktop|status}"; exit 1 ;;
esac
