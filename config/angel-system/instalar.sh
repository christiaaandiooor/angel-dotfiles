#!/usr/bin/env bash
# 🎀 lo del rice angel que necesita sudo. Correr con:  sudo bash ~/.config/angel-system/instalar.sh
# hace respaldos de todo lo que toca (*.bak-angel)
set -e
[ "$EUID" -eq 0 ] || { echo "Córrelo con sudo ♡"; exit 1; }
HERE="$(cd "$(dirname "$0")" && pwd)"
ok()  { printf '\e[38;2;255;143;200m♡\e[0m %s\n' "$*"; }
warn(){ printf '\e[38;2;226;93;164m!\e[0m %s\n' "$*"; }

# 1) paquetes
pacman -S --needed --noconfirm hyprsunset plymouth || true
ok "Hyprsunset y Plymouth instalados"

# 2) login de SDDM (tema caelestia con colores angel + tu wallpaper)
T=/usr/share/sddm/themes/caelestia
if [ -d "$T" ]; then
  [ -f "$T/theme.conf.bak-angel" ] || cp "$T/theme.conf" "$T/theme.conf.bak-angel"
  for f in background.jpg background.png; do
    [ -f "$T/assets/$f" ] && [ ! -f "$T/assets/$f.bak-angel" ] && cp "$T/assets/$f" "$T/assets/$f.bak-angel"
    [ -f "$HERE/sddm/$f" ] && cp "$HERE/sddm/$f" "$T/assets/$f"
  done
  cp "$HERE/sddm/theme.conf" "$T/theme.conf"
  ok "SDDM pintado de angel"
else
  warn "No encontré $T, me salto SDDM"
fi

# 3) plymouth (pantallita de arranque)
P=/usr/share/plymouth/themes/angel
mkdir -p "$P"; cp "$HERE"/plymouth/angel/* "$P/"
plymouth-set-default-theme angel
ok "Tema Plymouth 'angel' puesto"

# hook en mkinitcpio (después de udev/systemd)
M=/etc/mkinitcpio.conf
if ! grep -q '^HOOKS=.*plymouth' "$M"; then
  cp "$M" "$M.bak-angel"
  if grep -q '^HOOKS=.*systemd' "$M"; then
    sed -i '/^HOOKS=/ s/systemd/systemd plymouth/' "$M"
  else
    sed -i '/^HOOKS=/ s/udev/udev plymouth/' "$M"
  fi
  ok "Hook de Plymouth agregado: $(grep '^HOOKS=' "$M")"
fi

# "quiet splash" en el arranque
added=0
if [ -d /boot/loader/entries ]; then
  for e in /boot/loader/entries/*.conf; do
    [ -f "$e" ] || continue
    grep -q '^options.*splash' "$e" && continue
    cp "$e" "$e.bak-angel"
    sed -i '/^options/ s/$/ quiet splash/' "$e"
    ok "Splash agregado a $(basename "$e")"; added=1
  done
fi
if command -v grub-mkconfig >/dev/null && [ -f /boot/grub/grub.cfg ] && ! grep -q '^GRUB_CMDLINE_LINUX_DEFAULT=.*splash' /etc/default/grub; then
  cp /etc/default/grub /etc/default/grub.bak-angel
  sed -i 's/^GRUB_CMDLINE_LINUX_DEFAULT="\(.*\)"/GRUB_CMDLINE_LINUX_DEFAULT="\1 quiet splash"/' /etc/default/grub
  grub-mkconfig -o /boot/grub/grub.cfg
  ok "Splash agregado a GRUB"; added=1
fi
[ -f /etc/kernel/cmdline ] && ! grep -q splash /etc/kernel/cmdline && {
  cp /etc/kernel/cmdline /etc/kernel/cmdline.bak-angel
  sed -i 's/$/ quiet splash/' /etc/kernel/cmdline; ok "Splash agregado a /etc/kernel/cmdline (UKI)"; added=1; }
[ "$added" = 1 ] || grep -rqs splash /boot/loader/entries /etc/default/grub /etc/kernel/cmdline || \
  warn "No supe cuál es tu bootloader: agrega 'quiet splash' a los parámetros del kernel a mano"

mkinitcpio -P
ok "Listo ✧ Reinicia para ver el arranque y el login nuevos"
