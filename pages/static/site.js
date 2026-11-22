// The status page's behaviour: its own freshness check, the time-lapse map, and the
// station panel. All data comes from the JSON block the build wrote into the page.
(function () {
  "use strict";
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

  // ---------- 1. freshness, judged in the browser ----------
  // Nobody rebuilds a static page when the builder stops. So the page checks its own age
  // against the visitor's clock and turns itself red when the data is too old.
  function ago(ms) {
    const minutes = Math.round(ms / 60000);
    if (minutes < 1) return "just now";
    if (minutes < 60) return minutes + " min ago";
    const hours = Math.floor(minutes / 60);
    return hours < 48 ? hours + " h " + (minutes % 60) + " min ago" : Math.floor(hours / 24) + " days ago";
  }
  function checkAge() {
    if (!data.last_fetch_utc) return;
    const age = Date.now() - new Date(data.last_fetch_utc).getTime();
    const ageEl = document.getElementById("age");
    if (ageEl) ageEl.textContent = ago(age);
    if (age > data.fresh_for_ms) {
      document.querySelector(".status").dataset.level = "down";
      document.getElementById("status-label").textContent = "Not updating";
      document.getElementById("status-note").textContent =
        "No new data for " + ago(age).replace(" ago", "") + ". The collector may have stopped; what you see is the last known state.";
    }
  }
  checkAge();
  setInterval(checkAge, 60000);

  // ---------- 2. patterns: weekday x hour heatmap ----------
  const heat = data.heatmap;
  if (heat && window.Plotly) {
    const hours = Array.from({ length: 24 }, (_, h) => h);
    Plotly.newPlot(
      "heatmap",
      [{
        type: "heatmap", z: heat.z, x: hours, y: heat.weekdays,
        // Dark = few empty, red = many: the same red as "empty" on the map.
        colorscale: [[0, color("--surface")], [1, color("--empty")]],
        zmin: 0, zmax: heat.max, showscale: false, xgap: 1, ygap: 1, hoverinfo: "none",
      }],
      {
        paper_bgcolor: color("--bg"), plot_bgcolor: color("--bg"),
        margin: { l: 36, r: 4, t: 4, b: 28 },
        font: { family: css.getPropertyValue("--mono"), color: color("--muted"), size: 13 },
        xaxis: { tickvals: [0, 6, 12, 18, 23], ticktext: ["00", "06", "12", "18", "23h"], fixedrange: true },
        yaxis: { autorange: "reversed", fixedrange: true },  // Monday on top, like a calendar
        // The peak is written on the chart, not hidden in a hover.
        annotations: [{
          x: heat.peak.hour, y: heat.weekdays[heat.peak.weekday], text: heat.peak.value + "%",
          showarrow: true, arrowcolor: color("--text"), ax: 0, ay: -22,
          font: { color: color("--text"), size: 13 }, bgcolor: color("--bg"),
        }],
      },
      { responsive: true, displayModeBar: false, staticPlot: true }
    );
  }

  // ---------- 3. the time-lapse map ----------
  if (!data.windows || !data.windows.length || !window.Plotly) return;
  const stations = data.stations;
  const last = data.windows.length - 1;
  let frame = last;
  let selected = null;
  let timer = null;

  const lat0 = stations.reduce((sum, s) => sum + s.lat, 0) / stations.length;
  const colorsAt = (i) => data.states.map((row) => COLORS[row[i]]);

  const mapEl = document.getElementById("map");
  Plotly.newPlot(
    mapEl,
    [{
      type: "scatter", mode: "markers",
      x: stations.map((s) => s.lon), y: stations.map((s) => s.lat),
      marker: { color: colorsAt(frame), size: 8, line: { width: 0 } },
      hoverinfo: "none",  // touch has no hover: everything is in the tap panel instead
    }],
    {
      paper_bgcolor: color("--bg"), plot_bgcolor: color("--bg"),
      margin: { l: 4, r: 4, t: 4, b: 4 }, showlegend: false, dragmode: "pan",
      xaxis: { visible: false },
      // A degree of longitude is shorter than a degree of latitude away from the equator
      // (0.75 at Barcelona). Without this the city would be stretched sideways.
      yaxis: { visible: false, scaleanchor: "x", scaleratio: 1 / Math.cos((lat0 * Math.PI) / 180) },
    },
    { responsive: true, displayModeBar: false, scrollZoom: false }
  );

  const scrub = document.getElementById("scrub");
  const playBtn = document.getElementById("play");
  scrub.max = String(last);

  function showFrame(i) {
    frame = i;
    scrub.value = String(i);
    Plotly.restyle(mapEl, { "marker.color": [colorsAt(i)] }, [0]);
    document.getElementById("frame-time").textContent = madrid.format(new Date(data.windows[i]));
    const counts = { o: 0, e: 0, f: 0, x: 0 };
    data.states.forEach((row) => {
      const c = row[i] === "u" ? "x" : row[i];
      if (c in counts) counts[c] += 1;
    });
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

  // ---------- 4. tap a station: its last 24 hours ----------
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

  function text(value) {
    const span = document.createElement("span");
    span.textContent = value;  // never innerHTML with data: a name is text, not markup
    return span.innerHTML;
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
  mapEl.on("plotly_click", (event) => showStation(event.points[0].pointIndex));

  showFrame(last);
})();
