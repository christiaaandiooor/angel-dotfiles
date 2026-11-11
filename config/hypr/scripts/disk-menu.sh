#!/usr/bin/env bash
# 🎀 menú de disco con rofi
THEME="$HOME/.config/rofi/angel-menu.rasi"
menu() { rofi -dmenu -i -markup-rows -format i -theme "$THEME" "$@"; }
note() { notify-send -a osd -u low -t 2500 "$1" "$2"; }
open() { setsid dolphin "$1" >/dev/null 2>&1 & }
bar() { local p=$1 n=$(( $1 / 10 )) c='#c3a6f5'; (( p >= 85 )) && c='#e8963a'; (( p >= 95 )) && c='#ff5fae'
        printf "<span color='%s'>%s</span><span alpha='35%%'>%s</span>" "$c" "$(printf '▰%.0s' $(seq 1 $n))" "$(printf '▱%.0s' $(seq 1 $((10-n))))"; }
human() { numfmt --to=iec --suffix=B "$1" 2>/dev/null || echo "${1}B"; }

main() {
    local mesg="" line
    while read -r src size used avail pct mnt; do
        p=${pct%\%}
        name=$mnt; [ "$mnt" = / ] && name="sistema"; [ "$mnt" = /boot ] && name="arranque"
        mesg+="<b>$name</b>  <span alpha='60%' size='small'>$mnt</span>
$(bar "$p")  <b>$pct</b>  <span size='small' alpha='70%'>$avail libres</span>

"
    done < <(df -h --output=source,size,used,avail,pcent,target -x tmpfs -x devtmpfs -x efivarfs -x overlay -x squashfs | tail -n +2 | grep '^/dev/' | sort -u -k6,6)
    mesg=$(printf "%s" "$mesg" | sed -e :a -e '/^\n*$/{$d;N;ba' -e '}')

    local trash="$HOME/.local/share/Trash" thumbs="$HOME/.cache/thumbnails"
    local tsize csize
    tsize=$(du -sb "$trash" 2>/dev/null | cut -f1); tsize=${tsize:-0}
    csize=$(du -sb "$thumbs" 2>/dev/null | cut -f1); csize=${csize:-0}

    rows=("󰉋  Abrir mis archivos"
          "󰋊  ¿qué ocupa espacio?  <span alpha='55%' size='small'>en tu carpeta</span>"
          "󰩺  Vaciar papelera  <span alpha='55%' size='small'>$(human "$tsize")</span>"
          "󰃢  Borrar miniaturas  <span alpha='55%' size='small'>$(human "$csize")</span>"
          "<span alpha='70%'>󰙅  análisis a fondo (terminal)</span>")
    sel=$(printf '%s\n' "${rows[@]}" | menu -p "󰋊" -mesg "$mesg") || exit
    case $sel in
        0) open "$HOME" ;;
        1) biggest "$HOME" ;;
        2) confirm "¿Vaciar la papelera? ($(human "$tsize"))" && { rm -rf "$trash"/files/* "$trash"/files/.[!.]* "$trash"/info/* 2>/dev/null; note "󰩺  Papelera vacía ✧" "Liberaste $(human "$tsize")"; } ;;
        3) confirm "¿Borrar miniaturas? ($(human "$csize")) se vuelven a crear solas" && { rm -rf "$thumbs"/* 2>/dev/null; note "󰃢  Miniaturas borradas ✧" "Liberaste $(human "$csize")"; } ;;
        4) setsid kitty --class floating-gdu -e gdu "$HOME" >/dev/null 2>&1 & ;;
    esac
}

biggest() {
    local dir=$1
    note "󰋊  Midiendo carpetas…" "Un momentito ✧"
    mapfile -t items < <(du -xsb "$dir"/* "$dir"/.[!.]* 2>/dev/null | sort -rn | head -12)
    local total=0 rows=() paths=()
    for it in "${items[@]}"; do total=$(( total + ${it%%$'\t'*} )); done
    (( total == 0 )) && total=1
    for it in "${items[@]}"; do
        b=${it%%$'\t'*}; p=${it#*$'\t'}; pc=$(( b * 100 / total ))
        icon="󰉋"; [ -f "$p" ] && icon="󰈔"
        rows+=("$icon  $(basename "$p" | sed 's/&/\&amp;/g;s/</\&lt;/g')  <span alpha='55%' size='small'>$(human "$b")</span>  $(bar "$pc")")
        paths+=("$p")
    done
    rows+=("<span alpha='70%'>󰅖  volver</span>")
    sel=$(printf '%s\n' "${rows[@]}" | menu -p "󰋊" -mesg "<b>Lo que más pesa</b> en ${dir/#$HOME/~}
<span size='small' alpha='70%'>click para entrar · las carpetas se abren en dolphin si no hay más</span>") || exit
    if (( sel == ${#paths[@]} )); then main; return; fi
    p=${paths[sel]}
    if [ -d "$p" ] && [ -n "$(ls -A "$p" 2>/dev/null)" ]; then
        sub=$(printf '%s\n' "󰋊  Ver qué hay adentro" "󰉋  Abrir en dolphin" | menu -p "󰉋" -mesg "<b>$(basename "$p")</b>") || exit
        [ "$sub" = 0 ] && biggest "$p" || open "$p"
    else open "$(dirname "$p")"; fi
}

confirm() { [ "$(printf '%s\n' "󰄬  Sí" "󰅖  No" | menu -p "?" -mesg "<b>$1</b>")" = 0 ]; }

pkill -x rofi && exit 0
main
