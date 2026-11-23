// The status page's own freshness check and the patterns heatmap. The map lives in map.js.
// All data comes from the JSON block the build wrote into the page.
(function () {
  "use strict";
  const data = JSON.parse(document.getElementById("site-data").textContent);
  const css = getComputedStyle(document.documentElement);
  const color = (name) => css.getPropertyValue(name).trim();

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
  if (heat && heat.ready && window.Plotly) {
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

})();
