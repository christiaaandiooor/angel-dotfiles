#!/usr/bin/env python3
# 🎀 widget de música en el escritorio (capa "bottom": arriba del fondo, abajo de las ventanas)
# se esconde solito cuando no hay nada reproduciéndose
import os, hashlib, threading, urllib.request
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
gi.require_version("Playerctl", "2.0")
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib, GtkLayerShell, Playerctl

CACHE = os.path.expanduser("~/.cache/angel-music")
os.makedirs(CACHE, exist_ok=True)
ART = 96

CSS = b"""
window { background: transparent; }
#card {
  background: alpha(#f5fdff, 0.86);
  border: 2px solid alpha(#8fe4ff, 0.75);
  border-radius: 24px;
  padding: 14px;
  box-shadow: 0 4px 18px alpha(#5dc5e2, 0.25);
}
#title  { color: #3b6e4e; font: bold 13px "Noto Sans"; }
#artist { color: #8bbb9d; font: 11px "Noto Sans"; }
#src    { color: #5dc5e2; font: 10px "JetBrainsMono Nerd Font"; }
button {
  background: alpha(#d6f6ff, 0.7); color: #5dc5e2; border: none; box-shadow: none;
  border-radius: 999px; min-width: 30px; min-height: 30px; padding: 0;
  font: 15px "JetBrainsMono Nerd Font";
}
button:hover { background: #8fe4ff; color: #fff; }
#play { background: #8fe4ff; color: #fff; min-width: 38px; min-height: 38px; }
#play:hover { background: #5dc5e2; }
progressbar trough   { background: alpha(#a6f5af, 0.25); border-radius: 6px; min-height: 5px; }
progressbar progress { background: linear-gradient(to right, #8fe4ff, #a6f5af); border-radius: 6px; min-height: 5px; }
"""


def rounded(pix, r=16):
    import cairo
    w, h = pix.get_width(), pix.get_height()
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    cr = cairo.Context(surf)
    cr.new_sub_path()
    for (x, y, a) in ((w - r, r, -90), (w - r, h - r, 0), (r, h - r, 90), (r, r, 180)):
        import math
        cr.arc(x, y, r, math.radians(a), math.radians(a + 90))
    cr.close_path()
    Gdk.cairo_set_source_pixbuf(cr, pix, 0, 0)
    cr.fill()
    return surf


class Widget(Gtk.Window):
    def __init__(self):
        super().__init__()
        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_namespace(self, "angel-music")
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.BOTTOM)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.RIGHT, True)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, 24)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.RIGHT, 30)
        self.set_app_paintable(True)
        vis = self.get_screen().get_rgba_visual()
        if vis:
            self.set_visual(vis)

        prov = Gtk.CssProvider(); prov.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov, 800)

        card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14, name="card")
        self.art = Gtk.Image(); self.art.set_size_request(ART, ART)
        card.pack_start(self.art, False, False, 0)

        col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.src = Gtk.Label(name="src", xalign=0)
        self.title = Gtk.Label(name="title", xalign=0, max_width_chars=22, ellipsize=3)
        self.artist = Gtk.Label(name="artist", xalign=0, max_width_chars=26, ellipsize=3)
        self.bar = Gtk.ProgressBar(); self.bar.set_margin_top(6)
        btns = Gtk.Box(spacing=8); btns.set_margin_top(6); btns.set_halign(Gtk.Align.START)
        self.prev = Gtk.Button(label="󰒮"); self.play = Gtk.Button(label="󰐊", name="play"); self.next = Gtk.Button(label="󰒭")
        for b in (self.prev, self.play, self.next):
            btns.pack_start(b, False, False, 0)
        self.prev.connect("clicked", lambda *_: self.cmd("previous"))
        self.play.connect("clicked", lambda *_: self.cmd("play_pause"))
        self.next.connect("clicked", lambda *_: self.cmd("next"))
        for w in (self.src, self.title, self.artist, self.bar, btns):
            col.pack_start(w, False, False, 0)
        col.set_size_request(230, -1)
        card.pack_start(col, True, True, 0)
        self.add(card)

        self.player = None
        self.art_url = None
        self.mgr = Playerctl.PlayerManager()
        self.mgr.connect("name-appeared", lambda m, n: self.attach(n))
        self.mgr.connect("player-vanished", lambda *_: self.pick())
        for n in self.mgr.props.player_names:
            self.attach(n)
        self.pick()
        GLib.timeout_add(1000, self.tick)

    # --- reproductores ---
    def attach(self, name):
        p = Playerctl.Player.new_from_name(name)
        p.connect("playback-status", lambda *_: self.pick())
        p.connect("metadata", lambda *_: self.refresh())
        self.mgr.manage_player(p)
        self.pick()

    def pick(self):
        players = list(self.mgr.props.players)
        playing = [p for p in players if p.props.playback_status == Playerctl.PlaybackStatus.PLAYING]
        paused = [p for p in players if p.props.playback_status == Playerctl.PlaybackStatus.PAUSED]
        self.player = (playing or paused or [None])[0]
        self.refresh()

    def cmd(self, what):
        if self.player:
            try: getattr(self.player, what)()
            except GLib.Error: pass

    # --- pintar ---
    def refresh(self):
        p = self.player
        if not p:
            self.hide(); return
        try:
            title = p.get_title() or "Sin título"
            artist = p.get_artist() or ""
        except GLib.Error:
            self.hide(); return
        self.title.set_text(title)
        self.artist.set_text(artist or " ")
        self.src.set_text("♡ " + (p.props.player_name or "música").capitalize())
        playing = p.props.playback_status == Playerctl.PlaybackStatus.PLAYING
        self.play.set_label("󰏤" if playing else "󰐊")
        try:
            url = p.print_metadata_prop("mpris:artUrl")
        except GLib.Error:
            url = None
        if url != self.art_url:
            self.art_url = url
            self.load_art(url)
        self.show_all()

    def tick(self):
        p = self.player
        if p:
            try:
                length = int(p.print_metadata_prop("mpris:length") or 0)
                pos = p.get_position()
                self.bar.set_fraction(min(pos / length, 1) if length else 0)
            except (GLib.Error, ValueError, TypeError):
                self.bar.set_fraction(0)
        return True

    def load_art(self, url):
        def done(path):
            try:
                pix = GdkPixbuf.Pixbuf.new_from_file(path)
                w, h = pix.get_width(), pix.get_height()
                s = min(w, h)
                pix = pix.new_subpixbuf((w - s) // 2, (h - s) // 2, s, s).scale_simple(ART, ART, GdkPixbuf.InterpType.BILINEAR)
                self.art.set_from_surface(rounded(pix))
            except Exception:
                self.art.set_from_icon_name("audio-x-generic", Gtk.IconSize.DIALOG)
            return False

        if not url:
            done(""); return
        if url.startswith("file://"):
            done(urllib.request.url2pathname(url[7:])); return

        def fetch():
            path = os.path.join(CACHE, hashlib.md5(url.encode()).hexdigest())
            try:
                if not os.path.exists(path):
                    urllib.request.urlretrieve(url, path)
            except Exception:
                path = ""
            GLib.idle_add(done, path)
        threading.Thread(target=fetch, daemon=True).start()


if __name__ == "__main__":
    w = Widget()
    w.connect("destroy", Gtk.main_quit)
    Gtk.main()
