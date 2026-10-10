/*
  Artwork. Generated images (Higgsfield, see assets/ARTWORK.md) are embedded as
  data URIs in web/art-data.js by tools/embed_art.py, because Qollab serves
  modules reliably but not loose image files. When an image is missing, the
  hand-drawn SVG emblems below are used instead, so the game never depends on it.
*/

import { ART_DATA } from "./art-data.js";

export const LEVEL_ALT = {
  "invisible-ink": "Illustration: a qubit splits into a blue and an orange path; a faint painted phase on the orange path only shows up as ripples where the paths meet again.",
  "dark-port": "Illustration: an interferometer with a violet mystery crystal on one path; one output detector glows, the other is completely dark.",
  "eraser": "Illustration: a small eye-shaped detector watches two light paths while an eraser wipes away its line of sight and interference ripples return.",
  "kickback": "Illustration: an interferometer whose lower path is linked by a controlled gate to a second, straight target wire; a curved arrow shows the phase kicking back from the target onto the interferometer.",
  "amplifier": "Illustration: four bars for four doors; three short bars and one tall cyan bar for the marked door, with a dashed line showing the average.",
};

const CYAN = "#5ce1e6";

const BLUE = "#4ea8ff";
const AMBER = "#ffb000";
const VIOLET = "#c4a3ff";
const WHITE = "#e8ecf8";

function diamond(extra) {
  return `
  <rect width="120" height="120" rx="18" fill="#141b34"/>
  <circle cx="22" cy="60" r="7" fill="${WHITE}"/>
  <circle cx="98" cy="60" r="7" fill="${WHITE}"/>
  <path d="M22 60 L60 26 L98 60" fill="none" stroke="${BLUE}" stroke-width="5" stroke-linejoin="round"/>
  <path d="M22 60 L60 94 L98 60" fill="none" stroke="${AMBER}" stroke-width="5" stroke-dasharray="9 6" stroke-linejoin="round"/>
  ${extra}`;
}

const EMBLEMS = {
  "invisible-ink": diamond(`
  <path d="M48 98 q6 -10 12 0 t12 0" fill="none" stroke="${WHITE}" stroke-opacity="0.45" stroke-width="3"/>
  <circle cx="98" cy="60" r="14" fill="none" stroke="${WHITE}" stroke-opacity="0.5" stroke-width="2"/>
  <circle cx="98" cy="60" r="21" fill="none" stroke="${WHITE}" stroke-opacity="0.25" stroke-width="2"/>`),
  "dark-port": diamond(`
  <polygon points="60,84 68,94 60,104 52,94" fill="${VIOLET}"/>
  <circle cx="108" cy="40" r="8" fill="${WHITE}"/>
  <circle cx="108" cy="80" r="8" fill="#0b1020" stroke="${WHITE}" stroke-width="2"/>`),
  "eraser": diamond(`
  <ellipse cx="60" cy="60" rx="13" ry="8" fill="none" stroke="${WHITE}" stroke-width="3"/>
  <circle cx="60" cy="60" r="3.5" fill="${WHITE}"/>
  <rect x="70" y="68" width="22" height="12" rx="3" fill="${VIOLET}" transform="rotate(-30 81 74)"/>`),
  "kickback": `
  <rect width="120" height="120" rx="18" fill="#141b34"/>
  <circle cx="20" cy="46" r="6" fill="${WHITE}"/>
  <circle cx="100" cy="46" r="6" fill="${WHITE}"/>
  <path d="M20 46 L60 18 L100 46" fill="none" stroke="${BLUE}" stroke-width="5" stroke-linejoin="round"/>
  <path d="M20 46 L60 74 L100 46" fill="none" stroke="${AMBER}" stroke-width="5" stroke-dasharray="9 6" stroke-linejoin="round"/>
  <path d="M14 100 H106" stroke="${WHITE}" stroke-width="4" stroke-linecap="round"/>
  <path d="M60 74 V100" stroke="${CYAN}" stroke-width="4"/>
  <circle cx="60" cy="74" r="6" fill="${CYAN}"/>
  <circle cx="60" cy="100" r="6" fill="${CYAN}"/>
  <path d="M78 98 C 92 92, 92 78, 80 70" fill="none" stroke="${CYAN}" stroke-width="3" stroke-linecap="round"/>
  <path d="M80 70 l9 1 l-6 7 z" fill="${CYAN}"/>`,
  "amplifier": `
  <rect width="120" height="120" rx="18" fill="#141b34"/>
  <path d="M14 100 H106" stroke="${WHITE}" stroke-opacity="0.5" stroke-width="2"/>
  <rect x="20" y="82" width="16" height="18" rx="3" fill="${BLUE}"/>
  <rect x="42" y="82" width="16" height="18" rx="3" fill="${BLUE}"/>
  <rect x="64" y="82" width="16" height="18" rx="3" fill="${BLUE}"/>
  <rect x="86" y="22" width="16" height="78" rx="3" fill="${CYAN}"/>
  <path d="M14 76 H106" stroke="${AMBER}" stroke-width="3" stroke-dasharray="7 5"/>
  <path d="M94 12 l4 -6 l4 6" fill="none" stroke="${WHITE}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>`,
};

/** An <img> (generated art) or an inline SVG emblem, with a text alternative.
 *  decorative: true when the surrounding control already names the level
 *  (the level list), so screen readers do not hear the illustration twice. */
export function levelArt(levelId, { decorative = false, size = 96 } = {}) {
  const src = ART_DATA.levels?.[levelId];
  const alt = decorative ? "" : LEVEL_ALT[levelId] ?? "";
  if (src) {
    const img = document.createElement("img");
    img.src = src;
    img.alt = alt;
    img.width = size;
    img.height = size;
    img.decoding = "async";
    return img;
  }
  const wrap = document.createElement("span");
  const a11y = decorative ? 'aria-hidden="true" focusable="false"' : `role="img" aria-label="${alt.replace(/"/g, "&quot;")}"`;
  wrap.innerHTML = `<svg viewBox="0 0 120 120" width="${size}" height="${size}" ${a11y}>${EMBLEMS[levelId] ?? diamond("")}</svg>`;
  return wrap.firstElementChild;
}
