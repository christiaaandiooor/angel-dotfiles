#!/usr/bin/env bash
# 🎀 pone el splash angel al arrancar (solo cambia la imagen; no toca Windows ni el menú de arranque)
# Correr con:  sudo bash ~/.config/angel-system/splash/aplicar-splash.sh
set -e
[ "$EUID" -eq 0 ] || { echo "Córrelo con sudo ♡"; exit 1; }
HERE="$(cd "$(dirname "$0")" && pwd)"
P=/etc/mkinitcpio.d/linux.preset
install -Dm644 "$HERE/splash-angel.bmp" /usr/local/share/angel/splash-angel.bmp
[ -f "$P.bak-angel" ] || cp "$P" "$P.bak-angel"
sed -i 's|--splash [^ "]*|--splash /usr/local/share/angel/splash-angel.bmp|' "$P"
grep -n splash "$P"
mkinitcpio -P
echo "♡ Listo ✧ Reinicia para ver el splash angel"
echo "  (para regresar al logo de Arch: sudo cp $P.bak-angel $P && sudo mkinitcpio -P)"
