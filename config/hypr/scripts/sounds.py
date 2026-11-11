#!/usr/bin/env python3
# 🔔 sonidito "pop" al cambiar de escritorio (escucha los eventos de Hyprland)
import os, socket, subprocess, time
SND = os.path.expanduser("~/.local/share/sounds/angel/pop.ogg")
sock = f"{os.environ['XDG_RUNTIME_DIR']}/hypr/{os.environ['HYPRLAND_INSTANCE_SIGNATURE']}/.socket2.sock"
s = socket.socket(socket.AF_UNIX); s.connect(sock)
buf, last = b"", 0.0
while True:
    data = s.recv(4096)
    if not data: break
    buf += data
    *lines, buf = buf.split(b"\n")
    for l in lines:
        if l.startswith(b"workspacev2>>") and time.time() - last > 0.15:
            last = time.time()
            subprocess.Popen(["pw-play", "--volume", "0.6", SND], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
