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
};

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
};

/** An <img> (generated art) or an inline SVG emblem, with a text alternative. */
export function levelArt(levelId) {
  const src = ART_DATA.levels?.[levelId];
  const alt = LEVEL_ALT[levelId] ?? "";
  if (src) {
    const img = document.createElement("img");
    img.src = src;
    img.alt = alt;
    img.width = 96;
    img.height = 96;
    img.decoding = "async";
    return img;
  }
  const wrap = document.createElement("span");
  wrap.innerHTML = `<svg viewBox="0 0 120 120" width="96" height="96" role="img" aria-label="${alt.replace(/"/g, "&quot;")}">${EMBLEMS[levelId] ?? diamond("")}</svg>`;
  return wrap.firstElementChild;
}

const HERO_FALLBACK = `url("data:image/svg+xml,${encodeURIComponent(`
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 300' preserveAspectRatio='xMaxYMid slice'>
  <rect width='1200' height='300' fill='#0b1020'/>
  <g fill='none' stroke-width='5' stroke-linecap='round'>
    <path d='M560 150 C 700 30, 860 30, 1000 150' stroke='${BLUE}'/>
    <path d='M560 150 C 700 270, 860 270, 1000 150' stroke='${AMBER}' stroke-dasharray='16 10'/>
    <path d='M380 150 L560 150' stroke='${WHITE}'/>
  </g>
  <g fill='none' stroke='${WHITE}' stroke-opacity='0.35' stroke-width='3'>
    <circle cx='1000' cy='150' r='30'/><circle cx='1000' cy='150' r='60'/>
    <circle cx='1000' cy='150' r='95' stroke-opacity='0.2'/><circle cx='1000' cy='150' r='135' stroke-opacity='0.1'/>
  </g>
  <rect x='545' y='135' width='30' height='30' fill='#5ce1e6' transform='rotate(45 560 150)'/>
  <rect x='985' y='135' width='30' height='30' fill='#5ce1e6' transform='rotate(45 1000 150)'/>
</svg>`)}")`;

/** Decorative header background (the element is aria-hidden). */
export function applyHero(node) {
  node.style.backgroundImage = ART_DATA.hero ? `url("${ART_DATA.hero}")` : HERO_FALLBACK;
}
