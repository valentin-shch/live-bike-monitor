// Writes pages/static/map/style.json: the Protomaps "black" flavour (made for data drawn on
// top), with land and sea moved onto this site's palette. Run once, after changing it:
//
//   npm pack @protomaps/basemaps@5.7.2 && tar -xzf protomaps-basemaps-5.7.2.tgz
//   node build/make_style.mjs package/dist/esm/index.js
//
// The style keeps relative paths; map.js turns them into full URLs on our own site, so the
// visitor's browser never asks anyone but us for map data, fonts or icons.
import { writeFileSync } from "node:fs";
import { pathToFileURL } from "node:url";

const [basemapsPath] = process.argv.slice(2);
const { layers, namedFlavor } = await import(pathToFileURL(basemapsPath).href);

const flavor = {
  ...namedFlavor("black"),
  // Same near-black as the page, so the map sits in it instead of in a grey box.
  background: "#0a0c0f",
  earth: "#0e1216",
  // A little blue in the sea, so the coastline reads without a drawn border.
  water: "#121a23",
  buildings: "#0b0e12",
  // Town names stay readable but step back: the stations are the subject, not the labels.
  city_label: "#4a525b",
  city_label_halo: "#0a0c0f",
};

const style = {
  version: 8,
  glyphs: "map/fonts/{fontstack}/{range}.pbf",
  sprite: "map/sprites/black",
  sources: {
    protomaps: {
      type: "vector",
      url: "pmtiles://map/barcelona.pmtiles",
      attribution:
        '<a href="https://www.openstreetmap.org/copyright">© OpenStreetMap</a> contributors (ODbL) · ' +
        '<a href="https://protomaps.com">Protomaps</a>',
    },
  },
  layers: layers("protomaps", flavor, { lang: "en" }),
};

const out = new URL("../pages/static/map/style.json", import.meta.url);
writeFileSync(out, JSON.stringify(style));
console.log(`wrote ${out.pathname} (${style.layers.length} layers)`);
