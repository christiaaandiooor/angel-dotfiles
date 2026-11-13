#!/usr/bin/env bash
# 🎀 menú de wifi con rofi
THEME="$HOME/.config/rofi/angel-menu.rasi"
menu() { rofi -dmenu -i -markup-rows -format i -theme "$THEME" "$@"; }
note() { notify-send -a osd -u low -t 2500 "$1" "$2"; }

sig_icon() { local s=$1
    if   (( s >= 75 )); then echo "󰤨"; elif (( s >= 50 )); then echo "󰤥"
    elif (( s >= 25 )); then echo "󰤢"; else echo "󰤟"; fi; }
esc() { sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g' <<<"$1"; }

main() {
    local radio rescan="${1:-no}"
    radio=$(nmcli radio wifi)
    if [ "$radio" != enabled ]; then
        sel=$(printf '%s\n' "󰖩  Prender wifi" "󰒓  Ajustes avanzados" |
              menu -p "󰖪" -mesg "<b>Wifi apagado</b>  (˘ω˘) zzz") || exit
        case $sel in
            0) nmcli radio wifi on; note "󰖩  Wifi prendido" "Buscando redes ✧"; sleep 2; main yes ;;
            1) setsid nm-connection-editor >/dev/null 2>&1 & ;;
        esac; return
    fi

    local cur ip
    cur=$(nmcli -t -f ACTIVE,SSID dev wifi | awk -F: '$1=="yes"{sub(/^yes:/,""); print; exit}')
    ip=$(ip -4 -o addr show scope global | awk '{print $4; exit}')
    local mesg
    if [ -n "$cur" ]; then mesg="<b>󰖩  $(esc "$cur")</b>
<span size='small' alpha='70%'>conectada ✧ ${ip%/*}</span>"
    else mesg="<b>󰖪  sin conexión</b>  (；ω；)
<span size='small' alpha='70%'>elige una red ♡</span>"; fi

    # redes (sin repetir, la de mejor señal primero)
    mapfile -t nets < <(nmcli -t -e no -f IN-USE,SIGNAL,SECURITY,SSID dev wifi list --rescan "$rescan" |
        awk -F: '{ssid=$0; sub(/^[^:]*:[^:]*:[^:]*:/,"",ssid); if(ssid=="")next;
                  if(!(ssid in seen)||$1=="*"){seen[ssid]=1; print $2":"$3":"($1=="*"?1:0)":"ssid}}' |
        sort -t: -k3,3nr -k1,1nr | awk -F: '{k=$0; sub(/^[^:]*:[^:]*:[^:]*:/,"",k); if(!(k in s)){s[k]=1;print}}')
    mapfile -t saved < <(nmcli -t -f NAME,TYPE con show | awk -F: '$2=="802-11-wireless"{print $1}')

    local rows=() ssids=()
    for n in "${nets[@]}"; do
        IFS=: read -r s sec on ssid <<<"$n"
        local lock="" extra=""
        [[ -n "$sec" && "$sec" != "--" ]] && lock="  <span alpha='55%'>󰌾</span>"
        printf '%s\n' "${saved[@]}" | grep -qxF "$ssid" && extra="  <span alpha='55%' size='small'>guardada</span>"
        if (( on )); then rows+=("$(sig_icon "$s")  <b>$(esc "$ssid")</b>  <span color='#e25da4'>✓</span>$lock")
        else rows+=("$(sig_icon "$s")  $(esc "$ssid")$lock$extra"); fi
        ssids+=("$ssid")
    done
    local nnet=${#rows[@]} hs
    if [ "$("$HOME/.config/hypr/scripts/hotspot.sh" status)" = on ]; then
        hs="<span color='#e25da4'>󰀃  Hotspot prendido</span>  <span alpha='55%' size='small'>Toca para apagar</span>"
    else hs="<span alpha='70%'>󰀃  Compartir internet (hotspot)</span>"; fi
    rows+=("$hs"
           "<span alpha='70%'>󰒓  Cambiar nombre/contraseña del hotspot</span>"
           "<span alpha='70%'>󰑓  buscar redes otra vez</span>"
           "<span alpha='70%'>󰖪  apagar wifi</span>"
           "<span alpha='70%'>󰒓  ajustes avanzados</span>")

    sel=$(printf '%s\n' "${rows[@]}" | menu -p "󰖩" -mesg "$mesg") || exit
    if (( sel < nnet )); then net_action "${ssids[sel]}" "$cur"
    else case $((sel - nnet)) in
        0) "$HOME/.config/hypr/scripts/hotspot.sh" toggle ;;
        1) "$HOME/.config/hypr/scripts/hotspot.sh" config ;;
        2) note "󰑓  Buscando redes…" "Un momentito ✧"; main yes ;;
        3) nmcli radio wifi off; note "󰖪  Wifi apagado" "(˘ω˘) zzz" ;;
        4) setsid nm-connection-editor >/dev/null 2>&1 & ;;
    esac; fi
}

net_action() {
    local ssid=$1 cur=$2
    if [ "$ssid" = "$cur" ]; then
        local info; info=$(nmcli -t -f IP4.ADDRESS,IP4.GATEWAY dev show "$(nmcli -t -f DEVICE,TYPE dev | awk -F: '$2=="wifi"{print $1;exit}')" | sed 's/^[^:]*://' | paste -sd' ')
        sel=$(printf '%s\n' "󰖪  Desconectar" "󰆴  Olvidar esta red" "󰅖  Volver" |
              menu -p "󰖩" -mesg "<b>$(esc "$ssid")</b>
<span size='small' alpha='70%'>$info</span>") || exit
        case $sel in
            0) nmcli con down id "$ssid" >/dev/null && note "󰖪  Desconectada" "$ssid" ;;
            1) nmcli con delete id "$ssid" >/dev/null && note "󰆴  Red olvidada" "$ssid" ;;
            2) main ;;
        esac; return
    fi
    if nmcli -t -f NAME con show | grep -qxF "$ssid"; then
        note "󰖩  Conectando…" "$ssid ✧"
        if nmcli con up id "$ssid" >/dev/null 2>&1; then note "󰖩  ¡conectada! ♡" "$ssid"; return; fi
        nmcli con delete id "$ssid" >/dev/null 2>&1   # contraseña vieja/mala: la volvemos a pedir
    fi
    local pass=""
    local sec; sec=$(nmcli -t -e no -f SECURITY,SSID dev wifi list --rescan no | awk -v s="$ssid" '{k=$0; sub(/^[^:]*:/,"",k); if(k==s){split($0,a,":"); print a[1]; exit}}')
    if [[ -n "$sec" && "$sec" != "--" ]]; then
        pass=$(rofi -dmenu -password -p "󰌾" -theme "$THEME" -theme-str 'listview{enabled:false;} entry{placeholder:"Contraseña ♡";}' \
               -mesg "<b>$(esc "$ssid")</b>
<span size='small' alpha='70%'>escribe la contraseña y dale enter</span>" </dev/null) || exit
    fi
    note "󰖩  Conectando…" "$ssid ✧"
    if nmcli dev wifi connect "$ssid" ${pass:+password "$pass"} >/dev/null 2>&1; then note "󰖩  ¡conectada! ♡" "$ssid"
    else nmcli con delete id "$ssid" >/dev/null 2>&1; note "󰖪  No se pudo conectar (；ω；)" "¿La contraseña está bien?"; fi
}

pkill -x rofi && exit 0
(nmcli dev wifi rescan >/dev/null 2>&1 &)
main
