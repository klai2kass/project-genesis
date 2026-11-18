// The map view. This file only DRAWS what the Python server tells it and
// sends button presses back. No simulation rules live here.

const TILE = 14;                 // size of one map tile in pixels
const $ = (id) => document.getElementById(id);

const map = $("map");
const mapCtx = map.getContext("2d");
const chart = $("chart");
const chartCtx = chart.getContext("2d");

let state = null;        // the latest snapshot from the server
let worldId = null;      // changes when a new world starts or a save is loaded
let lastSeq = 0;         // newest event we have already shown
let feedMode = "notable";
let selectedId = null;
const TERRAIN_COLORS = ["#1f4a66", "#5a8f47", "#2f6b3e"];   // water, grass, forest
const FOOD_COLOR = "#d6ec6a";

// ---------- talking to the server ----------

async function poll() {
  try {
    const askedMode = feedMode;
    const params = new URLSearchParams({ since: lastSeq, feed: askedMode });
    if (selectedId !== null) params.set("agent", selectedId);
    const reply = await fetch("/api/state?" + params);
    const next = await reply.json();
    if (next.world_id !== worldId) {      // a different world: start fresh
      worldId = next.world_id;
      selectedId = null;
      next.selected = null;
      $("feed").replaceChildren();
      $("seed-input").value = next.seed;
      setupMap(next);
    }
    // If the feed switch was flipped while we waited, this reply is stale.
    if (askedMode === feedMode) lastSeq = next.last_seq;
    else next.events = [];
    state = next;
    render();
  } catch (error) {
    setRunState("offline", "Server stopped");
  }
  setTimeout(poll, 100);
}

async function send(command) {
  try {
    const reply = await fetch("/api/control", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(command),
    });
    const result = await reply.json();
    showMessage(result.ok ? result.message : result.error, !result.ok);
    if (command.action === "load") {
      showToast(result.ok ? result.message : "Could not load: " + result.error,
                !result.ok);
    }
    return result.ok;
  } catch (error) {
    showMessage("Could not reach the server. Is server.py still running?", true);
    if (command.action === "load") {
      showToast("Could not load: the server did not answer.", true);
    }
    return false;
  }
}

async function refreshSaves() {
  try {
    const reply = await fetch("/api/saves");
    const names = (await reply.json()).saves;
    const select = $("load-name");
    const options = names.map((name) => new Option(name, name));
    if (!names.length) options.push(new Option("(no saves yet)", ""));
    select.replaceChildren(...options);
  } catch (error) { /* the poll loop already reports a stopped server */ }
}

// ---------- drawing ----------

function mix(a, b, t) {
  const c = a.map((v, i) => Math.round(v + (b[i] - v) * t));
  return `rgb(${c[0]},${c[1]},${c[2]})`;
}

function setupMap(s) {
  const dpr = window.devicePixelRatio || 1;
  map.width = s.width * TILE * dpr;
  map.height = s.height * TILE * dpr;
  mapCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
}

function drawMap() {
  const s = state;
  for (let y = 0; y < s.height; y++) {
    for (let x = 0; x < s.width; x++) {
      const i = y * s.width + x;
      mapCtx.fillStyle = TERRAIN_COLORS[+s.terrain[i]];
      mapCtx.fillRect(x * TILE, y * TILE, TILE, TILE);
      const food = s.food[i];
      if (food > 0) {                 // food is a bright dot; more food = bigger
        const size = Math.min(10, 2 + food);
        mapCtx.fillStyle = FOOD_COLOR;
        mapCtx.fillRect(x * TILE + (TILE - size) / 2, y * TILE + (TILE - size) / 2, size, size);
      }
    }
  }
  const starving = [229, 86, 75], fed = [255, 243, 209];
  for (const [id, x, y, energy, resting] of s.agents) {
    const cx = x * TILE + TILE / 2, cy = y * TILE + TILE / 2;
    mapCtx.beginPath();
    mapCtx.arc(cx, cy, 4.2, 0, Math.PI * 2);
    mapCtx.fillStyle = mix(starving, fed, Math.min(1, energy / 60));
    mapCtx.fill();
    mapCtx.lineWidth = 1.5;
    // A resting agent gets a violet ring instead of the dark outline.
    mapCtx.strokeStyle = resting ? "#8a7ce0" : "#101114";
    mapCtx.stroke();
    if (id === selectedId) {
      mapCtx.beginPath();
      mapCtx.arc(cx, cy, 8.5, 0, Math.PI * 2);
      mapCtx.lineWidth = 2;
      mapCtx.strokeStyle = "#e8b04a";
      mapCtx.stroke();
    }
  }
  drawHome();
}

// The selected agent's home: a gold square, and a dashed box for the area it
// stays inside while wandering (home_radius steps; none if homes are off).
function drawHome() {
  const sel = state.selected;
  if (!sel || !sel.alive || !sel.agent.home) return;
  const [hx, hy] = sel.agent.home;
  const r = (sel.effects || {}).home_radius || 0;
  mapCtx.lineWidth = 1.5;
  mapCtx.strokeStyle = "#e8b04a";
  if (r > 0) {
    mapCtx.setLineDash([4, 4]);
    mapCtx.strokeRect((hx - r) * TILE, (hy - r) * TILE, (2 * r + 1) * TILE, (2 * r + 1) * TILE);
    mapCtx.setLineDash([]);
  }
  mapCtx.fillStyle = "#e8b04a";
  mapCtx.fillRect(hx * TILE + 3, hy * TILE + 3, TILE - 6, TILE - 6);
  mapCtx.strokeStyle = "#101114";
  mapCtx.strokeRect(hx * TILE + 3, hy * TILE + 3, TILE - 6, TILE - 6);
}

function drawChart() {
  const dpr = window.devicePixelRatio || 1;
  const w = chart.clientWidth, h = 70;
  if (chart.width !== w * dpr) { chart.width = w * dpr; chart.height = h * dpr; }
  chartCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
  chartCtx.clearRect(0, 0, w, h);

  const points = state.history;
  const top = Math.max(80, ...points) * 1.1;
  const px = (i) => (points.length > 1 ? (i / (points.length - 1)) * (w - 34) : 0);
  const py = (v) => h - 4 - (v / top) * (h - 10);

  chartCtx.beginPath();
  points.forEach((v, i) => (i ? chartCtx.lineTo(px(i), py(v)) : chartCtx.moveTo(px(i), py(v))));
  chartCtx.strokeStyle = "#e8b04a";
  chartCtx.lineWidth = 1.75;
  chartCtx.lineJoin = "round";
  chartCtx.stroke();

  const last = points[points.length - 1];
  chartCtx.fillStyle = "#e8e4da";
  chartCtx.font = "600 12px system-ui, sans-serif";
  chartCtx.textBaseline = "middle";
  chartCtx.fillText(String(last), px(points.length - 1) + 6, py(last));
}

// ---------- the side panels ----------

function setRunState(kind, text) {
  const label = $("run-state");
  label.className = "state " + kind;
  label.textContent = text;
}

// A short pop-up that fades away by itself (longer for errors). It never
// takes clicks, so the controls underneath keep working.
let toastTimers = [];
function showToast(text, isError) {
  const toast = $("toast");
  toastTimers.forEach(clearTimeout);
  toast.textContent = text;
  toast.classList.toggle("error", Boolean(isError));
  toast.hidden = false;
  requestAnimationFrame(() => toast.classList.add("show"));
  toastTimers = [
    setTimeout(() => toast.classList.remove("show"), isError ? 6000 : 3500),
    setTimeout(() => { toast.hidden = true; }, isError ? 6700 : 4200),
  ];
}

function showMessage(text, isError) {
  const box = $("message");
  box.textContent = text;
  box.classList.toggle("error", Boolean(isError));
}

function eventRow(event, withAgent) {
  const row = document.createElement("li");
  row.className = event.action;
  const tick = document.createElement("span");
  tick.className = "t";
  tick.textContent = "t" + event.tick;
  const what = document.createElement("b");
  what.textContent = (withAgent ? "#" + event.agent + " " : "") + event.action;
  row.append(tick, what, " — " + event.why);
  if (!withAgent && event.need) {       // in an agent's own trail, show its need too
    const need = document.createElement("span");
    need.className = "needed";
    need.textContent = "need: " + event.need;
    row.append(need);
  }
  row.dataset.agent = event.agent;
  return row;
}

// The options an agent weighed for one decision: chosen / could / no.
function optionRows(event) {
  return (event.options || []).map((option) => {
    const kind = option.action === event.action ? "chosen" : option.ok ? "could" : "no";
    const row = document.createElement("li");
    row.className = kind;
    const name = document.createElement("span");
    name.textContent = option.action;
    const verdict = document.createElement("span");
    verdict.className = "verdict";
    verdict.textContent = kind;
    const note = document.createElement("span");
    note.textContent = option.note;
    row.append(name, verdict, note);
    return row;
  });
}

// Who this agent has met most (encounter memory, genesis/memory.py).
function renderKnown(known) {
  const list = $("a-known-list");
  list.replaceChildren();
  if (!known || known.keep <= 0) {
    $("a-known").textContent = known ? "Remembers no meetings (memory is off in this world)." : "";
    return;
  }
  $("a-known").textContent = known.count === 0 ? "Has not met anyone yet." :
    "Knows " + known.count + " agent" + (known.count === 1 ? "" : "s") +
    " (remembers up to " + known.keep +
    (known.fade > 0 ? ", forgets anyone not met for " + known.fade + " ticks" : "") +
    "). Met most:";
  for (const k of known.top) {
    const li = document.createElement("li");
    const who = document.createElement("strong");
    who.textContent = "#" + k.id + (k.family ? " (" + k.family + ")" : "");
    li.append(who, document.createTextNode(
      " · met " + k.meetings + " time" + (k.meetings === 1 ? "" : "s") +
      ", last at tick " + k.last + " near (" + k.x + ", " + k.y + ")" +
      (k.gave ? " · I gave it " + k.gave + " food" : "") +
      (k.got ? " · it gave me " + k.got + " food" : "") +
      (k.alive ? "" : " · has died")));
    list.append(li);
  }
}

function renderAgent() {
  const sel = state.selected;
  $("agent-empty").hidden = Boolean(sel);
  $("agent-panel").hidden = !sel;
  if (!sel) return;

  if (sel.alive) {
    const a = sel.agent;
    $("a-name").textContent = "Agent #" + a.id;
    $("a-meta").textContent = "generation " + a.generation +
      (a.parent ? ", child of #" + a.parent : ", one of the first");
    $("a-bar").style.width = (100 * a.energy / state.max_energy) + "%";
    $("a-numbers").textContent = "Energy " + a.energy + "/" + state.max_energy +
      " · carrying " + a.food + "/" + state.carry_max + " food · age " + a.age +
      " of " + a.max_age + " · at (" + a.x + ", " + a.y + ")";
    $("a-action").textContent = a.last_action;
    $("a-why").textContent = a.last_why;
    const fx = sel.effects || {};
    const rest = a.needs ? a.needs.rest : 100;
    $("a-rest-bar").style.width = rest + "%";
    $("a-rest").textContent = "Rest " + rest + "/100" +
      (a.resting ? " · resting (until " + fx.rest_resume + ")"
                 : " · rests below " + fx.rest_below + " when not hungry");
    const t = a.traits || {};
    $("a-traits").textContent = "Curiosity " + t.curiosity + " (turns " + fx.turn_percent +
      "% of wandering ticks: high searches nearby, low walks straight) · industriousness " +
      t.industriousness + " (loses " + (fx.tire_rate / fx.tire_scale).toFixed(2) +
      " rest per move)";
    if (a.home) {
      const far = Math.max(Math.abs(a.x - a.home[0]), Math.abs(a.y - a.home[1]));
      const whose = a.parent === null ? "where it started"
        : (fx.home_inherit ? "its family's home, from #" + a.parent : "where it was born");
      $("a-home").textContent = "Home (" + a.home[0] + ", " + a.home[1] + "), " + whose + " · " +
        far + " tiles away · " + (fx.home_radius > 0
          ? "wanders within " + fx.home_radius + " tiles of it (gold square on the map)"
          : "homes are off in this world");
    } else {
      $("a-home").textContent = "";
    }
    renderKnown(sel.known);
  } else {
    const last = sel.trail[sel.trail.length - 1];
    $("a-name").textContent = "Agent #" + sel.id;
    $("a-meta").textContent = "has died";
    $("a-bar").style.width = "0%";
    $("a-numbers").textContent = "";
    $("a-rest-bar").style.width = "0%";
    $("a-rest").textContent = "";
    $("a-traits").textContent = "";
    $("a-home").textContent = "";
    renderKnown(null);
    $("a-action").textContent = "die";
    $("a-why").textContent = last ? last.why : "It is no longer in the world.";
  }
  // The newest decision is shown in full: need, options, reason.
  const newest = sel.trail[sel.trail.length - 1];
  const needLine = $("a-need");
  needLine.replaceChildren();
  if (newest && newest.need) {
    const label = document.createElement("b");
    label.textContent = "Need: ";
    needLine.append(label, newest.need);
  }
  $("a-options").replaceChildren(...(newest ? optionRows(newest) : []));

  const rows = sel.trail.slice(0, -1).reverse().map((event) => eventRow(event, false));
  $("a-trail").replaceChildren(...rows);
}

function renderFeed() {
  const feed = $("feed");
  for (const event of state.events) feed.prepend(eventRow(event, true));
  while (feed.children.length > 80) feed.lastChild.remove();
}

function render() {
  const s = state;
  $("seed-label").textContent = s.seed;
  $("tick-label").textContent = s.tick.toLocaleString();
  if (!s.stats.alive) setRunState("offline", "Everyone has died");
  else setRunState(s.paused ? "paused" : "running", s.paused ? "Paused" : "Running");
  $("play").textContent = s.paused ? "Play" : "Pause";

  $("s-alive").textContent = s.stats.alive;
  $("s-births").textContent = s.stats.births.toLocaleString();
  $("s-starved").textContent = s.stats.starved.toLocaleString();
  $("s-old").textContent = s.stats.old_age.toLocaleString();
  $("s-energy").textContent = s.stats.avg_energy;
  $("s-food").textContent = s.stats.food.toLocaleString();
  $("s-resting").textContent = s.stats.resting;
  $("s-gifts").textContent = (s.stats.gifts || 0).toLocaleString();
  $("s-generation").textContent = s.stats.generation;
  $("s-curiosity").textContent = s.stats.avg_curiosity;
  $("s-industrious").textContent = s.stats.avg_industriousness;

  for (const button of $("speeds").children) {
    button.classList.toggle("on", Number(button.dataset.speed) === s.speed);
  }
  for (const button of $("feed-mode").children) {
    button.classList.toggle("on", button.dataset.feed === feedMode);
  }

  drawMap();
  drawChart();
  renderAgent();
  renderFeed();
}

// ---------- buttons, clicks and keys ----------

function togglePlay() {
  if (state) send({ action: state.paused ? "play" : "pause" });
}

$("play").addEventListener("click", togglePlay);
$("step").addEventListener("click", () => send({ action: "step" }));

$("speeds").addEventListener("click", (event) => {
  const speed = Number(event.target.dataset.speed);
  if (speed) send({ action: "speed", value: speed });
});

$("feed-mode").addEventListener("click", (event) => {
  const mode = event.target.dataset.feed;
  if (!mode || mode === feedMode) return;
  feedMode = mode;
  lastSeq = 0;                       // ask the server for that feed's recent history
  $("feed").replaceChildren();
});

$("new-form").addEventListener("submit", (event) => {
  event.preventDefault();
  send({ action: "new", seed: $("seed-input").value });
});

$("save-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (await send({ action: "save", name: $("save-name").value.trim() })) refreshSaves();
});

$("load-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const name = $("load-name").value;
  if (name) send({ action: "load", name });
  else showMessage("There is nothing to load yet. Save first.", true);
});

// Click the map to pick the nearest agent (or click empty ground to deselect).
map.addEventListener("click", (event) => {
  if (!state) return;
  const box = map.getBoundingClientRect();
  const tx = ((event.clientX - box.left) / box.width) * state.width - 0.5;
  const ty = ((event.clientY - box.top) / box.height) * state.height - 0.5;
  let best = null, bestDistance = 1.5;
  for (const [id, x, y] of state.agents) {
    const distance = Math.hypot(x - tx, y - ty);
    if (distance < bestDistance) { best = id; bestDistance = distance; }
  }
  selectedId = best;
});

// Click a line in the feed to follow that agent.
$("feed").addEventListener("click", (event) => {
  const row = event.target.closest("li");
  if (row) selectedId = Number(row.dataset.agent);
});

// Space bar = play / pause (unless you are typing in a box).
document.addEventListener("keydown", (event) => {
  const typing = ["INPUT", "SELECT", "BUTTON", "TEXTAREA"].includes(event.target.tagName);
  if (event.code === "Space" && !typing) {
    event.preventDefault();
    togglePlay();
  }
});

refreshSaves();
poll();
