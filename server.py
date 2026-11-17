"""The map view. Start it with:   python3 server.py

This runs the world in the background and serves a small web page that
draws it. Everything stays on your own computer (address 127.0.0.1).

The simulation itself lives in the `genesis/` folder and knows nothing
about this file. This file only: keeps time, answers the web page, and
handles pause / speed / save / load.
"""

import argparse
import errno
import json
import os
import re
import threading
import time
import traceback
import webbrowser
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from genesis import create_world, load_world, save_world, step
from genesis.history import events_for

ROOT = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(ROOT, "web")
SAVES_DIR = os.path.join(ROOT, "saves")

# The only files the web page may ask for.
STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
}

BASE_TICKS_PER_SECOND = 4        # what "1x" speed means
ALLOWED_SPEEDS = (1, 2, 5, 20)
SAVE_NAME = re.compile(r"^[A-Za-z0-9_-]{1,40}$")  # keeps saves inside saves/


class Game:
    """One running world plus the things the UI needs around it."""

    def __init__(self, seed):
        self.lock = threading.Lock()   # only one thread touches the world at a time
        self.paused = False
        self.speed = 1
        self.running = True            # set to False to end the background loop
        self.world_id = 0              # goes up whenever the world is replaced
        self.seq = 0                   # running number for events
        self._use_world(create_world(seed))

    def _use_world(self, world):
        self.world = world
        self.world_id += 1
        self.notable = deque(maxlen=200)   # births and deaths
        self.recent = deque(maxlen=300)    # every decision
        self.history = deque([len(world["agents"])], maxlen=300)  # population

    # ---- time -----------------------------------------------------------

    def _tick(self):
        events = step(self.world)
        for event in events:
            self.seq += 1
            event["seq"] = self.seq
            self.recent.append(event)
            if event["action"] in ("born", "die"):
                self.notable.append(event)
        if self.world["tick"] % 5 == 0:
            self.history.append(len(self.world["agents"]))
        if not self.world["agents"]:
            self.paused = True   # nobody left: stop the clock

    def loop(self):
        """Runs in a background thread, ticking at the chosen speed."""
        next_tick = time.monotonic()
        while self.running:
            with self.lock:
                running = not self.paused
                if running:
                    try:
                        self._tick()
                    except Exception:
                        traceback.print_exc()
                        self.paused = True
                interval = 1.0 / (BASE_TICKS_PER_SECOND * self.speed)
            if not running:
                time.sleep(0.05)
                next_tick = time.monotonic()
                continue
            next_tick += interval
            delay = next_tick - time.monotonic()
            if delay > 0:
                time.sleep(delay)
            else:
                next_tick = time.monotonic()   # running behind: don't pile up

    # ---- what the web page sees -----------------------------------------

    def snapshot(self, since, feed, agent_id):
        with self.lock:
            world = self.world
            cfg = world["config"]
            agents = world["agents"]
            source = self.recent if feed == "all" else self.notable
            # The feed only needs the headline; the full record (need and
            # options) is sent for the one selected agent, below.
            events = [{k: e[k] for k in ("seq", "tick", "agent", "action", "why")}
                      for e in source if e["seq"] > since][-80:]

            selected = None
            if agent_id is not None:
                agent = next((a for a in agents if a["id"] == agent_id), None)
                # The trail comes from the world itself (genesis/history.py),
                # so it survives save and load.
                trail = events_for(world, agent_id)
                if agent is not None:
                    selected = {"alive": True, "agent": agent, "trail": trail}
                else:
                    selected = {"alive": False, "id": agent_id, "trail": trail}

            energy_total = sum(a["energy"] for a in agents)
            return json.dumps({
                "world_id": self.world_id,
                "seed": world["seed"],
                "tick": world["tick"],
                "paused": self.paused,
                "speed": self.speed,
                "width": cfg["width"],
                "height": cfg["height"],
                "food_cap": cfg["food_cap"],
                "max_energy": cfg["max_energy"],
                "carry_max": cfg["carry_max"],
                "terrain": "".join(str(t) for t in world["terrain"]),
                "food": world["food"],
                "agents": [[a["id"], a["x"], a["y"], a["energy"]] for a in agents],
                "stats": {
                    "alive": len(agents),
                    "births": world["stats"]["births"],
                    "starved": world["stats"]["deaths_starved"],
                    "old_age": world["stats"]["deaths_old_age"],
                    "avg_energy": round(energy_total / len(agents)) if agents else 0,
                    "food": sum(world["food"]),
                    "generation": max((a["generation"] for a in agents), default=0),
                },
                "history": list(self.history),
                "events": events,
                "last_seq": self.seq,
                "selected": selected,
            })

    # ---- buttons --------------------------------------------------------

    def control(self, command):
        """Handle one button press from the web page. Returns a message."""
        action = command.get("action")
        with self.lock:
            if action == "play":
                if not self.world["agents"]:
                    raise ValueError("Nobody is alive. Start a new world.")
                self.paused = False
                return "Running"
            if action == "pause":
                self.paused = True
                return "Paused"
            if action == "step":
                self.paused = True
                if self.world["agents"]:
                    self._tick()
                return "Stepped to tick %d" % self.world["tick"]
            if action == "speed":
                if command.get("value") not in ALLOWED_SPEEDS:
                    raise ValueError("Unknown speed.")
                self.speed = command["value"]
                return "Speed %dx" % self.speed
            if action == "new":
                seed = str(command.get("seed", "")).strip()[:40] or "1"
                self._use_world(create_world(seed))
                return "New world from seed %s" % seed
            if action == "save":
                path = self._save_path(command.get("name"))
                save_world(self.world, path)
                return "Saved as %s (tick %d)" % (command["name"], self.world["tick"])
            if action == "load":
                path = self._save_path(command.get("name"))
                if not os.path.exists(path):
                    raise ValueError("No save called %s." % command["name"])
                self._use_world(load_world(path))
                self.paused = True   # paused so you can look before it moves on
                return "Loaded %s: tick %d, seed %s (paused)" % (
                    command["name"], self.world["tick"], self.world["seed"])
        raise ValueError("Unknown action.")

    @staticmethod
    def _save_path(name):
        if not isinstance(name, str) or not SAVE_NAME.match(name):
            raise ValueError("Save names can use letters, numbers, - and _ "
                             "(up to 40 characters).")
        return os.path.join(SAVES_DIR, name + ".json")

    @staticmethod
    def list_saves():
        if not os.path.isdir(SAVES_DIR):
            return []
        found = []
        for filename in os.listdir(SAVES_DIR):
            name, ext = os.path.splitext(filename)
            if ext == ".json" and SAVE_NAME.match(name):
                found.append((os.path.getmtime(os.path.join(SAVES_DIR, filename)), name))
        return [name for _, name in sorted(found, reverse=True)]   # newest first


class Handler(BaseHTTPRequestHandler):
    game = None   # set in main()

    def log_message(self, *args):
        pass   # the page asks for updates 10 times a second; don't print each

    def _send(self, code, body, content_type):
        data = body.encode("utf-8") if isinstance(body, str) else body
        try:
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass   # the browser tab went away mid-reply; nothing to do

    def _json(self, payload, code=200):
        self._send(code, json.dumps(payload), "application/json")

    def _is_local(self):
        """Only answer requests that really come from a page on this computer."""
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0]
        if host not in ("127.0.0.1", "localhost"):
            return False
        origin = self.headers.get("Origin")
        if origin and urlparse(origin).hostname not in ("127.0.0.1", "localhost"):
            return False
        return True

    def do_GET(self):
        if not self._is_local():
            return self._json({"ok": False, "error": "Local use only."}, 403)
        url = urlparse(self.path)
        if url.path in STATIC_FILES:
            filename, content_type = STATIC_FILES[url.path]
            with open(os.path.join(WEB_DIR, filename), "rb") as f:
                return self._send(200, f.read(), content_type)
        if url.path == "/api/state":
            query = parse_qs(url.query)
            try:
                since = int(query.get("since", ["0"])[0])
                agent_id = int(query["agent"][0]) if "agent" in query else None
            except ValueError:
                return self._json({"ok": False, "error": "Bad number."}, 400)
            feed = query.get("feed", ["notable"])[0]
            return self._send(200, self.game.snapshot(since, feed, agent_id),
                              "application/json")
        if url.path == "/api/saves":
            return self._json({"saves": Game.list_saves()})
        self._json({"ok": False, "error": "Not found."}, 404)

    def do_POST(self):
        if not self._is_local():
            return self._json({"ok": False, "error": "Local use only."}, 403)
        if urlparse(self.path).path != "/api/control":
            return self._json({"ok": False, "error": "Not found."}, 404)
        try:
            length = int(self.headers.get("Content-Length") or 0)
            if length > 10000:
                raise ValueError("Request too large.")
            command = json.loads(self.rfile.read(length) or b"{}")
            if not isinstance(command, dict):
                raise ValueError("Bad request.")
            message = self.game.control(command)
        except (ValueError, OSError) as error:
            return self._json({"ok": False, "error": str(error)}, 400)
        self._json({"ok": True, "message": message})


def main():
    parser = argparse.ArgumentParser(description="Project Genesis map view.")
    parser.add_argument("--seed", default="1", help="any number or word")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true",
                        help="don't open the browser automatically")
    args = parser.parse_args()

    Handler.game = Game(args.seed)
    try:
        server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    except OSError as error:
        if error.errno == errno.EADDRINUSE:
            print("Port %d is already in use (is Genesis already running in "
                  "another window?). Try:  python3 server.py --port %d"
                  % (args.port, args.port + 1))
        else:
            print("Could not start the server on port %d: %s" % (args.port, error))
        return 1
    threading.Thread(target=Handler.game.loop, daemon=True).start()

    address = "http://127.0.0.1:%d" % args.port
    print("Project Genesis is running at", address)
    print("Press Ctrl+C in this window to stop it.")
    if not args.no_browser:
        webbrowser.open(address)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
