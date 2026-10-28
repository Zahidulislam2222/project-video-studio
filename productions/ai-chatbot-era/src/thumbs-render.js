// Renders the four thumbnails to thumbnails/*.png (YouTube limit: 2 MB, so also writes JPEGs).
const http = require('http');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.ttf': 'font/ttf' };
const NAMES = { 1: 'thumbnail', 2: 'thumbnail-2', 3: 'thumbnail-3', 4: 'thumbnail-short-cover' };

(async () => {
  const server = http.createServer((req, res) => {
    const file = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
    if (!file.startsWith(ROOT) || !fs.existsSync(file)) { res.writeHead(404); return res.end(); }
    res.writeHead(200, { 'Content-Type': TYPES[path.extname(file)] || 'application/octet-stream' });
    fs.createReadStream(file).pipe(res);
  }).listen(0, '127.0.0.1');
  await new Promise((r) => server.once('listening', r));
  const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const dir = path.join(ROOT, 'thumbnails');
  fs.mkdirSync(dir, { recursive: true });
  for (const id of [1, 2, 3, 4]) {
    const page = await browser.newPage({ viewport: id === 4 ? { width: 1080, height: 1920 } : { width: 1280, height: 720 } });
    page.on('pageerror', (e) => console.error(e.message));
    await page.goto(`http://127.0.0.1:${server.address().port}/src/thumbs.html?id=${id}`);
    await page.waitForFunction(() => window.ready === true);
    const data = await page.evaluate(() => window.png());
    const png = path.join(dir, `${NAMES[id]}.png`);
    fs.writeFileSync(png, Buffer.from(data.split(',')[1], 'base64'));
    execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', png, '-q:v', '2', png.replace('.png', '.jpg')]);
    console.log(png);
    await page.close();
  }
  await browser.close();
  server.close();
})();
