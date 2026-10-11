// Render every SVG in a folder to a 1920x1080 PNG with Playwright's Chromium.
//   node render_svg.mjs svg_dir png_dir
// In the Higgsfield sandbox, import from '/usr/local/lib/node_modules/playwright/index.mjs'
// and set PLAYWRIGHT_BROWSERS_PATH=/ms-playwright.
import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const [src, dst] = process.argv.slice(2);
fs.mkdirSync(dst, { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
for (const f of fs.readdirSync(src).filter(f => f.endsWith('.svg')).sort()) {
  await page.setContent(`<html><body style="margin:0">${fs.readFileSync(path.join(src, f), 'utf8')}</body></html>`);
  await page.screenshot({ path: path.join(dst, f.replace('.svg', '.png')) });
}
await browser.close();
