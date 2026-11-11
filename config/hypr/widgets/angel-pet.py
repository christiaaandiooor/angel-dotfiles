#!/usr/bin/env python3
# 🪽 mascota angelito: camina sobre la ventana activa (o sobre el dock si no hay ventana)
# es "click-through": nunca estorba al mouse
import math, random, json, subprocess, cairo
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
from gi.repository import Gtk, Gdk, GLib, GtkLayerShell

W, H = 64, 72           # tamaño de la ventanita
BAR = 26                # hyprbars dibuja la barra 26px arriba de la ventana
DOCK_TOP = 72           # el dock ocupa ~70px abajo
FPS = 24

PINK = (1.0, 0.56, 0.78); PINK_L = (1.0, 0.84, 0.93); DEEP = (0.89, 0.36, 0.64)
LAV = (0.76, 0.65, 0.96); TEXT = (0.36, 0.23, 0.43); BLUE = (0.56, 0.81, 0.97)


def hypr(cmd):
    try:
        return json.loads(subprocess.run(["hyprctl", cmd, "-j"], capture_output=True, text=True, timeout=1).stdout or "{}")
    except Exception:
        return {}


class Pet(Gtk.Window):
    def __init__(self):
        super().__init__()
        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_namespace(self, "angel-pet")
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.TOP)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.LEFT, True)
        GtkLayerShell.set_exclusive_zone(self, -1)
        GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.NONE)
        self.set_size_request(W, H)
        self.set_app_paintable(True)
        vis = self.get_screen().get_rgba_visual()
        if vis: self.set_visual(vis)
        self.connect("draw", self.draw)
        self.connect("realize", lambda *_: self.get_window().input_shape_combine_region(cairo.Region(), 0, 0))

        mon = hypr("monitors")
        m = next((x for x in mon if x.get("focused")), mon[0] if mon else {"x": 0, "y": 0, "width": 1920, "height": 1080, "scale": 1})
        sc = m.get("scale", 1) or 1
        self.mx, self.my = m["x"], m["y"]
        self.mw, self.mh = int(m["width"] / sc), int(m["height"] / sc)

        self.x = self.mw / 2; self.y = self.mh - DOCK_TOP - H
        self.dir = 1; self.speed = 1.6
        self.state = "walk"; self.timer = 120
        self.t = 0; self.blink = 0
        self.floor = (0, self.mw, self.y)   # (x0, x1, y) de la "repisa" donde camina
        self.fall = 0.0

        GLib.timeout_add(1000 // FPS, self.step)
        GLib.timeout_add(400, self.find_floor)

    # dónde pararse: arriba de la ventana activa (con su barrita) o arriba del dock
    def find_floor(self):
        a = hypr("activewindow")
        dock = (40, self.mw - 40, self.mh - DOCK_TOP - H)
        if a and a.get("at") and a.get("mapped", True) and not a.get("hidden"):
            x, y = a["at"][0] - self.mx, a["at"][1] - self.my
            w = a["size"][0]
            top = y - BAR - H + 6
            if a.get("fullscreen") or top < 40 or w < W * 2:
                self.floor = dock
            else:
                self.floor = (x + 4, x + w - W - 4, top)
        else:
            self.floor = dock
        return True

    def step(self):
        self.t += 1
        x0, x1, fy = self.floor
        # caer / subir suavecito a la nueva repisa
        if abs(self.y - fy) > 1:
            self.y += (fy - self.y) * 0.18
        else:
            self.y = fy
        if self.x < x0 or self.x > x1:
            self.x = min(max(self.x, x0), max(x0, x1))

        self.timer -= 1
        if self.timer <= 0:
            r = random.random()
            if r < 0.55: self.state, self.timer = "walk", random.randint(90, 260); self.dir = random.choice((-1, 1))
            elif r < 0.85: self.state, self.timer = "idle", random.randint(60, 160)
            else: self.state, self.timer = "sleep", random.randint(200, 420)
        if self.state == "walk":
            self.x += self.dir * self.speed
            if self.x <= x0 or self.x >= x1:
                self.dir *= -1
        if self.blink > 0: self.blink -= 1
        elif random.random() < 0.012: self.blink = 4

        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.LEFT, int(self.x))
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, int(self.y))
        self.queue_draw()
        return True

    # --- dibujito (todo con cairo, sin imágenes) ---
    def draw(self, _w, cr):
        cr.set_operator(cairo.OPERATOR_CLEAR); cr.paint(); cr.set_operator(cairo.OPERATOR_OVER)
        t = self.t / FPS
        walking = self.state == "walk"
        sleeping = self.state == "sleep"
        hop = abs(math.sin(t * 7)) * 5 if walking else (math.sin(t * 2) * 1.2 if not sleeping else 0)
        squash = 1 + (0.06 * math.cos(t * 14) if walking else 0)
        cx, base = W / 2, H - 4
        bw, bh = 21 * squash, 19 / squash
        cy = base - bh - hop

        # sombrita
        cr.save(); cr.translate(cx, base); cr.scale(1, 0.25)
        cr.arc(0, 0, 16 - hop, 0, 2 * math.pi); cr.restore()
        cr.set_source_rgba(*DEEP, 0.18); cr.fill()

        # alitas (aletean)
        flap = math.sin(t * (14 if walking else 5)) * 0.35
        for s in (-1, 1):
            cr.save(); cr.translate(cx + s * bw * 0.8, cy - 2); cr.rotate(s * (0.5 + flap)); cr.scale(s, 1)
            cr.move_to(0, 0); cr.curve_to(10, -14, 20, -6, 16, 4); cr.curve_to(10, 6, 4, 4, 0, 0)
            cr.set_source_rgba(1, 1, 1, 0.95); cr.fill_preserve()
            cr.set_source_rgba(*BLUE, 0.9); cr.set_line_width(1.4); cr.stroke(); cr.restore()

        # cuerpito
        cr.save(); cr.translate(cx, cy); cr.scale(bw, bh); cr.arc(0, 0, 1, 0, 2 * math.pi); cr.restore()
        g = cairo.RadialGradient(cx - 6, cy - 8, 2, cx, cy, bw * 1.2)
        g.add_color_stop_rgb(0, *PINK_L); g.add_color_stop_rgb(1, *PINK)
        cr.set_source(g); cr.fill_preserve()
        cr.set_source_rgb(*DEEP); cr.set_line_width(1.6); cr.stroke()

        # aureola
        hy = cy - bh - 8 + math.sin(t * 3) * 1.5
        cr.save(); cr.translate(cx, hy); cr.scale(11, 3.2); cr.arc(0, 0, 1, 0, 2 * math.pi); cr.restore()
        cr.set_source_rgba(*LAV, 0.95); cr.set_line_width(2.6); cr.stroke()

        # carita
        ex = 6.5; ey = cy - 2; look = self.dir * 2 if walking else 0
        cr.set_source_rgb(*TEXT)
        if sleeping or self.blink:
            for s in (-1, 1):
                cr.move_to(cx + s * ex + look - 3, ey); cr.curve_to(cx + s * ex + look - 1, ey + 2.5, cx + s * ex + look + 1, ey + 2.5, cx + s * ex + look + 3, ey)
            cr.set_line_width(1.6); cr.stroke()
        else:
            for s in (-1, 1):
                cr.arc(cx + s * ex + look, ey, 2.6, 0, 2 * math.pi); cr.fill()
                cr.set_source_rgb(1, 1, 1); cr.arc(cx + s * ex + look + 0.9, ey - 0.9, 0.9, 0, 2 * math.pi); cr.fill()
                cr.set_source_rgb(*TEXT)
        # boquita
        cr.move_to(cx + look - 2.2, ey + 5); cr.curve_to(cx + look - 1, ey + 7, cx + look + 1, ey + 7, cx + look + 2.2, ey + 5)
        cr.set_line_width(1.3); cr.stroke()
        # cachetitos
        cr.set_source_rgba(*DEEP, 0.35)
        for s in (-1, 1):
            cr.save(); cr.translate(cx + s * 12 + look, ey + 4); cr.scale(3.2, 2); cr.arc(0, 0, 1, 0, 2 * math.pi); cr.restore(); cr.fill()

        # zZz
        if sleeping:
            cr.select_font_face("Noto Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            for i, size in enumerate((8, 10, 12)):
                ph = (t * 0.8 + i * 0.33) % 1
                cr.set_font_size(size); cr.set_source_rgba(*LAV, 1 - ph)
                cr.move_to(cx + 10 + i * 5, cy - bh - 4 - ph * 10 - i * 4); cr.show_text("z")


if __name__ == "__main__":
    p = Pet(); p.connect("destroy", Gtk.main_quit); p.show_all(); Gtk.main()
