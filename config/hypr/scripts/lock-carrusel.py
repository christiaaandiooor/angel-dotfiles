#!/usr/bin/env python3
# ♡ Carrusel de fondos para hyprlock
# Sin argumentos: avanza al siguiente fondo e imprime su ruta (lo usa reload_cmd)
# --prep: prepara todas las copias a 1920x1080 en ~/.cache/angel-lock
import os, sys, glob
from PIL import Image, ImageOps

HOME = os.path.expanduser("~")
WALLS = f"{HOME}/Pictures/wallpapers"
LISTA = f"{HOME}/.config/angel-lock/lista.txt"
CACHE = f"{HOME}/.cache/angel-lock"
ACTUAL = f"{CACHE}/actual.jpg"
SIZE = (1920, 1080)

def fondos():
    if os.path.exists(LISTA):
        fs = [l.strip() for l in open(LISTA) if l.strip() and not l.startswith("#")]
        fs = [f"{WALLS}/{f}" for f in fs if os.path.exists(f"{WALLS}/{f}")]
        if fs:
            return fs
    return sorted(f for e in ("jpg", "jpeg", "png", "webp") for f in glob.glob(f"{WALLS}/*.{e}"))

def preparar(src):
    dst = f"{CACHE}/{os.path.splitext(os.path.basename(src))[0]}.jpg"
    if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
        im = ImageOps.fit(Image.open(src).convert("RGB"), SIZE, Image.LANCZOS)
        im.save(dst + ".tmp.jpg", quality=92)
        os.replace(dst + ".tmp.jpg", dst)
    return dst

def main():
    os.makedirs(CACHE, exist_ok=True)
    fs = fondos()
    if not fs:
        return
    if "--prep" in sys.argv:
        for f in fs:
            preparar(f)
        if not os.path.exists(ACTUAL):
            os.symlink(preparar(fs[0]), ACTUAL)
        return
    idx_file = f"{CACHE}/idx"
    try:
        i = (int(open(idx_file).read()) + 1) % len(fs)
    except Exception:
        i = 0
    open(idx_file, "w").write(str(i))
    dst = preparar(fs[i])
    tmp = ACTUAL + ".tmp"
    if os.path.lexists(tmp):
        os.remove(tmp)
    os.symlink(dst, tmp)
    os.replace(tmp, ACTUAL)
    print(dst)

if __name__ == "__main__":
    main()
