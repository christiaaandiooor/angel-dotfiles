#!/usr/bin/env python3
# ˚₊‧ fastfetch centrado ‧₊˚
# Mide la terminal, escoge config completa o compacta (la que quepa) y centra imagen + info.
import fcntl, os, re, struct, subprocess, sys, termios, unicodedata

DIR = os.path.expanduser("~/.config/fastfetch")
LOGO = os.path.join(DIR, "logos/k-angel.png")  # imagen cuadrada
CONFIGS = [os.path.join(DIR, "config.jsonc"), os.path.join(DIR, "config-showcase.jsonc")]
GAP_L, GAP_R = 0, 4  # espacio antes/después de la imagen

def term_size():
    try:
        rows, cols, xpx, ypx = struct.unpack("HHHH", fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ, b"\0" * 8))
    except OSError:
        return 24, 80, 0.5
    aspect = (xpx / cols) / (ypx / rows) if xpx and ypx else 0.5  # ancho/alto de una celda
    return rows, cols, aspect

def width(s):
    w = 0
    for ch in s:
        if unicodedata.combining(ch):
            continue
        w += 2 if unicodedata.east_asian_width(ch) in "WF" else 1
    return w

def info(cfg):
    out = subprocess.run(["fastfetch", "-c", cfg, "--logo", "none", "--pipe", "false"],
                         capture_output=True, text=True).stdout
    lines = out.rstrip("\n").split("\n")
    w = 0
    for ln in lines:
        ln = re.sub(r"\x1b\[[0-9;]*m", "", ln)
        # \e[NG = brincar a la columna N (lo usa key.width)
        col = 0
        for part in re.split(r"(\x1b\[\d+G)", ln):
            m = re.fullmatch(r"\x1b\[(\d+)G", part)
            col = max(col, int(m.group(1)) - 1) if m else col + width(part)
        w = max(w, col)
    return len(lines), w

def main():
    rows, cols, aspect = term_size()
    avail_h = rows - 2  # deja espacio para el prompt
    choice = None
    for cfg in CONFIGS:
        h, w = info(cfg)
        # imagen: lo más grande que quepa, sin pasar de 38 columnas
        logo_w = min(38, cols - w - GAP_L - GAP_R - 2, int(min(avail_h, h + 4) / aspect))
        logo_h = round(logo_w * aspect)
        if logo_w >= 14 and max(h, logo_h) <= avail_h:
            choice = (cfg, h, w, logo_w, logo_h)
            break
    if not choice:  # ni la compacta cabe: sin imagen
        cfg = CONFIGS[-1]
        os.execvp("fastfetch", ["fastfetch", "-c", cfg, "--logo", "none"])

    cfg, h, w, logo_w, logo_h = choice
    total_w = GAP_L + logo_w + GAP_R + w
    total_h = max(h, logo_h)
    pad_left = max(0, (cols - total_w) // 2) + GAP_L
    pad_top_logo = max(0, (h - logo_h) // 2)
    top = max(0, (avail_h - total_h) // 2)

    sys.stdout.write("\n" * top)
    sys.stdout.flush()
    os.execvp("fastfetch", ["fastfetch", "-c", cfg,
        "--logo-type", "kitty-direct", "--logo", LOGO,
        "--logo-width", str(logo_w), "--logo-height", str(logo_h),
        "--logo-padding-left", str(pad_left), "--logo-padding-right", str(GAP_R),
        "--logo-padding-top", str(pad_top_logo)])

if __name__ == "__main__":
    main()
