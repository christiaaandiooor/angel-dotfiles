#!/usr/bin/env bash
# 🎶 barritas de cava para waybar; se esconde cuando no suena nada
PIDF="${XDG_RUNTIME_DIR:-/tmp}/angel-cava.pid"
[ -f "$PIDF" ] && kill "$(cat "$PIDF")" 2>/dev/null
dict="s/;//g;s/0/▁/g;s/1/▂/g;s/2/▃/g;s/3/▄/g;s/4/▅/g;s/5/▆/g;s/6/▇/g;s/7/█/g"
exec 3< <(exec cava -p ~/.config/cava/waybar.conf)
echo $! > "$PIDF"
trap 'kill $(cat "$PIDF") 2>/dev/null' EXIT
while IFS= read -r line <&3; do
  if [[ "$line" =~ ^(0\;)+$ ]]; then echo ""; else sed "$dict" <<<"$line"; fi
done
