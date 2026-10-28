// Frame-accurate renderer: serves the production folder, drives headless Chromium and pipes
// JPEG frames into FFmpeg. Usage:
//   node src/render.js long stills 3 12.5 40      -> out/long/stills/*.png
//   node src/render.js long video [workers]        -> out/long/video.mp4 (silent picture)
const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const [video, mode, ...rest] = process.argv.slice(2);
const FPS = 30;
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.ttf': 'font/ttf', '.jpg': 'image/jpeg', '.png': 'image/png' };

function serve() {
  return new Promise((resolve) => {
    const server = http.createServer((req, res) => {
      const file = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
      if (!file.startsWith(ROOT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) { res.writeHead(404); return res.end(); }
      res.writeHead(200, { 'Content-Type': TYPES[path.extname(file)] || 'application/octet-stream' });
      fs.createReadStream(file).pipe(res);
    });
    server.listen(0, '127.0.0.1', () => resolve(server));
  });
}

async function openPage(browser, port) {
  const portrait = JSON.parse(fs.readFileSync(path.join(ROOT, 'out', video, 'timing.json'))).ratio === 'portrait';
  const page = await browser.newPage({ viewport: portrait ? { width: 1080, height: 1920 } : { width: 1920, height: 1080 } });
  page.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warning') console.error('[page]', m.text()); });
  page.on('pageerror', (e) => console.error('[page error]', e.message));
  await page.goto(`http://127.0.0.1:${port}/src/index.html?v=${video}`);
  await page.waitForFunction(() => window.ready === true, null, { timeout: 120000 });
  return page;
}

const launch = () => chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });

async function stills(times) {
  const server = await serve();
  const browser = await launch();
  const page = await openPage(browser, server.address().port);
  const warnings = await page.evaluate(() => window.warnings);
  if (warnings.length) console.log('CUE WARNINGS:\n' + warnings.join('\n'));
  const dir = path.join(ROOT, 'out', video, 'stills');
  fs.mkdirSync(dir, { recursive: true });
  for (const t of times) {
    const data = await page.evaluate((tt) => window.renderFrame(tt, 0.92), +t);
    const file = path.join(dir, `t${String(t).padStart(6, '0')}.jpg`);
    fs.writeFileSync(file, Buffer.from(data.split(',')[1], 'base64'));
    console.log(file);
  }
  await browser.close();
  server.close();
}

async function segment(port, browser, from, to, file, label) {
  const page = await openPage(browser, port);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-c:v', 'mjpeg', '-framerate', String(FPS), '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p', '-r', String(FPS), file], { stdio: ['pipe', 'inherit', 'inherit'] });
  const started = Date.now();
  for (let f = from; f < to; f++) {
    const data = await page.evaluate((tt) => window.renderFrame(tt, 0.95), f / FPS);
    const buf = Buffer.from(data.slice(data.indexOf(',') + 1), 'base64');
    if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
    if ((f - from) % 300 === 0) {
      const done = f - from, rate = done / ((Date.now() - started) / 1000 || 1);
      console.log(`[${label}] ${done}/${to - from} frames · ${rate.toFixed(1)} fps`);
    }
  }
  ff.stdin.end();
  await new Promise((r, j) => ff.on('close', (c) => (c ? j(new Error('ffmpeg ' + c)) : r())));
  await page.close();
}

async function full(workers) {
  const timing = JSON.parse(fs.readFileSync(path.join(ROOT, 'out', video, 'timing.json')));
  const total = Math.round(timing.duration * FPS);
  const server = await serve();
  const port = server.address().port;
  const dir = path.join(ROOT, 'out', video, 'parts');
  fs.mkdirSync(dir, { recursive: true });
  const per = Math.ceil(total / workers);
  const browsers = await Promise.all(Array.from({ length: workers }, launch));
  const files = [];
  await Promise.all(browsers.map((b, i) => {
    const file = path.join(dir, `part${i}.mp4`);
    files.push(file);
    return segment(port, b, i * per, Math.min(total, (i + 1) * per), file, `w${i}`);
  }));
  await Promise.all(browsers.map((b) => b.close()));
  server.close();
  const list = path.join(dir, 'list.txt');
  fs.writeFileSync(list, files.map((f) => `file '${f}'`).join('\n'));
  await new Promise((r, j) => spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy', path.join(ROOT, 'out', video, 'picture.mp4')], { stdio: 'inherit' }).on('close', (c) => (c ? j(c) : r())));
  console.log(`picture: ${total} frames`);
}

async function events() {
  const server = await serve();
  const browser = await launch();
  const page = await openPage(browser, server.address().port);
  const ev = await page.evaluate(() => window.sfxEvents());
  fs.writeFileSync(path.join(ROOT, 'out', video, 'sfx.json'), JSON.stringify(ev));
  await browser.close();
  server.close();
}

(mode === 'stills' ? stills(rest) : mode === 'events' ? events() : full(+(rest[0] || 3))).catch((e) => { console.error(e); process.exit(1); });
