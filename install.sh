#!/usr/bin/env bash
# 🎀 instalador de angel-dotfiles
#   ./install.sh [TuNombre]
# Respalda lo que vaya a reemplazar en ~/.config/angel-backup-FECHA antes de copiar.
set -e
cd "$(dirname "$0")"
NAME="${1:-$(echo "${USER^}")}"
STAMP=$(date +%Y%m%d-%H%M%S)
BK="$HOME/.config/angel-backup-$STAMP"
p(){ printf '\e[38;2;255;143;200m♡\e[0m %s\n' "$*"; }

p "Hola, $NAME ✧ instalando el rice angel"

# 1) copiar (con respaldo) y poner tu HOME y tu nombre
for top in config local; do
  find "$top" -type f | while read -r f; do
    rel="${f#*/}"
    case "$top" in config) dst="$HOME/.config/$rel" ;; local) dst="$HOME/.local/$rel" ;; esac
    if [ -e "$dst" ]; then mkdir -p "$BK/$(dirname "$top/$rel")"; cp -a "$dst" "$BK/$top/$rel"; fi
    mkdir -p "$(dirname "$dst")"; cp "$f" "$dst"
    if file -b --mime "$dst" | grep -q text; then
      sed -i "s|__HOME__|$HOME|g; s|__NAME__|$NAME|g; s|__name__|${NAME,,}|g" "$dst"
    fi
  done
done
chmod +x ~/.config/hypr/scripts/* ~/.config/hypr/widgets/*.py ~/.config/angel-theme/theme.py 2>/dev/null || true
p "Configs copiadas (respaldo en $BK)"

# 2) carpetas rosas (Papirus-Angel, hereda de Papirus)
if [ -d /usr/share/icons/Papirus ]; then
  T="$HOME/.local/share/icons/Papirus-Angel"; rm -rf "$T"; mkdir -p "$T"; dirs=""
  ( cd /usr/share/icons/Papirus
    for d in */places; do
      mkdir -p "$T/$d"; dirs="$dirs,$d"
      for f in "$d"/*.svg; do
        [ -L "$f" ] || continue; t=$(readlink "$f"); case "$t" in *-blue*) ;; *) continue;; esac
        [ -e "$d/${t/-blue/-pink}" ] && ln -sf "/usr/share/icons/Papirus/$d/${t/-blue/-pink}" "$T/$f"
      done
    done
    { printf '[Icon Theme]\nName=Papirus-Angel\nInherits=Papirus,breeze,hicolor\nDirectories=%s\n' "${dirs#,}"
      for d in $(echo "${dirs#,}" | tr ',' ' '); do sz=${d%%/*}; s=${sz%%x*}; sc=1; [[ $sz == *@2x* ]] && sc=2
        printf '\n[%s]\nContext=Places\nSize=%s\nScale=%s\nType=Fixed\n' "$d" "${s%@*}" "$sc"; done; } > "$T/index.theme" )
  p "Carpetas rosas listas (tema de iconos Papirus-Angel)"
fi

# 3) cursor angel
command -v magick >/dev/null && python3 ~/.config/angel-system/cursor/make-cursor.py >/dev/null && p "Cursor Angel-Cursor generado"

# 4) modo noche automático
systemctl --user daemon-reload && systemctl --user enable --now angel-noche.timer >/dev/null 2>&1 && p "Modo noche automático activado"

p "Listo ✧ Cierra sesión y vuelve a entrar. Atajos: SUPER + /"
p "Pon tus imágenes en ~/Pictures/wallpapers (bloqueo.png, menu.jpg, escritorio.jpg) y tu avatar en ~/.config/fastfetch/logos/k-angel.png"
