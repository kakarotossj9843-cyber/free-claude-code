// Usage: node render.js <stills|full> <outDir> [startFrame] [endFrame]
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const FPS = 24, DUR = 120, N = FPS * DUR;

(async () => {
  const [, , mode = 'stills', outDir = '.', s = '0', e = String(N)] = process.argv;
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({
    args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--no-sandbox'],
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  page.on('console', (m) => { if (m.type() === 'error') console.error('PAGE:', m.text()); });
  page.on('pageerror', (err) => console.error('PAGEERR:', err.message));
  await page.goto('http://127.0.0.1:8765/index.html');
  await page.waitForFunction(() => window.ready === true, null, { timeout: 60000 });

  const save = async (t, file) => {
    const url = await page.evaluate((tt) => window.renderAt(tt), t);
    fs.writeFileSync(file, Buffer.from(url.split(',')[1], 'base64'));
  };

  if (mode === 'stills') {
    const times = [5, 15, 25, 40, 52, 64, 72, 75, 88, 98, 110, 117];
    for (const tt of times) await save(tt, path.join(outDir, `still_${String(tt).padStart(3, '0')}.png`));
  } else {
    const t0 = Number(s), t1 = Math.min(Number(e), N);
    const t_start = Date.now();
    for (let i = t0; i < t1; i++) {
      await save(i / FPS, path.join(outDir, `f_${String(i).padStart(5, '0')}.png`));
      if (i % 120 === 0) console.log('frame', i, '/', N, 'elapsed', ((Date.now() - t_start) / 1000).toFixed(0) + 's');
    }
    console.log('done', t0, t1);
  }
  await browser.close();
})().catch((err) => { console.error(err); process.exit(1); });
