#!/usr/bin/env python3
# ✧ protector de pantalla angel: reloj grande, canción, brillitos que flotan y un kaomoji rebotando
# lo abre hypridle cuando estás conectada a la corriente; se cierra al mover el mouse o tocar una tecla
import math, os, random, subprocess, datetime as dt, cairo
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
gi.require_version("PangoCairo", "1.0")
from gi.repository import Gtk, Gdk, GLib, Pango, PangoCairo, GtkLayerShell as LS

DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
KAO = ["(˘ω˘)ᶻᶻ", "(｡•ᴗ•｡)", "ʕ•ᴥ•ʔ", "ฅ^•ﻌ•^ฅ", "(◕‿◕✿)", "(っ˘ڡ˘ς)", "(´｡• ω •｡`) ♡", "/ᐠ｡ꞈ｡ᐟ\\"]
PINK, DEEP, LAV, BLUE, TEXT = (1, .56, .78), (.89, .36, .64), (.76, .65, .96), (.56, .81, .97), (.36, .23, .43)
FPS = 30


class Saver(Gtk.Window):
    def __init__(self):
        super().__init__()
        LS.init_for_window(self)
        LS.set_namespace(self, "angel-screensaver")
        LS.set_layer(self, LS.Layer.OVERLAY)
        for e in (LS.Edge.TOP, LS.Edge.BOTTOM, LS.Edge.LEFT, LS.Edge.RIGHT):
            LS.set_anchor(self, e, True)
        LS.set_exclusive_zone(self, -1)
        LS.set_keyboard_mode(self, LS.KeyboardMode.NONE if os.environ.get("ANGEL_PREVIEW") else LS.KeyboardMode.EXCLUSIVE)
        self.set_app_paintable(True)
        vis = self.get_screen().get_rgba_visual()
        if vis: self.set_visual(vis)
        self.add_events(Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.KEY_PRESS_MASK)
        self.start = GLib.get_monotonic_time()
        self.last_xy = None
        self.connect("motion-notify-event", self.wake)
        self.connect("button-press-event", lambda *_: Gtk.main_quit())
        self.connect("key-press-event", lambda *_: Gtk.main_quit())
        self.connect("draw", self.draw)
        self.t = 0
        self.parts = []
        self.kx, self.ky, self.kvx, self.kvy = 200.0, 200.0, 2.2, 1.7
        self.kao = random.choice(KAO); self.kcol = random.choice((PINK, LAV, BLUE, DEEP))
        self.song = ""
        self.poll_song(); GLib.timeout_add_seconds(3, self.poll_song)
        GLib.timeout_add(1000 // FPS, self.step)

    def wake(self, _w, ev):
        # ignora el primer movimiento "fantasma" al aparecer
        if (GLib.get_monotonic_time() - self.start) < 1_500_000:
            return
        xy = (round(ev.x), round(ev.y))
        if self.last_xy and (abs(xy[0] - self.last_xy[0]) + abs(xy[1] - self.last_xy[1])) > 6:
            Gtk.main_quit()
        self.last_xy = xy

    def poll_song(self):
        try:
            st = subprocess.run(["playerctl", "status"], capture_output=True, text=True, timeout=1).stdout.strip()
            if st == "Playing":
                t = subprocess.run(["playerctl", "metadata", "--format", "{{title}}  ·  {{artist}}"],
                                   capture_output=True, text=True, timeout=1).stdout.strip()
                self.song = "󰎈  " + t[:60]
            else:
                self.song = ""
        except Exception:
            self.song = ""
        return True

    def step(self):
        self.t += 1
        w, h = self.get_allocated_width(), self.get_allocated_height()
        if w > 1 and random.random() < 0.35:
            self.parts.append([random.uniform(0, w), h + 20, random.uniform(-.4, .4), random.uniform(.6, 1.6),
                               random.uniform(5, 13), random.choice((PINK, LAV, BLUE, (1, 1, 1))), random.random() < .5])
        for p in self.parts:
            p[0] += p[2] + math.sin((self.t + p[1]) / 40) * .4; p[1] -= p[3]
        self.parts = [p for p in self.parts if p[1] > -30]
        # kaomoji rebotando (tipo DVD)
        self.kx += self.kvx; self.ky += self.kvy
        if w > 1:
            if self.kx < 20 or self.kx > w - 260: self.kvx *= -1; self.bounce()
            if self.ky < 60 or self.ky > h - 40: self.kvy *= -1; self.bounce()
        self.queue_draw()
        return True

    def bounce(self):
        self.kcol = random.choice([c for c in (PINK, LAV, BLUE, DEEP) if c != self.kcol])

    @staticmethod
    def heart(cr, x, y, s):
        cr.move_to(x, y + s * .3)
        cr.curve_to(x, y, x - s * .5, y - s * .1, x - s * .5, y + s * .25)
        cr.curve_to(x - s * .5, y + s * .55, x, y + s * .75, x, y + s)
        cr.curve_to(x, y + s * .75, x + s * .5, y + s * .55, x + s * .5, y + s * .25)
        cr.curve_to(x + s * .5, y - s * .1, x, y, x, y + s * .3)
        cr.close_path()

    @staticmethod
    def star(cr, x, y, r):
        cr.move_to(x, y - r)
        for a in range(1, 9):
            ang = a * math.pi / 4 - math.pi / 2
            rr = r if a % 2 == 0 else r * .35
            cr.line_to(x + rr * math.cos(ang), y + rr * math.sin(ang))
        cr.close_path()

    def text(self, cr, txt, size, color, bold=True, center_y=None, xy=None, font="JetBrainsMono Nerd Font"):
        lay = PangoCairo.create_layout(cr)
        fd = Pango.FontDescription(f"{font} {'Bold' if bold else ''} {size}")
        lay.set_font_description(fd); lay.set_text(txt, -1)
        w, h = lay.get_pixel_size()
        if xy: x, y = xy
        else: x, y = (self.get_allocated_width() - w) / 2, center_y - h / 2
        cr.set_source_rgba(*color); cr.move_to(x, y); PangoCairo.show_layout(cr, lay)

    def draw(self, _w, cr):
        w, h = self.get_allocated_width(), self.get_allocated_height()
        fade = min(1.0, self.t / (FPS * 1.2))
        g = cairo.LinearGradient(0, 0, w, h)
        g.add_color_stop_rgba(0, 1.0, .93, .97, fade)
        g.add_color_stop_rgba(.5, .95, .91, 1.0, fade)
        g.add_color_stop_rgba(1, .9, .95, 1.0, fade)
        cr.set_operator(cairo.OPERATOR_SOURCE); cr.set_source(g); cr.paint(); cr.set_operator(cairo.OPERATOR_OVER)
        for x, y, _vx, _vy, s, c, is_heart in self.parts:
            a = max(0, min(1, y / h)) * .8 * fade
            cr.set_source_rgba(*c, a)
            (self.heart(cr, x, y, s * 1.4) if is_heart else self.star(cr, x, y, s)); cr.fill()
        n = dt.datetime.now()
        cy = h / 2
        self.text(cr, n.strftime("%H:%M"), 140, (*DEEP, fade), center_y=cy - 40)
        self.text(cr, f"{DIAS[n.weekday()]} {n.day} de {MESES[n.month - 1]}  ♡", 20, (*TEXT, .85 * fade), bold=False, center_y=cy + 70)
        if self.song:
            self.text(cr, self.song, 14, (*LAV, fade), bold=False, center_y=cy + 115)
        self.text(cr, "Mueve el mouse para volver ✧", 11, (.66, .55, .73, .8 * fade), bold=False, center_y=h - 50)
        self.text(cr, self.kao, 30, (*self.kcol, fade), font="Noto Sans", xy=(self.kx, self.ky))

if __name__ == "__main__":
    s = Saver(); s.connect("destroy", Gtk.main_quit); s.show_all(); Gtk.main()
