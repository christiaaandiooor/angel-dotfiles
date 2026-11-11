#!/usr/bin/env python3
# 🎀 genera el tema de cursor "Angel-Cursor" (XCursor) dibujado con la paleta angel
# los cursores que no están aquí se heredan de Bibata-Modern-Ice
import math, os, struct, subprocess, tempfile

OUT = os.path.expanduser("~/.local/share/icons/Angel-Cursor")
SIZES = [24, 32, 48, 64]
O = "#5b3b6e"

def svg(body, extra=""):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">{extra}{body}</svg>'

DEFS = '''<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="#ffd6ec"/><stop offset=".55" stop-color="#ff8fc8"/><stop offset="1" stop-color="#e25da4"/></linearGradient></defs>'''

ARROW = svg(f'''
<path d="M30,22 L30,196 L74,154 L104,222 L134,208 L104,142 L166,142 Z" fill="url(#g)" stroke="#ffffff" stroke-width="22" stroke-linejoin="round"/>
<path d="M30,22 L30,196 L74,154 L104,222 L134,208 L104,142 L166,142 Z" fill="url(#g)" stroke="{O}" stroke-width="8" stroke-linejoin="round"/>
<path d="M60,80 c-6,-10 -20,-3 -13,7 l13,12 l13,-12 c7,-10 -7,-17 -13,-7z" fill="#ffffff" opacity=".9"/>
<ellipse cx="54" cy="18" rx="26" ry="8" fill="none" stroke="#c3a6f5" stroke-width="7"/>''', DEFS)

WAND = svg(f'''
<path d="M150,120 L234,236" stroke="#ffffff" stroke-width="30" stroke-linecap="round"/>
<path d="M150,120 L234,236" stroke="{O}" stroke-width="20" stroke-linecap="round"/>
<path d="M150,120 L234,236" stroke="#c3a6f5" stroke-width="10" stroke-linecap="round"/>
<path d="M90,8 L110,62 L166,66 L122,100 L138,154 L90,122 L42,154 L58,100 L14,66 L70,62 Z"
      fill="url(#g)" stroke="#ffffff" stroke-width="20" stroke-linejoin="round"/>
<path d="M90,8 L110,62 L166,66 L122,100 L138,154 L90,122 L42,154 L58,100 L14,66 L70,62 Z"
      fill="url(#g)" stroke="{O}" stroke-width="7" stroke-linejoin="round"/>
<circle cx="78" cy="84" r="6" fill="{O}"/><circle cx="104" cy="84" r="6" fill="{O}"/>
<path d="M84,100 q7,7 14,0" stroke="{O}" stroke-width="5" fill="none" stroke-linecap="round"/>''', DEFS)

TEXT = svg(f'''
<path d="M96,28 q32,0 32,24 v152 q0,24 32,24 M160,28 q-32,0 -32,24 v152 q0,24 -32,24 M100,128 h56"
      fill="none" stroke="#ffffff" stroke-width="26" stroke-linecap="round"/>
<path d="M96,28 q32,0 32,24 v152 q0,24 32,24 M160,28 q-32,0 -32,24 v152 q0,24 -32,24 M100,128 h56"
      fill="none" stroke="{O}" stroke-width="14" stroke-linecap="round"/>
<path d="M96,28 q32,0 32,24 v152 q0,24 32,24 M160,28 q-32,0 -32,24 v152 q0,24 -32,24 M100,128 h56"
      fill="none" stroke="#ff8fc8" stroke-width="6" stroke-linecap="round"/>''')

NO = svg(f'''
<circle cx="128" cy="128" r="92" fill="#fff5fb" stroke="#ffffff" stroke-width="30"/>
<circle cx="128" cy="128" r="92" fill="#fff5fb" stroke="{O}" stroke-width="22"/>
<circle cx="128" cy="128" r="92" fill="none" stroke="#ff8fc8" stroke-width="12"/>
<path d="M64,64 L192,192" stroke="{O}" stroke-width="22" stroke-linecap="round"/>
<path d="M64,64 L192,192" stroke="#ff8fc8" stroke-width="12" stroke-linecap="round"/>''')

def heart(cx, cy, s, fill):
    return (f'<path transform="translate({cx},{cy}) scale({s})" d="M0,-6 c-6,-14 -30,-10 -30,8 c0,16 18,26 30,36 c12,-10 30,-20 30,-36 c0,-18 -24,-22 -30,-8z" '
            f'fill="{fill}" stroke="{O}" stroke-width="{4 / s:.2f}"/>')

def wait_frame(k, n=12, arrow=False):
    cols = ["#ff8fc8", "#e9a0e6", "#c3a6f5", "#a9bdf6", "#8fcff7", "#c3a6f5"]
    cx, cy, r = (178, 178, 52) if arrow else (128, 128, 82)
    parts = []
    for i in range(6):
        a = 2 * math.pi * (i / 6) + 2 * math.pi * k / n
        sc = (0.55 + 0.45 * ((i + k) % 6) / 5) * (0.75 if arrow else 1.15)
        parts.append(heart(cx + r * math.cos(a), cy + r * math.sin(a), sc, cols[i]))
    body = "".join(parts)
    if arrow:
        return ARROW.replace("</svg>", body + "</svg>")
    return svg(body)

def raster(svg_text, size):
    with tempfile.NamedTemporaryFile("w", suffix=".svg", delete=False) as f:
        f.write(svg_text); p = f.name
    raw = subprocess.run(["magick", "-background", "none", "-density", "384", p, "-resize", f"{size}x{size}",
                          "-depth", "8", "rgba:-"], capture_output=True, check=True).stdout
    os.unlink(p)
    px = []
    for i in range(0, len(raw), 4):
        r, g, b, a = raw[i:i + 4]
        r, g, b = (r * a // 255, g * a // 255, b * a // 255)   # premultiplicado
        px.append((a << 24) | (r << 16) | (g << 8) | b)
    return px

def write_xcursor(path, frames_by_size, hot, delay=60):
    imgs = []
    for size, frames in frames_by_size.items():
        for fr in frames:
            imgs.append((size, fr))
    header = struct.pack("<4sIII", b"Xcur", 16, 0x10000, len(imgs))
    pos = 16 + 12 * len(imgs); toc = b""; chunks = b""
    for size, px in imgs:
        toc += struct.pack("<III", 0xFFFD0002, size, pos)
        hx, hy = round(hot[0] * size / 256), round(hot[1] * size / 256)
        ch = struct.pack("<IIIIIIIII", 36, 0xFFFD0002, size, 1, size, size, hx, hy, delay) + struct.pack(f"<{len(px)}I", *px)
        chunks += ch; pos += len(ch)
    open(path, "wb").write(header + toc + chunks)

CURSORS = {
    "left_ptr":    (lambda: [ARROW], (30, 22), ["default", "arrow", "top_left_arrow", "left_arrow"]),
    "pointer":     (lambda: [WAND], (90, 10), ["hand1", "hand2", "pointing_hand", "e29285e634086352946a0e7090d73106", "9d800788f1b08800ae810202380a0822"]),
    "text":        (lambda: [TEXT], (128, 128), ["xterm", "ibeam"]),
    "wait":        (lambda: [wait_frame(k) for k in range(12)], (128, 128), ["watch"]),
    "progress":    (lambda: [wait_frame(k, arrow=True) for k in range(12)], (30, 22), ["left_ptr_watch", "half-busy", "00000000000000020006000e7e9ffc3f", "08e8e1c95fe2fc01f976f1e063a24ccd", "3ecb610c1bf2410f44200f48c40d3599"]),
    "not-allowed": (lambda: [NO], (128, 128), ["crossed_circle", "no-drop", "forbidden", "circle", "03b6e0fcb3499374a867c041f52298f0"]),
}

os.makedirs(f"{OUT}/cursors", exist_ok=True)
for name, (mk, hot, aliases) in CURSORS.items():
    svgs = mk()
    write_xcursor(f"{OUT}/cursors/{name}", {s: [raster(x, s) for x in svgs] for s in SIZES}, hot)
    for al in aliases:
        p = f"{OUT}/cursors/{al}"
        if os.path.lexists(p): os.unlink(p)
        os.symlink(name, p)
    print("✓", name)
open(f"{OUT}/index.theme", "w").write("[Icon Theme]\nName=Angel-Cursor\nComment=Cursor angel ♡ (hereda de Bibata-Modern-Ice)\nInherits=Bibata-Modern-Ice\n")
# vista previa
prev = os.path.expanduser("~/.config/angel-system/cursor/preview.png")
tmp = []
for name, (mk, hot, _) in CURSORS.items():
    t = tempfile.NamedTemporaryFile("w", suffix=".svg", delete=False); t.write(mk()[0 if name not in ("wait", "progress") else 3]); t.close(); tmp.append(t.name)
subprocess.run(["magick", "montage", "-background", "#fff5fb", *[f"{t}" for t in tmp], "-geometry", "96x96+12+12", "-tile", "6x", prev])
for t in tmp: os.unlink(t)
print("vista previa:", prev)
