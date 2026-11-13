#!/usr/bin/env python3
# ♡ mini reproductor del showcase: portada + canción + barrita de progreso (playerctl + chafa)
import hashlib, os, shutil, subprocess, sys, time, urllib.parse

PINK, LAV, BLUE, DIM, DEEP = "255;143;200", "195;166;245", "143;207;247", "169;139;187", "226;93;164"
CACHE = os.path.expanduser("~/.cache/angel-showcase")
DEFAULT = os.path.expanduser("~/.config/fastfetch/logos/k-angel.png")
os.makedirs(CACHE, exist_ok=True)

def c(rgb, s, bold=False):
    return f"\033[{'1;' if bold else ''}38;2;{rgb}m{s}\033[0m"

def meta():
    fmt = "{{status}}\t{{title}}\t{{artist}}\t{{mpris:artUrl}}\t{{position}}\t{{mpris:length}}"
    try:
        out = subprocess.run(["playerctl", "metadata", "--format", fmt], capture_output=True, text=True, timeout=2).stdout
    except Exception:
        return None
    parts = out.rstrip("\n").split("\t")
    if len(parts) < 6 or parts[0] not in ("Playing", "Paused"):
        return None
    st, title, artist, art, pos, length = parts
    num = lambda x: int(x) if x.isdigit() else 0
    return dict(status=st, title=title or "Sin título", artist=artist or "", art=art, pos=num(pos), len=num(length))

def cover(url):
    if url.startswith("file://"):
        p = urllib.parse.unquote(url[7:])
        return p if os.path.exists(p) else DEFAULT
    if url.startswith("http"):
        p = os.path.join(CACHE, hashlib.md5(url.encode()).hexdigest() + ".img")
        if not os.path.exists(p):
            subprocess.run(["curl", "-sL", "-m", "4", "-o", p, url])
        return p if os.path.exists(p) and os.path.getsize(p) else DEFAULT
    return DEFAULT

def center(s, visible_len, cols):
    return " " * max(0, (cols - visible_len) // 2) + s

def cut(s, n):
    return s if len(s) <= n else s[: n - 1] + "…"

def tiempo(us):
    s = us // 1_000_000
    return f"{s // 60}:{s % 60:02d}"

def draw_static(m, cols, rows):
    sys.stdout.write("\033_Ga=d\033\\\033[2J\033[H")  # borra imágenes de kitty y pantalla
    img_h = max(4, rows - 7)
    img_w = img_h * 2
    top = 1
    sys.stdout.write("\n" * top)
    sys.stdout.flush()
    src = cover(m["art"]) if m else DEFAULT
    subprocess.run(["chafa", "-f", "kitty", "--size", f"{img_w}x{img_h}", "--align", "center", "--view-size", f"{cols}x{img_h}", src])
    row = top + img_h + 2
    if m:
        t = cut(m["title"], cols - 6)
        a = cut(m["artist"], cols - 6)
        lines = [(c(PINK, "♪ " + t, True), len(t) + 2), (c(LAV, a), len(a))]
    else:
        msg, sub = "Nada sonando", "(｡•́︿•̀｡)  pon algo bonito"
        lines = [(c(PINK, msg, True), len(msg)), (c(DIM, sub), len(sub) + 1)]
    for i, (s, n) in enumerate(lines):
        sys.stdout.write(f"\033[{row + i};1H" + center(s, n, cols))
    sys.stdout.flush()
    return row + 2

def draw_bar(m, cols, row):
    if not m:
        return
    w = max(10, cols - 20)
    frac = min(1, m["pos"] / m["len"]) if m["len"] else 0
    full = int(frac * w)
    icon = "" if m["status"] == "Playing" else ""
    bar = c(DEEP, "━" * full) + c(PINK, "♡") + c(DIM, "─" * (w - full))
    txt = f"{c(BLUE, icon)}  {c(DIM, tiempo(m['pos']))} {bar} {c(DIM, tiempo(m['len']))}"
    vis = 3 + len(tiempo(m["pos"])) + 1 + w + 1 + 1 + len(tiempo(m["len"]))
    sys.stdout.write(f"\033[{row};1H\033[2K" + center(txt, vis, cols))
    sys.stdout.flush()

def main():
    sys.stdout.write("\033[?25l")  # sin cursor
    last, bar_row, size = None, 0, None
    try:
        while True:
            m = meta()
            sz = shutil.get_terminal_size()
            key = (m["title"], m["artist"], m["art"]) if m else None
            if key != last or sz != size:
                bar_row = draw_static(m, sz.columns, sz.lines)
                last, size = key, sz
            draw_bar(m, sz.columns, bar_row)
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\033[?25h")

if __name__ == "__main__":
    main()
