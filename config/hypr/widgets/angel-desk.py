#!/usr/bin/env python3
# 🎀 widgets del escritorio angel (capa "bottom": arriba del fondo, abajo de las ventanas)
#   reloj · clima · próxima clase · medidores · cuenta regresiva · calendario · polaroids · pomodoro · notitas · frase del día
# on/off: SUPER+SHIFT+D        config: ~/.config/angel-desk/config.json
import os, json, math, random, datetime as dt, threading, urllib.request, subprocess, glob
import cairo, psutil
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
gi.require_version("PangoCairo", "1.0")
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib, Pango, PangoCairo, GtkLayerShell as LS

HOME = os.path.expanduser("~")
CONF_DIR = f"{HOME}/.config/angel-desk"
CONF = f"{CONF_DIR}/config.json"
SND = f"{HOME}/.local/share/sounds/angel"
os.makedirs(CONF_DIR, exist_ok=True)
PREVIEW = os.environ.get("ANGEL_DESK_PREVIEW") == "1"   # solo para probar: los pone encima de todo

DEFAULT_CONF = {
    "_ayuda": "Edita las fechas de 'cuenta_regresiva' (AAAA-MM-DD) y las carpetas de 'polaroids'. Reinicia con SUPER+SHIFT+D dos veces.",
    "cuenta_regresiva": [
        {"que": "Navidad 🎄", "fecha": "2026-12-25"},
        {"que": "Año nuevo ✨", "fecha": "2027-01-01"},
    ],
    "polaroids": ["~/Pictures/wallpapers"],
    "aviso_clase_min": 10,
}
if not os.path.exists(CONF):
    json.dump(DEFAULT_CONF, open(CONF, "w"), indent=2, ensure_ascii=False)
try:
    CFG = {**DEFAULT_CONF, **json.load(open(CONF))}
except Exception:
    CFG = DEFAULT_CONF

# ───────────── horario (ejemplo) ─────────────
H = {
    # (inicio, fin, materia, salón) — lunes=0 … viernes=4. Cámbialo por tu horario ♡
    0: [("07:00", "08:50", "Programación", "Lab-1"), ("09:00", "09:50", "Inglés", "Aula-3"),
        ("10:00", "11:50", "Bases de Datos", "Lab-2"), ("12:20", "14:00", "Cálculo", "Aula-5")],
    1: [("07:00", "08:50", "Cálculo", "Aula-5"), ("09:00", "10:50", "Redes", "Lab-3")],
    2: [("08:00", "09:50", "Programación", "Lab-1"), ("11:00", "12:50", "Inglés", "Aula-3")],
    3: [("07:00", "08:50", "Bases de Datos", "Lab-2"), ("12:20", "14:00", "Redes", "Lab-3")],
    4: [("09:00", "10:50", "Tutoría", "Aula-1")],
}
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

FRASES = [
    "hoy también lo estás haciendo increíble ♡", "un commit a la vez ✧", "toma agüita, angel 💧",
    "eres la main character de este semestre", "descansar también es productivo (˘ω˘)",
    "tu yo del futuro te va a agradecer ✨", "si compila, es arte", "pequeños pasos, grandes sueños ♡",
    "brilla aunque el wifi no ✧", "el bug no es tuyo, es del universo", "ánimo, ya casi es viernes ☆",
    "hoy es un buen día para aprender algo nuevo", "respira hondo y sigue ♡", "eres más fuerte que cualquier examen",
    "guarda tu progreso (ctrl+s y en la vida)", "lo cute no quita lo programador ✧", "un café, una canción y a darle",
    "nadie decora un escritorio como tú ♡", "tus ideas valen mucho ✨", "error 404: flojera not found",
]

CSS = b"""
window { background: transparent; }
.card {
  background: alpha(#fff5fa, 0.82);
  border: 2px solid alpha(#ff8fbf, 0.6);
  border-radius: 24px;
  padding: 14px 18px;
  box-shadow: 0 4px 18px alpha(#e25d99, 0.18);
  color: #5f3b6e;
  font-family: "JetBrainsMono Nerd Font";
}
.h      { color: #e25d99; font-weight: 800; font-size: 12px; }
.dim    { color: #ad8bbb; font-size: 11px; }
.big    { font-size: 15px; font-weight: 800; }
.clock  { font-size: 72px; font-weight: 800; color: #e25d99; letter-spacing: -2px; }
.sec    { font-size: 22px; font-weight: 800; color: #caa6f5; }
.temp   { font-size: 34px; font-weight: 800; color: #e25d99; }
.emoji  { font-size: 40px; }
.now    { background: alpha(#ffd6e9, 0.9); border-radius: 16px; padding: 10px 12px; }
.next   { background: alpha(#eadbfb, 0.7); border-radius: 14px; padding: 8px 12px; }
.quote  { font-size: 14px; font-style: italic; padding: 10px 22px; }
progressbar trough   { background: alpha(#caa6f5, 0.22); border-radius: 8px; min-height: 9px; }
progressbar progress { background: linear-gradient(to right, #8fc6f7, #caa6f5, #ff8fbf); border-radius: 8px; min-height: 9px; }
button {
  background: alpha(#ffd6e9, 0.8); color: #e25d99; border: none; box-shadow: none;
  border-radius: 999px; padding: 4px 14px; font-weight: 800;
}
button:hover { background: #ff8fbf; color: #fff; }
textview, textview text { background: transparent; color: #5f3b6e; font-size: 13px; }
.notes { background: alpha(#fff6c9, 0.9); border-color: alpha(#f5ce6b, 0.7); }
.day     { font-size: 12px; padding: 3px 0; border-radius: 999px; }
.weekend { color: #ad8bbb; }
.today   { background: #ff8fbf; color: #ffffff; font-weight: 800; }
.marked  { background: alpha(#caa6f5, 0.35); color: #e25d99; font-weight: 800; }
"""


# ───────────── base: ventanita pegada al escritorio ─────────────
class Card(Gtk.Window):
    def __init__(self, ns, edges, margins, keyboard=False, css="card"):
        super().__init__()
        LS.init_for_window(self)
        LS.set_namespace(self, "angel-desk-" + ns)
        LS.set_layer(self, LS.Layer.OVERLAY if PREVIEW else LS.Layer.BOTTOM)
        for e in edges:
            LS.set_anchor(self, e, True)
        for e, m in margins.items():
            LS.set_margin(self, e, m)
        LS.set_keyboard_mode(self, LS.KeyboardMode.ON_DEMAND if keyboard and not PREVIEW else LS.KeyboardMode.NONE)
        self.set_app_paintable(True)
        vis = self.get_screen().get_rgba_visual()
        if vis:
            self.set_visual(vis)
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        for c in css.split():
            self.box.get_style_context().add_class(c)
        self.add(self.box)

    @staticmethod
    def label(text="", cls=None, xalign=0, wrap=False):
        l = Gtk.Label(label=text, xalign=xalign)
        if cls:
            for c in cls.split():
                l.get_style_context().add_class(c)
        if wrap:
            l.set_line_wrap(True); l.set_max_width_chars(34)
        return l


T, B, L, R = LS.Edge.TOP, LS.Edge.BOTTOM, LS.Edge.LEFT, LS.Edge.RIGHT
X = 34  # margen lateral


# ───────────── reloj ─────────────
class Clock(Card):
    def __init__(self):
        super().__init__("clock", [T, L], {T: 10, L: X})
        row = Gtk.Box(spacing=8)
        self.hm = self.label(cls="clock"); self.s = self.label(cls="sec")
        self.s.set_valign(Gtk.Align.END); self.s.set_margin_bottom(14)
        row.pack_start(self.hm, False, False, 0); row.pack_start(self.s, False, False, 0)
        self.d = self.label(cls="big")
        self.g = self.label(cls="dim")
        for w in (row, self.d, self.g):
            self.box.pack_start(w, False, False, 0)
        self.box.set_size_request(420, -1)
        self.tick(); GLib.timeout_add(1000, self.tick)

    def tick(self):
        n = dt.datetime.now()
        self.hm.set_text(n.strftime("%H:%M")); self.s.set_text(n.strftime("%S"))
        self.d.set_text(f"{DIAS[n.weekday()].capitalize()} {n.day} de {MESES[n.month - 1]} ♡")
        h = n.hour
        self.g.set_text("Ya duérmete, __NAME__ (˘ω˘)ᶻᶻ" if h < 6 else "Buenos días, __NAME__ ☀︎" if h < 12
                        else "Buenas tardes, __NAME__ ✧" if h < 19 else "Buenas noches, __NAME__ ☾")
        return True


# ───────────── clima (wttr.in, ubicación automática) ─────────────
ICON = {113: "☀️", 116: "⛅", 119: "☁️", 122: "☁️", 143: "🌫️", 248: "🌫️", 260: "🌫️", 200: "⛈️", 386: "⛈️", 389: "⛈️",
        176: "🌦️", 263: "🌦️", 266: "🌧️", 293: "🌦️", 296: "🌧️", 299: "🌧️", 302: "🌧️", 305: "🌧️", 308: "🌧️", 353: "🌦️",
        356: "🌧️", 359: "🌧️", 179: "🌨️", 227: "🌨️", 230: "❄️", 323: "🌨️", 326: "🌨️", 329: "❄️", 332: "❄️", 335: "❄️", 338: "❄️"}


class Weather(Card):
    def __init__(self):
        super().__init__("weather", [T, L], {T: 190, L: X})
        row = Gtk.Box(spacing=14)
        self.ic = self.label("🌸", "emoji")
        col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.t = self.label("--°", "temp"); self.desc = self.label("Cargando clima…", "dim", wrap=True)
        col.pack_start(self.t, False, False, 0); col.pack_start(self.desc, False, False, 0)
        row.pack_start(self.ic, False, False, 0); row.pack_start(col, True, True, 0)
        self.extra = self.label("", "dim")
        self.box.pack_start(row, False, False, 0); self.box.pack_start(self.extra, False, False, 0)
        self.box.set_size_request(420, -1)
        self.fetch(); GLib.timeout_add_seconds(1800, self.fetch)

    def fetch(self):
        def run():
            try:
                req = urllib.request.Request("https://wttr.in/?format=j1&lang=es", headers={"User-Agent": "curl/8"})
                d = json.load(urllib.request.urlopen(req, timeout=15))
                GLib.idle_add(self.show, d)
            except Exception:
                GLib.idle_add(self.desc.set_text, "Sin internet para el clima (｡•́︿•̀｡)")
        threading.Thread(target=run, daemon=True).start()
        return True

    def show(self, d):
        c = d["current_condition"][0]
        place = d["nearest_area"][0]["areaName"][0]["value"]
        today = d["weather"][0]
        self.ic.set_text(ICON.get(int(c["weatherCode"]), "🌸"))
        self.t.set_text(f'{c["temp_C"]}°')
        desc = (c.get("lang_es") or c["weatherDesc"])[0]["value"].lower()
        self.desc.set_text(f"{desc[:1].upper() + desc[1:]} · {place}")
        self.extra.set_text(f'↑ {today["maxtempC"]}°  ↓ {today["mintempC"]}°   💧 {c["humidity"]}%   Sensación {c["FeelsLikeC"]}°')


# ───────────── próxima clase ─────────────
def hm(s):
    h, m = map(int, s.split(":")); return h * 60 + m


class School(Card):
    def __init__(self):
        super().__init__("school", [T, L], {T: 330, L: X})
        self.box.pack_start(self.label("󰑴  Escuela", "h"), False, False, 0)
        self.now = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2); self.now.get_style_context().add_class("now")
        self.now_t = self.label("", "dim"); self.now_s = self.label("", "big"); self.now_r = self.label("", "dim")
        self.bar = Gtk.ProgressBar(); self.bar.set_margin_top(4); self.bar.set_no_show_all(True)
        for w in (self.now_t, self.now_s, self.now_r, self.bar):
            self.now.pack_start(w, False, False, 0)
        self.nxt = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2); self.nxt.get_style_context().add_class("next")
        self.nxt_t = self.label("", "dim"); self.nxt_s = self.label("", "big")
        self.nxt.pack_start(self.nxt_t, False, False, 0); self.nxt.pack_start(self.nxt_s, False, False, 0)
        self.box.pack_start(self.now, False, False, 0); self.box.pack_start(self.nxt, False, False, 0)
        self.box.set_size_request(420, -1)
        self.warned = set()
        self.tick(); GLib.timeout_add_seconds(20, self.tick)

    def upcoming(self, n):
        """siguiente clase después de ahora (puede ser otro día)"""
        mins = n.hour * 60 + n.minute
        for add in range(0, 8):
            d = (n.weekday() + add) % 7
            for c in H.get(d, []):
                if add > 0 or hm(c[0]) > mins:
                    return add, d, c
        return None

    def tick(self):
        n = dt.datetime.now(); mins = n.hour * 60 + n.minute; wd = n.weekday()
        cur = next((c for c in H.get(wd, []) if hm(c[0]) <= mins < hm(c[1])), None)
        if cur:
            a, b = hm(cur[0]), hm(cur[1])
            self.now_t.set_text(f"Ahorita · {cur[0]}–{cur[1]}")
            self.now_s.set_text(cur[2]); self.now_r.set_text(f"📍 {cur[3]} · faltan {b - mins} min")
            self.bar.set_fraction((mins - a) / (b - a)); self.bar.show()
        else:
            self.bar.hide()
            if wd >= 5:
                self.now_t.set_text("Fin de semana"); self.now_s.set_text("Sin clases ♡ a descansar"); self.now_r.set_text("")
            elif H.get(wd) and mins >= hm(H[wd][-1][1]):
                self.now_t.set_text("Ya saliste"); self.now_s.set_text("Terminaste por hoy ✧"); self.now_r.set_text("")
            elif 11 * 60 + 50 <= mins < 12 * 60 + 20:
                self.now_t.set_text("11:50–12:20"); self.now_s.set_text("Receso 🍙"); self.now_r.set_text("A comer algo rico")
            else:
                self.now_t.set_text("Libre"); self.now_s.set_text("Hora libre (˘ᵕ˘)"); self.now_r.set_text("")
        up = self.upcoming(n)
        if up:
            add, d, c = up
            if add == 0:
                left = hm(c[0]) - mins
                when = f"en {left} min" if left < 60 else f"a las {c[0]}"
                if left <= CFG["aviso_clase_min"] and (d, c[0]) not in self.warned and not cur:
                    self.warned.add((d, c[0]))
                    subprocess.Popen(["notify-send", "-a", "angel", "-i", "x-office-calendar",
                                      f"🎒 {c[2]} en {left} min", f"📍 {c[3]} ♡"])
            else:
                when = ("mañana" if add == 1 else DIAS[d]) + f" {c[0]}"
            self.nxt_t.set_text(f"Sigue · {when}"); self.nxt_s.set_text(f"{c[2]}  ·  {c[3]}")
        return True


# ───────────── medidores tipo juego ─────────────
def temp_c():
    try:
        t = psutil.sensors_temperatures().get("coretemp") or []
        return max(x.current for x in t) if t else 0
    except Exception:
        return 0


class Meters(Card):
    ROWS = [("💢", "Estrés", "cpu"), ("🔋", "Energía", "bat"), ("🧠", "Memoria", "ram"), ("🔥", "Calor", "temp")]

    def __init__(self):
        super().__init__("meters", [T, L], {T: 560, L: X})
        self.box.pack_start(self.label("✧  Estado de __name__.exe", "h"), False, False, 0)
        grid = Gtk.Grid(column_spacing=10, row_spacing=8)
        self.w = {}
        for i, (ic, name, key) in enumerate(self.ROWS):
            grid.attach(self.label(f"{ic} {name}", "dim"), 0, i, 1, 1)
            pb = Gtk.ProgressBar(); pb.set_hexpand(True); pb.set_valign(Gtk.Align.CENTER)
            val = self.label("", "big", xalign=1); val.set_width_chars(5)
            grid.attach(pb, 1, i, 1, 1); grid.attach(val, 2, i, 1, 1)
            self.w[key] = (pb, val)
        self.mood = self.label("", "dim")
        self.box.pack_start(grid, False, False, 0); self.box.pack_start(self.mood, False, False, 0)
        self.box.set_size_request(420, -1)
        psutil.cpu_percent(None)
        self.tick(); GLib.timeout_add(2000, self.tick)

    def tick(self):
        cpu = psutil.cpu_percent(None)
        ram = psutil.virtual_memory().percent
        b = psutil.sensors_battery()
        bat = b.percent if b else 100
        tc = temp_c()
        for key, v, txt in (("cpu", cpu, f"{cpu:.0f}%"), ("bat", bat, f"{bat:.0f}%"),
                            ("ram", ram, f"{ram:.0f}%"), ("temp", min(tc, 100), f"{tc:.0f}°")):
            pb, lab = self.w[key]; pb.set_fraction(v / 100); lab.set_text(txt)
        if cpu > 80 or tc > 85: m = "Ánimo: aaaAAAA estoy al máximo (╯°□°)╯"
        elif bat < 20 and not (b and b.power_plugged): m = "Ánimo: con sueñito… cárgame plis (╥﹏╥)"
        elif cpu < 15: m = "Ánimo: chill total ♡ (˘ω˘)"
        else: m = "Ánimo: chambeando bonito ✧ (•̀ᴗ•́)و"
        if b and b.power_plugged: m += "   ⚡ Cargando"
        self.mood.set_text(m)
        return True


# ───────────── cuenta regresiva ─────────────
class Countdown(Card):
    def __init__(self):
        super().__init__("countdown", [T, L], {T: 770, L: X})
        self.box.pack_start(self.label("󰔟  Cuenta regresiva", "h"), False, False, 0)
        self.rows = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.box.pack_start(self.rows, False, False, 0)
        self.box.set_size_request(420, -1)
        self.tick(); GLib.timeout_add_seconds(600, self.tick)

    def tick(self):
        for c in self.rows.get_children():
            self.rows.remove(c)
        today = dt.date.today()
        items = []
        for it in CFG["cuenta_regresiva"]:
            try:
                d = dt.date.fromisoformat(it["fecha"])
            except Exception:
                continue
            if d >= today:
                items.append(((d - today).days, it["que"]))
        for days, que in sorted(items)[:3]:
            r = Gtk.Box(spacing=8)
            r.pack_start(self.label(que, "big"), True, True, 0)
            r.pack_start(self.label("¡Hoy! 🎉" if days == 0 else "Mañana ♡" if days == 1 else f"{days} días", "h", xalign=1), False, False, 0)
            self.rows.pack_start(r, False, False, 0)
        if not items:
            self.rows.pack_start(self.label("Agrega fechas en ~/.config/angel-desk/config.json", "dim"), False, False, 0)
        self.rows.show_all()
        return True


# ───────────── polaroids ─────────────
class Polaroid(Card):
    W, Hh = 250, 300

    def __init__(self):
        super().__init__("polaroid", [T, R], {T: 190, R: X + 20}, css="")
        self.area = Gtk.DrawingArea(); self.area.set_size_request(self.W + 40, self.Hh + 40)
        self.area.connect("draw", self.draw)
        self.box.pack_start(self.area, False, False, 0)
        exts = (".jpg", ".jpeg", ".png", ".webp")
        self.files = [f for d in CFG["polaroids"] for f in glob.glob(os.path.expanduser(d) + "/**/*", recursive=True)
                      if f.lower().endswith(exts)]
        random.shuffle(self.files)
        self.i = -1; self.pix = None; self.angle = 0
        self.next(); GLib.timeout_add_seconds(45, self.next)

    def next(self):
        if not self.files:
            return True
        self.i = (self.i + 1) % len(self.files)
        f = self.files[self.i]
        try:
            p = GdkPixbuf.Pixbuf.new_from_file_at_scale(f, 600, 600, True)
            w, h = p.get_width(), p.get_height(); tw, th = self.W - 24, self.Hh - 70
            s = max(tw / w, th / h)
            p = p.scale_simple(int(w * s) + 1, int(h * s) + 1, GdkPixbuf.InterpType.BILINEAR)
            ox, oy = (p.get_width() - tw) // 2, (p.get_height() - th) // 2
            self.pix = p.new_subpixbuf(ox, oy, tw, th)
            self.caption = os.path.splitext(os.path.basename(f))[0][:22]
        except Exception:
            self.pix = None
        self.angle = random.uniform(-5, 5)
        self.area.queue_draw()
        return True

    def draw(self, _w, cr):
        if not self.pix:
            return
        cx, cy = (self.W + 40) / 2, (self.Hh + 40) / 2
        cr.translate(cx, cy); cr.rotate(math.radians(self.angle)); cr.translate(-self.W / 2, -self.Hh / 2)
        cr.set_source_rgba(0.89, 0.36, 0.64, 0.18); cr.rectangle(4, 6, self.W, self.Hh); cr.fill()  # sombrita
        cr.set_source_rgb(1, 1, 1); cr.rectangle(0, 0, self.W, self.Hh); cr.fill()
        Gdk.cairo_set_source_pixbuf(cr, self.pix, 12, 12); cr.paint()
        # cinta washi
        cr.save(); cr.translate(self.W / 2, 0); cr.rotate(math.radians(-4))
        cr.set_source_rgba(1.0, 0.56, 0.78, 0.55); cr.rectangle(-42, -10, 84, 22); cr.fill(); cr.restore()
        cr.set_source_rgb(0.36, 0.23, 0.43)
        lay = PangoCairo.create_layout(cr)
        lay.set_font_description(Pango.FontDescription("Noto Sans Italic 10"))
        lay.set_text(self.caption + " ♡", -1)
        tw, _th = lay.get_pixel_size()
        cr.move_to((self.W - tw) / 2, self.Hh - 36); PangoCairo.show_layout(cr, lay)


# ───────────── pomodoro ─────────────
class Pomodoro(Card):
    MODES = [("Enfoque", 25), ("Descanso", 5)]

    def __init__(self):
        super().__init__("pomodoro", [T, R], {T: 540, R: X})
        self.box.pack_start(self.label("🍅  Pomodoro", "h"), False, False, 0)
        row = Gtk.Box(spacing=14)
        self.ring = Gtk.DrawingArea(); self.ring.set_size_request(110, 110); self.ring.connect("draw", self.draw)
        col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6); col.set_valign(Gtk.Align.CENTER)
        self.mode_l = self.label("", "big"); self.count_l = self.label("", "dim")
        btns = Gtk.Box(spacing=6)
        self.play = Gtk.Button(label="▶ Va"); self.play.connect("clicked", self.toggle)
        rst = Gtk.Button(label="↺"); rst.connect("clicked", self.reset)
        btns.pack_start(self.play, False, False, 0); btns.pack_start(rst, False, False, 0)
        for w in (self.mode_l, self.count_l, btns):
            col.pack_start(w, False, False, 0)
        row.pack_start(self.ring, False, False, 0); row.pack_start(col, True, True, 0)
        self.box.pack_start(row, False, False, 0)
        self.box.set_size_request(300, -1)
        self.mode = 0; self.done = 0; self.running = False
        self.left = self.MODES[0][1] * 60
        self.update(); GLib.timeout_add(1000, self.tick)

    def toggle(self, *_):
        self.running = not self.running; self.update()

    def reset(self, *_):
        self.running = False; self.mode = 0; self.left = self.MODES[0][1] * 60; self.update()

    def tick(self):
        if self.running:
            self.left -= 1
            if self.left <= 0:
                if self.mode == 0:
                    self.done += 1
                    msg = ("🍅 ¡Pomodoro terminado!", "Tómate 5 minutitos ♡")
                else:
                    msg = ("✨ Descanso terminado", "A darle otra vez (•̀ᴗ•́)و")
                subprocess.Popen(["notify-send", "-a", "angel", *msg])
                subprocess.Popen(["pw-play", f"{SND}/login.ogg"], stderr=subprocess.DEVNULL)
                self.mode = 1 - self.mode; self.left = self.MODES[self.mode][1] * 60
            self.update()
        return True

    def update(self):
        name, _ = self.MODES[self.mode]
        self.mode_l.set_text(name + (" ♡" if self.running else " (pausa)"))
        self.count_l.set_text("🍅" * min(self.done, 8) if self.done else "Aún sin tomatitos")
        self.play.set_label("❚❚ Pausa" if self.running else "▶ Va")
        self.ring.queue_draw()

    def draw(self, _w, cr):
        total = self.MODES[self.mode][1] * 60
        frac = self.left / total
        cx = cy = 55; r = 46
        cr.set_line_width(10); cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.set_source_rgba(0.76, 0.65, 0.96, 0.25); cr.arc(cx, cy, r, 0, 2 * math.pi); cr.stroke()
        g = cairo.LinearGradient(0, 0, 110, 110)
        if self.mode == 0:
            g.add_color_stop_rgb(0, 1.0, 0.56, 0.78); g.add_color_stop_rgb(1, 0.89, 0.36, 0.64)
        else:
            g.add_color_stop_rgb(0, 0.56, 0.81, 0.97); g.add_color_stop_rgb(1, 0.76, 0.65, 0.96)
        cr.set_source(g); cr.arc(cx, cy, r, -math.pi / 2, -math.pi / 2 + 2 * math.pi * frac); cr.stroke()
        cr.set_source_rgb(0.36, 0.23, 0.43)
        cr.select_font_face("JetBrainsMono Nerd Font", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(20)
        t = f"{self.left // 60:02d}:{self.left % 60:02d}"
        e = cr.text_extents(t); cr.move_to(cx - e.width / 2 - e.x_bearing, cy + e.height / 2); cr.show_text(t)


# ───────────── notitas ─────────────
class Notes(Card):
    FILE = f"{CONF_DIR}/notitas.txt"

    def __init__(self):
        super().__init__("notes", [T, R], {T: 760, R: X}, keyboard=True, css="card notes")
        self.box.pack_start(self.label("📌  Notitas", "h"), False, False, 0)
        self.tv = Gtk.TextView(); self.tv.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.tv.set_size_request(270, 120)
        buf = self.tv.get_buffer()
        try:
            buf.set_text(open(self.FILE).read())
        except FileNotFoundError:
            buf.set_text("• Haz clic aquí y escribe ♡\n• Se guarda solito")
        self.save_id = None
        buf.connect("changed", self.changed)
        self.box.pack_start(self.tv, True, True, 0)

    def changed(self, buf):
        if self.save_id:
            GLib.source_remove(self.save_id)
        self.save_id = GLib.timeout_add(800, self.save)

    def save(self):
        b = self.tv.get_buffer()
        open(self.FILE, "w").write(b.get_text(b.get_start_iter(), b.get_end_iter(), True))
        self.save_id = None
        return False



# ───────────── calendario del mes ─────────────
class Calendar(Card):
    def __init__(self):
        super().__init__("calendar", [T, R], {T: 10, R: 440})
        head = Gtk.Box(spacing=6)
        prev = Gtk.Button(label="‹"); nxt = Gtk.Button(label="›")
        prev.connect("clicked", lambda *_: self.move(-1)); nxt.connect("clicked", lambda *_: self.move(1))
        self.title = self.label("", "h", xalign=0.5)
        head.pack_start(prev, False, False, 0); head.pack_start(self.title, True, True, 0); head.pack_start(nxt, False, False, 0)
        self.grid = Gtk.Grid(column_spacing=4, row_spacing=3, column_homogeneous=True)
        self.foot = self.label("", "dim", xalign=0.5)
        self.box.pack_start(head, False, False, 0); self.box.pack_start(self.grid, False, False, 0)
        self.box.pack_start(self.foot, False, False, 0)
        self.box.set_size_request(290, -1)
        t = dt.date.today(); self.y, self.m = t.year, t.month
        self.draw(); GLib.timeout_add_seconds(600, self.draw)

    def move(self, d):
        self.m += d
        if self.m == 0: self.m, self.y = 12, self.y - 1
        if self.m == 13: self.m, self.y = 1, self.y + 1
        self.draw()

    def draw(self):
        import calendar
        for c in self.grid.get_children(): self.grid.remove(c)
        self.title.set_text(f"{MESES[self.m - 1].capitalize()} {self.y}")
        for i, d in enumerate("LMMJVSD"):
            self.grid.attach(self.label(d, "dim", xalign=0.5), i, 0, 1, 1)
        marks = {}
        for it in CFG["cuenta_regresiva"]:
            try: f = dt.date.fromisoformat(it["fecha"])
            except Exception: continue
            if (f.year, f.month) == (self.y, self.m): marks[f.day] = it["que"]
        today = dt.date.today()
        for r, week in enumerate(calendar.Calendar().monthdayscalendar(self.y, self.m), start=1):
            for c, day in enumerate(week):
                if not day: continue
                l = self.label(str(day), "day", xalign=0.5)
                if (self.y, self.m, day) == (today.year, today.month, today.day): l.get_style_context().add_class("today")
                elif day in marks: l.get_style_context().add_class("marked"); l.set_tooltip_text(marks[day])
                elif c >= 5: l.get_style_context().add_class("weekend")
                self.grid.attach(l, c, r, 1, 1)
        self.foot.set_text("  ·  ".join(f"♡ {d}: {q}" for d, q in sorted(marks.items()))[:60] if marks else "")
        self.grid.show_all()
        return True


# ───────────── frase del día ─────────────
class Quote(Card):
    def __init__(self):
        super().__init__("quote", [B], {B: 12})
        self.l = self.label("", "quote", xalign=0.5)
        self.box.pack_start(self.l, False, False, 0)
        self.tick(); GLib.timeout_add_seconds(3600, self.tick)

    def tick(self):
        n = dt.date.today()
        f = FRASES[n.toordinal() % len(FRASES)]
        self.l.set_text("✧ " + f[:1].upper() + f[1:] + " ✧")
        return True


if __name__ == "__main__":
    prov = Gtk.CssProvider(); prov.load_from_data(CSS)
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov, 800)
    wins = []
    for cls in (Clock, Weather, School, Meters, Countdown, Calendar, Polaroid, Pomodoro, Notes, Quote):
        try:
            w = cls(); w.show_all(); wins.append(w)
        except Exception as e:
            print("widget falló:", cls.__name__, e)
    Gtk.main()
