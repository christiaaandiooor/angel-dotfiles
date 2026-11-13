#!/usr/bin/env bash
# ♡ hotspot: compartir el internet de la lap (create_ap, interfaz virtual)
# uso: hotspot.sh {on|off|toggle|status|config}
THEME="$HOME/.config/rofi/angel-menu.rasi"
CONF="$HOME/.config/angel-hotspot.conf"      # nombre + contraseña (privado, no va al repo)
IFACE=wlp4s0
note() { notify-send -a osd -u low -t 3000 "$1" "$2"; }
ask() { rofi -dmenu "$@" -theme "$THEME" -theme-str 'listview{enabled:false;}' </dev/null; }

# por dónde sale el internet (cable si hay, si no el wifi)
inet_iface() { ip route show default | sort -t' ' -k9,9n -k11,11n | awk '{for(i=1;i<=NF;i++) if($i=="dev"){print $(i+1); exit}}'; }

running() { pgrep -x create_ap >/dev/null || pgrep -f "^/bin/bash /usr/bin/create_ap" >/dev/null; }

config() {
    local ssid pass
    ssid=$(ask -p "󰀃" -mesg "<b>Nombre del hotspot</b>
<span size='small' alpha='70%'>Así lo vas a ver en tu celular</span>" \
           -theme-str "entry{placeholder:\"Lap-$(whoami)\";}") || return 1
    [ -z "$ssid" ] && ssid="Lap-$(whoami)"
    while :; do
        pass=$(ask -password -p "󰌾" -mesg "<b>Contraseña</b>
<span size='small' alpha='70%'>Mínimo 8 letras ♡</span>" -theme-str 'entry{placeholder:"Contraseña ♡";}') || return 1
        (( ${#pass} >= 8 )) && break
        note "󰌾  Muy cortita (；ω；)" "Necesita mínimo 8 caracteres"
    done
    umask 077
    printf 'SSID=%q\nPASS=%q\n' "$ssid" "$pass" > "$CONF"
}

on() {
    running && { note "󰀃  El hotspot ya está prendido" ""; return; }
    [ -f "$CONF" ] || config || return
    # shellcheck disable=SC1090
    source "$CONF"
    note "󰀃  Prendiendo hotspot…" "Un momentito ✧"
    if pkexec /usr/bin/create_ap --daemon --logfile /tmp/angel-hotspot.log "$IFACE" "$(inet_iface)" "$SSID" "$PASS" >/dev/null 2>&1; then
        for _ in $(seq 20); do
            ip link show | grep -q "ap0\|x0$IFACE" && break
            grep -q "AP-ENABLED" /tmp/angel-hotspot.log 2>/dev/null && break
            sleep 0.5
        done
        if grep -q "AP-ENABLED" /tmp/angel-hotspot.log 2>/dev/null || running; then
            note "󰀃  Hotspot prendido ♡" "Conéctate a «$SSID» desde tu celular"
        else
            note "󰀃  No se pudo prender (；ω；)" "Revisa /tmp/angel-hotspot.log"
        fi
    else
        note "󰀃  No se pudo prender (；ω；)" "Revisa /tmp/angel-hotspot.log"
    fi
}

off() {
    running || { note "󰀃  El hotspot ya estaba apagado" ""; return; }
    pkexec /usr/bin/create_ap --stop "$IFACE" >/dev/null 2>&1
    note "󰀃  Hotspot apagado" "(˘ω˘)"
}

case "${1:-toggle}" in
    on) on ;;
    off) off ;;
    toggle) if running; then off; else on; fi ;;
    status) running && echo on || echo off ;;
    config) config && note "󰀃  Hotspot guardado ♡" "Se usa la próxima vez que lo prendas" ;;
esac
