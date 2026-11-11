#!/usr/bin/env python3
"""
✧ motor de temas del rice
  theme.py ame            → modo Ame (oscuro)
  theme.py angel          → modo Angel (el original, pastel)
  theme.py toggle         → cambia entre los dos
  theme.py auto on|off    → colores según el wallpaper
  theme.py apply          → vuelve a generar con el estado actual (lo usa wall.sh)
  theme.py wall RUTA      → (lo usa wall.sh) recuerda el fondo del modo actual
  theme.py noche on|off   → modo Ame automático al anochecer (y Angel al amanecer)
  theme.py tick           → (lo usa el timer) revisa si ya anocheció / amaneció
  theme.py status

Cómo funciona: los archivos en modo Angel son TUS originales. Al salir de Angel se guardan
como plantilla en ~/.config/angel-theme/templates y se generan versiones con los colores
transformados. Al regresar a Angel se restauran las plantillas tal cual.
Si editas un archivo mientras estás en otro modo, se convierte de regreso y se guarda en la plantilla.
"""
import colorsys, hashlib, json, os, re, shlex, shutil, subprocess, sys, time

HOME = os.path.expanduser("~")
BASE = f"{HOME}/.config/angel-theme"
TPL = f"{BASE}/templates"
STATE = f"{BASE}/state.json"
FILES = [
    ".config/waybar/style.css", ".config/rofi/config.rasi", ".config/rofi/angel-menu.rasi",
    ".config/kitty/angel.conf", ".config/swaync/style.css", ".config/hypr/hyprlock.conf",
    ".config/wlogout/style.css", ".config/starship.toml", ".config/btop/themes/angel.theme",
    ".config/cava/config", ".config/gtk-3.0/colors.css", ".config/gtk-4.0/gtk.css",
    ".config/hypr/hyprland.lua", ".config/hypr/widgets/angel-desk.py", ".config/hypr/widgets/angel-music.py",
]
DEFAULT = {"dark": False, "auto": False, "hue": None, "hashes": {}, "noche": False, "sol": {}, "ultimo_cambio": "",
           "wall": {"angel": f"{HOME}/Pictures/wallpapers/escritorio.jpg",
                    "ame": f"{HOME}/Pictures/wallpapers/kangel-cables.jpg"}}
PINK_HUE = 330 / 360


def load():
    try:
        return {**DEFAULT, **json.load(open(STATE))}
    except Exception:
        return json.loads(json.dumps(DEFAULT))


def save(st):
    os.makedirs(BASE, exist_ok=True)
    json.dump(st, open(STATE, "w"), indent=2, ensure_ascii=False)


def sha(path):
    try:
        return hashlib.sha1(open(path, "rb").read()).hexdigest()
    except FileNotFoundError:
        return None


# ───────────── transformación de un color ─────────────
def transform(rgb, dark, hue_shift):
    r, g, b = (c / 255 for c in rgb)
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    if hue_shift and s > 0.08:
        h = (h + hue_shift) % 1
    if dark:
        if l < 0.12:                                   # sombras negras: se quedan
            pass
        elif l >= 0.86:                                # fondos claros → morado casi negro
            l = 0.07 + (1 - l) * 0.75
            s = min(s, 0.45) if s > 0.05 else 0.25
            if not hue_shift:
                h = 275 / 360
        elif l <= 0.50:                                # texto oscuro → lavanda clarito
            l = 0.86 - l * 0.15
            s = min(s, 0.55)
        else:                                          # acentos: un poquito más intensos
            s = min(1, s * 1.1)
            l = max(0.55, l * 0.95)
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return tuple(max(0, min(255, round(c * 255))) for c in (r, g, b))


HEX = re.compile(r"(?<![0-9A-Za-z_&])#([0-9a-fA-F]{6})([0-9a-fA-F]{2})?(?![0-9a-zA-Z_])")
HYPR = re.compile(r"\b(rgba?)\(([0-9a-fA-F]{6})([0-9a-fA-F]{2})?\)")
DEC = re.compile(r"\b(rgba?)\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})(\s*,\s*[\d.]+)?\s*\)")


def recolor(text, fn):
    def hx(m):
        rgb = tuple(int(m.group(1)[i:i + 2], 16) for i in (0, 2, 4))
        n = "".join(f"{c:02x}" for c in fn(rgb))
        if m.group(1).isupper(): n = n.upper()
        return "#" + n + (m.group(2) or "")
    def hy(m):
        rgb = tuple(int(m.group(2)[i:i + 2], 16) for i in (0, 2, 4))
        return f"{m.group(1)}({''.join(f'{c:02x}' for c in fn(rgb))}{m.group(3) or ''})"
    def de(m):
        rgb = tuple(int(m.group(i)) for i in (2, 3, 4))
        n = fn(rgb)
        return f"{m.group(1)}({n[0]}, {n[1]}, {n[2]}{m.group(5) or ''})"
    text = HYPR.sub(hy, text)
    text = DEC.sub(de, text)
    return HEX.sub(hx, text)


def colors_in(text):
    out = set()
    for m in HEX.finditer(text): out.add(tuple(int(m.group(1)[i:i + 2], 16) for i in (0, 2, 4)))
    for m in HYPR.finditer(text): out.add(tuple(int(m.group(2)[i:i + 2], 16) for i in (0, 2, 4)))
    for m in DEC.finditer(text): out.add(tuple(int(m.group(i)) for i in (2, 3, 4)))
    return out


# ───────────── tono dominante del wallpaper ─────────────
def wall_hue(path):
    try:
        ppm = subprocess.run(["magick", path + "[0]", "-resize", "64x64!", "-depth", "8", "ppm:-"],
                             capture_output=True, timeout=20).stdout
        # cabecera P6\n64 64\n255\n
        data = ppm.split(b"\n", 3)[3]
    except Exception:
        return None
    bins = [0.0] * 36
    for i in range(0, len(data) - 2, 3):
        r, g, b = data[i] / 255, data[i + 1] / 255, data[i + 2] / 255
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        w = s * s * v
        if s > 0.18 and v > 0.25:
            bins[int(h * 36) % 36] += w
    if max(bins) == 0:
        return None
    k = max(range(36), key=lambda i: bins[i - 1] + bins[i] * 2 + bins[(i + 1) % 36])
    return (k + 0.5) / 36


# ───────────── aplicar ─────────────
def snapshot_templates(st):
    os.makedirs(TPL, exist_ok=True)
    for f in FILES:
        src = f"{HOME}/{f}"
        if os.path.exists(src):
            dst = f"{TPL}/{f.replace('/', '__')}"
            shutil.copy2(src, dst)


def absorb_edits(st, prev_fn_inv):
    """si editaste un archivo en otro modo, lo regreso a colores angel y actualizo la plantilla"""
    for f in FILES:
        src = f"{HOME}/{f}"; h = sha(src)
        if h and st["hashes"].get(f) and h != st["hashes"][f]:
            text = open(src).read()
            open(f"{TPL}/{f.replace('/', '__')}", "w").write(recolor(text, prev_fn_inv))
            print(f"♡ guardé tus cambios de {f} en la plantilla")


def make_fn(dark, hue):
    shift = ((hue - PINK_HUE) % 1) if hue is not None else 0
    cache = {}
    def fn(rgb):
        if rgb not in cache:
            cache[rgb] = transform(rgb, dark, shift)
        return cache[rgb]
    return fn


def inverse_fn(st):
    """mapa inverso aproximado: color generado → color original (usando los colores de las plantillas)"""
    fn = make_fn(st["dark"], st["hue"] if st["auto"] else None)
    inv = {}
    for f in FILES:
        p = f"{TPL}/{f.replace('/', '__')}"
        if os.path.exists(p):
            for c in colors_in(open(p).read()):
                inv.setdefault(fn(c), c)
    return lambda rgb: inv.get(rgb, rgb)


def is_original(st):
    return not st["dark"] and not (st["auto"] and st["hue"] is not None)


def render(st, prev_original):
    if prev_original:
        snapshot_templates(st)            # salimos del modo original: guardo tus archivos
    else:
        absorb_edits(st, inverse_fn(st["_prev"]))
    if is_original(st):
        for f in FILES:
            p = f"{TPL}/{f.replace('/', '__')}"
            if os.path.exists(p):
                shutil.copy2(p, f"{HOME}/{f}")
        st["hashes"] = {}
        return
    fn = make_fn(st["dark"], st["hue"] if st["auto"] else None)
    st["hashes"] = {}
    for f in FILES:
        p = f"{TPL}/{f.replace('/', '__')}"
        if not os.path.exists(p):
            continue
        out = recolor(open(p).read(), fn)
        open(f"{HOME}/{f}", "w").write(out)
        st["hashes"][f] = sha(f"{HOME}/{f}")


def sh(cmd):
    subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)


def set_wall(path):
    if path and os.path.exists(path):
        subprocess.run([f"{HOME}/.config/hypr/scripts/wall.sh", "--set", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def reload_all(starship_palette):
    subprocess.run(["hyprctl", "reload"], stdout=subprocess.DEVNULL)
    sh(f"{HOME}/.config/hypr/scripts/angel.sh bar-reload-quiet")
    sh("swaync-client -rs")
    sh("pkill -USR1 -x kitty")                     # kitty recarga su config
    sh("pkill -USR2 -x cava")                      # cava recarga colores
    # widgets: reinicio solo los que estaban corriendo
    for w in ("angel-desk.py", "angel-music.py"):
        out = subprocess.run(["pgrep", "-f", f"widgets/{w}"], capture_output=True, text=True).stdout.split()
        mine = str(os.getpid())
        pids = [p for p in out if p != mine and open(f"/proc/{p}/cmdline", "rb").read().startswith(b"python")]
        if pids:
            for p in pids: os.kill(int(p), 15)
            time.sleep(0.3)
            sh(f"hyprctl dispatch 'hl.dsp.exec_cmd(\"python3 {HOME}/.config/hypr/widgets/{w}\")'")
    # gtk: preferencia clara/oscura para apps nuevas
    sh(f"gsettings set org.gnome.desktop.interface color-scheme {'prefer-dark' if starship_palette else 'prefer-light'}")


def notify(title, body):
    sh(f"notify-send -a angel {shlex.quote(title)} {shlex.quote(body)}")



# ───────────── modo noche automático ─────────────
def sun_times(st):
    """amanecer/atardecer de hoy (wttr.in, ubicación automática); si no hay internet: 7:00 / 19:00"""
    import datetime as dt, urllib.request
    today = dt.date.today().isoformat()
    if st["sol"].get("fecha") != today:
        try:
            req = urllib.request.Request("https://wttr.in/?format=j1", headers={"User-Agent": "curl/8"})
            a = json.load(urllib.request.urlopen(req, timeout=15))["weather"][0]["astronomy"][0]
            to24 = lambda t: dt.datetime.strptime(t, "%I:%M %p").strftime("%H:%M")
            st["sol"] = {"fecha": today, "amanecer": to24(a["sunrise"]), "atardecer": to24(a["sunset"])}
        except Exception:
            st["sol"] = {"fecha": "", "amanecer": "07:00", "atardecer": "19:00"}
    return st["sol"]["amanecer"], st["sol"]["atardecer"]


def night_target(st):
    """devuelve 'ame'/'angel' si toca cambiar ahora (solo una vez por amanecer/atardecer), si no None"""
    import datetime as dt
    am, pm = sun_times(st)
    now = dt.datetime.now(); hm = now.strftime("%H:%M"); hoy = now.date().isoformat()
    if hm >= pm or hm < am:
        clave = f"noche-{hoy if hm >= pm else (now.date() - dt.timedelta(days=1)).isoformat()}"
        want = "ame"
    else:
        clave, want = f"dia-{hoy}", "angel"
    if st.get("ultimo_cambio") == clave:
        return None          # ya cambié en este tramo: respeto si lo cambiaste a mano
    st["ultimo_cambio"] = clave
    return want

def main():
    a = sys.argv[1:] or ["status"]
    st = load()
    st["_prev"] = {k: st[k] for k in ("dark", "auto", "hue")}
    was_original = is_original(st)
    prev_dark = st["dark"]

    if a[0] == "status":
        print(json.dumps({k: st.get(k) for k in ("dark", "auto", "noche", "sol", "hue", "wall")}, indent=2, ensure_ascii=False)); return
    if a[0] in ("ame", "angel", "toggle"):
        st["dark"] = (not st["dark"]) if a[0] == "toggle" else (a[0] == "ame")
    elif a[0] == "auto":
        st["auto"] = (a[1] == "on") if len(a) > 1 else not st["auto"]
    elif a[0] == "noche":
        st["noche"] = (a[1] == "on") if len(a) > 1 else not st["noche"]
        st["ultimo_cambio"] = ""
        st.pop("_prev", None); save(st)
        notify("Modo noche automático", ("Activado ☾ El modo Ame se prende al anochecer" if st["noche"] else "Desactivado ♡"))
        if not st["noche"]: return
        st = load(); st["_prev"] = {k: st[k] for k in ("dark", "auto", "hue")}; a = ["tick"]
    if a[0] == "tick":
        if not st.get("noche"):
            return
        want = night_target(st)
        if want is None or want == ("ame" if st["dark"] else "angel"):
            st.pop("_prev", None); save(st); return
        st["dark"] = want == "ame"
        a = [want]
    elif a[0] == "wall" and len(a) > 1:          # wall.sh avisa qué fondo elegiste
        st["wall"]["ame" if st["dark"] else "angel"] = a[1]
        if not st["auto"]:
            st.pop("_prev", None); save(st); return
    elif a[0] not in ("apply", "ame", "angel", "toggle", "auto"):
        print(__doc__); return

    mode = "ame" if st["dark"] else "angel"
    # wallpaper del modo (si cambiaste de modo)
    if st["dark"] != prev_dark:
        try:   # recuerdo el fondo que tenías en el modo anterior
            cur = re.search(r"^\s*path\s*=\s*(.+)$", open(f"{HOME}/.config/hypr/hyprpaper.conf").read(), re.M).group(1).strip()
            st["wall"]["ame" if prev_dark else "angel"] = cur
        except Exception:
            pass
        set_wall(st["wall"].get(mode))
    if st["auto"]:
        cur = open(f"{HOME}/.config/hypr/hyprpaper.conf").read()
        m = re.search(r"^\s*path\s*=\s*(.+)$", cur, re.M)
        st["hue"] = wall_hue(m.group(1).strip()) if m else None
    render(st, was_original)
    st.pop("_prev", None)
    save(st)
    reload_all(st["dark"])
    if a[0] in ("ame", "angel", "toggle"):
        notify("Modo Ame ☾" if st["dark"] else "Modo Angel ♡",
               "Lado oscuro activado (￢‿￢)" if st["dark"] else "De vuelta al pastel (｡•ᴗ•｡)")
    elif a[0] == "auto":
        notify("Colores del wallpaper", "Activados ✧" if st["auto"] else "Desactivados, de vuelta a la paleta normal ♡")


if __name__ == "__main__":
    main()
