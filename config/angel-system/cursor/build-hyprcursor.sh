#!/usr/bin/env bash
# 🖱️ convierte Angel-Cursor al formato de Hyprland (hyprcursor) usando Bibata-Modern-Ice como base
set -e
W=$(mktemp -d); I="$HOME/.local/share/icons/Angel-Cursor"
hyprcursor-util --extract /usr/share/icons/Bibata-Modern-Ice -o "$W" >/dev/null
hyprcursor-util --extract "$I" -o "$W" >/dev/null
python3 - "$W/extracted_Angel-Cursor/hyprcursors" "$W/extracted_Bibata-Modern-Ice/hyprcursors" <<'PY'
import sys, os, glob, shutil, re
A, B = sys.argv[1:]
MAP = {"left_ptr":"left_ptr","pointer":"hand2","text":"xterm","wait":"wait","progress":"left_ptr_watch","not-allowed":"crossed_circle"}
dirs = set(os.listdir(B))
for a, b in MAP.items():
    am = open(f"{A}/{a}/meta.hl").read(); bm = open(f"{B}/{b}/meta.hl").read()
    ov = []
    for l in re.findall(r"^define_override = (.+)$", bm, re.M) + re.findall(r"^define_override = (.+)$", am, re.M) + [a]:
        if l != b and l not in dirs and l not in ov: ov.append(l)
    for p in glob.glob(f"{B}/{b}/*"): os.unlink(p)
    for p in glob.glob(f"{A}/{a}/*.png"): shutil.copy(p, f"{B}/{b}/{os.path.basename(p)}")
    head = re.sub(r"^define_override.*\n?", "", am, flags=re.M).replace("resize_algorithm = none", "resize_algorithm = bilinear").rstrip()
    open(f"{B}/{b}/meta.hl", "w").write(head + "\n\n" + "".join(f"define_override = {o}\n" for o in ov))
PY
sed -i 's/^name = .*/name = Angel-Cursor/; s/^description = .*/description = Cursor angel (base Bibata-Modern-Ice)/' "$W/extracted_Bibata-Modern-Ice/manifest.hl"
hyprcursor-util --create "$W/extracted_Bibata-Modern-Ice" -o "$W" >/dev/null
rm -rf "$I/hyprcursors"; cp -r "$W/theme_Angel-Cursor/hyprcursors" "$I/"; cp "$W/theme_Angel-Cursor/manifest.hl" "$I/"
rm -rf "$W"; echo "♡ Angel-Cursor listo para Hyprland"
