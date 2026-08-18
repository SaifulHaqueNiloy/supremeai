/**
 * generate-desktop-icons.mjs — SupremeAI Desktop packaging icons
 * ==============================================================
 * বাংলা: public/favicon.svg (ব্র্যান্ডড bolt logo) থেকে Electron tray ও installer
 * icons (PNG) generate করে। Pure-vector রাস্টারাইজেশনের জন্য local Playwright Chromium
 * ব্যবহার করা হয় (zero third-party image deps)।
 *
 * Usage (repo root থেকে):
 *   node frontend/scripts/generate-desktop-icons.mjs
 *
 * Output: frontend/media/icon-{32,64,256,512}.png (+ icon.png = 64px alias for tray)
 */
import { chromium } from '@playwright/test';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '..', '..');
const svgPath = path.join(repoRoot, 'frontend', 'public', 'favicon.svg');
const outDir = path.join(repoRoot, 'frontend', 'media');

const SIZES = [32, 64, 256, 512];
const SVG_ASPECT = 46 / 48; // height / width (viewBox 0 0 48 46)

async function main() {
  if (!fs.existsSync(svgPath)) {
    throw new Error(`favicon.svg not found: ${svgPath}`);
  }
  fs.mkdirSync(outDir, { recursive: true });

  const svg = fs.readFileSync(svgPath, 'utf8');
  const dataUrl = `data:image/svg+xml;base64,${Buffer.from(svg).toString('base64')}`;

  const browser = await chromium.launch();
  try {
    const page = await browser.newPage({ viewport: { width: 1024, height: 1024 } });
    for (const size of SIZES) {
      const h = Math.round(size * SVG_ASPECT);
      await page.setContent(`
        <body style="margin:0;background:transparent">
          <img id="ic" src="${dataUrl}" width="${size}" height="${h}" style="display:block"/>
        </body>
      `);
      const target = path.join(outDir, `icon-${size}.png`);
      await page.locator('#ic').screenshot({ path: target, omitBackground: true });
      console.log(`[icon] ${path.relative(repoRoot, target)} (${size}x${h})`);
    }

    // tray alias — icon.png = 64px (Windows/macOS tray HiDPI-safe)
    const alias = path.join(outDir, 'icon.png');
    fs.copyFileSync(path.join(outDir, 'icon-64.png'), alias);
    console.log(`[icon] ${path.relative(repoRoot, alias)} (alias 64x64)`);
  } finally {
    await browser.close();
  }
}

main().catch((err) => {
  console.error('[generate-desktop-icons] failed:', err);
  process.exitCode = 1;
});