// The station map: a street map served from this site, the stations on top, the 24-hour
// time-lapse and the tap panel. All station data comes from the JSON block in the page.
import * as maplibregl from "./vendor/maplibre-gl.mjs";

const data = JSON.parse(document.getElementById("site-data").textContent);
const css = getComputedStyle(document.documentElement);
const color = (name) => css.getPropertyValue(name).trim();
const COLORS = {
  o: color("--ok"), e: color("--empty"), f: color("--full"),
  x: color("--off"), u: color("--off"), r: color("--retired"),
};
const WORDS = { o: "OK", e: "Empty", f: "Full", x: "Offline", u: "No data", r: "Retired" };
const madrid = new Intl.DateTimeFormat("en-GB", {
  timeZone: "Europe/Madrid", weekday: "short", hour: "2-digit", minute: "2-digit",
});
// The area the map file covers. Panning further would only show empty tiles.
const COVERED = [[2.04, 41.31], [2.27, 41.49]];

if (data.windows && data.windows.length) start();

async function start() {
  const stations = data.stations;
  const last = data.windows.length - 1;
  let frame = last;
  let selected = null;
  let timer = null;

  // pmtiles.js (loaded before this module) reads the one map file in small pieces, with
  // HTTP range requests, instead of thousands of separate tile files.
  const protocol = new pmtiles.Protocol();
  maplibregl.addProtocol("pmtiles", protocol.tile);

  // The style stores paths relative to the site; MapLibre needs full URLs.
  const site = new URL(".", location.href).href;
  const style = await (await fetch(site + "map/style.json")).json();
  style.glyphs = site + style.glyphs;
  style.sprite = site + style.sprite;
  style.sources.protomaps.url = "pmtiles://" + site + style.sources.protomaps.url.slice("pmtiles://".length);

  // The stations are part of the style from the start, coloured by the latest window, so
  // they appear with the first streets instead of after every tile has arrived.
  style.sources.stations = {
    type: "geojson",
    data: {
      type: "FeatureCollection",
      features: stations.map((s, i) => ({
        type: "Feature", id: i, properties: { s: data.states[i][last] },
        geometry: { type: "Point", coordinates: [s.lon, s.lat] },
      })),
    },
  };
  style.layers.push({
    id: "stations",
    type: "circle",
    source: "stations",
    paint: {
      // A frame of the time-lapse sets each station's "feature state": 540 small values
      // change, the layer is not rebuilt. Before the first frame, the latest state is used.
      "circle-color": ["match", ["coalesce", ["feature-state", "s"], ["get", "s"]],
        "o", COLORS.o, "e", COLORS.e, "f", COLORS.f, "r", COLORS.r, COLORS.x],
      "circle-radius": ["interpolate", ["linear"], ["zoom"], 11, 2.5, 13, 4.5, 16, 9],
      "circle-stroke-color": ["case", ["boolean", ["feature-state", "selected"], false], color("--text"), color("--bg")],
      "circle-stroke-width": ["case", ["boolean", ["feature-state", "selected"], false], 2, 0.75],
    },
  });

  const map = new maplibregl.Map({
    container: "map",
    style,
    bounds: bounds(stations),
    fitBoundsOptions: { padding: 16 },
    maxBounds: [[COVERED[0][0] - 0.05, COVERED[0][1] - 0.04], [COVERED[1][0] + 0.05, COVERED[1][1] + 0.04]],
    minZoom: 10,
    maxZoom: 17,  // the file has detail to zoom 14; beyond that MapLibre enlarges it
    // One finger scrolls the page, two move the map: the map must not trap a phone user.
    cooperativeGestures: true,
    attributionControl: false,
    dragRotate: false,
    pitchWithRotate: false,
  });
  // Always open, never folded into an (i) button: the OpenStreetMap credit must be visible.
  map.addControl(new maplibregl.AttributionControl({ compact: false }), "bottom-right");
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
  map.touchZoomRotate.disableRotation();
  // Feature state can be set once the style (not every tile) is ready.
  if (!map.isStyleLoaded()) await new Promise((resolve) => map.once("style.load", resolve));

  const scrub = document.getElementById("scrub");
  const playBtn = document.getElementById("play");
  scrub.max = String(last);

  function showFrame(i) {
    frame = i;
    scrub.value = String(i);
    const counts = { o: 0, e: 0, f: 0, x: 0 };
    data.states.forEach((row, s) => {
      map.setFeatureState({ source: "stations", id: s }, { s: row[i] });
      const c = row[i] === "u" ? "x" : row[i];
      if (c in counts) counts[c] += 1;
    });
    document.getElementById("frame-time").textContent = madrid.format(new Date(data.windows[i]));
    document.querySelectorAll("[data-count]").forEach((el) => { el.textContent = counts[el.dataset.count]; });
    if (selected !== null) showStation(selected);
  }

  function stop() {
    clearInterval(timer);
    timer = null;
    playBtn.textContent = "Play";
  }
  playBtn.addEventListener("click", () => {
    if (timer) return stop();
    if (frame === last) showFrame(0);
    playBtn.textContent = "Pause";
    timer = setInterval(() => (frame >= last ? stop() : showFrame(frame + 1)), 250);
  });
  scrub.addEventListener("input", () => { stop(); showFrame(Number(scrub.value)); });

  // A dot is a few pixels wide: a finger needs more room. Look in a box around the tap and
  // take the nearest station.
  map.on("click", (event) => {
    const { x, y } = event.point;
    const near = map.queryRenderedFeatures([[x - 16, y - 16], [x + 16, y + 16]], { layers: ["stations"] });
    if (!near.length) return;
    const distance = (f) => {
      const p = map.project(f.geometry.coordinates);
      return (p.x - x) ** 2 + (p.y - y) ** 2;
    };
    near.sort((a, b) => distance(a) - distance(b));
    select(near[0].id);
  });
  map.on("mousemove", (event) => {
    const hit = map.queryRenderedFeatures(event.point, { layers: ["stations"] });
    map.getCanvas().style.cursor = hit.length ? "pointer" : "";
  });

  function select(i) {
    if (selected !== null) map.setFeatureState({ source: "stations", id: selected }, { selected: false });
    map.setFeatureState({ source: "stations", id: i }, { selected: true });
    showStation(i);
  }

  function showStation(i) {
    selected = i;
    const s = stations[i];
    const state = data.states[i][frame];
    const bikes = data.bikes[i];
    const known = bikes.filter((b) => b !== null);
    document.getElementById("panel").innerHTML =
      "<h3>" + text(s.name || "Station " + s.id) + "</h3>" +
      '<p class="sub">Station <span class="num">' + text(s.id) + "</span> · " + WORDS[state] +
      (bikes[frame] === null ? "" : ' · <span class="num">' + bikes[frame] + "</span> bikes") +
      (s.capacity ? ' of <span class="num">' + s.capacity + "</span> docks" : "") + "</p>" +
      sparkline(bikes, s.capacity) +
      '<div class="spark-axis"><span class="num">' + madrid.format(new Date(data.windows[0])) +
      '</span><span>bikes, min <span class="num">' + Math.min(...known) + "</span> max <span class=\"num\">" +
      Math.max(...known) + '</span></span><span class="num">' + madrid.format(new Date(data.windows[last])) + "</span></div>";
  }

  function sparkline(bikes, capacity) {
    const top = Math.max(capacity || 0, ...bikes.filter((b) => b !== null), 1);
    const w = bikes.length - 1 || 1;
    const y = (b) => (30 - (b / top) * 28 - 1).toFixed(1);
    // A gap in the data is a gap in the line, not an invented straight segment.
    let path = "";
    let pen = false;
    bikes.forEach((b, i) => {
      if (b === null) { pen = false; return; }
      path += (pen ? "L" : "M") + ((i / w) * 100).toFixed(2) + " " + y(b);
      pen = true;
    });
    const now = bikes[frame];
    const marker = now === null ? "" :
      '<circle cx="' + ((frame / w) * 100).toFixed(2) + '" cy="' + y(now) + '" r="1.6" fill="' + color("--text") + '"/>';
    return '<svg class="spark" viewBox="0 0 100 30" preserveAspectRatio="none" aria-hidden="true">' +
      '<path d="' + path + '" fill="none" stroke="' + color("--muted") + '" stroke-width="0.8" vector-effect="non-scaling-stroke"/>' +
      marker + "</svg>";
  }

  showFrame(last);
}

function bounds(stations) {
  const lons = stations.map((s) => s.lon);
  const lats = stations.map((s) => s.lat);
  return [[Math.min(...lons), Math.min(...lats)], [Math.max(...lons), Math.max(...lats)]];
}

function text(value) {
  const span = document.createElement("span");
  span.textContent = value;  // never innerHTML with data: a name is text, not markup
  return span.innerHTML;
}
