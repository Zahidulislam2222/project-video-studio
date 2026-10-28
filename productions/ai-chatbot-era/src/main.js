// Compositor: 3D world + scene graphics + chapter HUD + word-synced captions + transitions.
// The renderer calls window.renderFrame(t) for every frame; nothing depends on wall time.
import { World } from './bg3d.js';
import { SCENES, CUES, PRESETS } from './scenes.js';
import { C, bind, clamp, prog, eOut, eInOut, lerp, hexA, text, measure, rrect, withAlpha, icon } from './kit.js';

const params = new URLSearchParams(location.search);
const VIDEO = params.get('v') || 'long';
const timing = await (await fetch(`../out/${VIDEO}/timing.json`)).json();
const P = timing.ratio === 'portrait';
const W = P ? 1080 : 1920, H = P ? 1920 : 1080;
const L = { W, H, P };

const glCanvas = document.getElementById('gl');
const out = document.getElementById('out');
glCanvas.width = out.width = W; glCanvas.height = out.height = H;
const g = out.getContext('2d');
bind(g);

const world = new World(glCanvas, W, H, timing.scenes, PRESETS[VIDEO]);
await document.fonts.load('800 40px Inter');
await Promise.all(['400', '600', '800'].map((w) => document.fonts.load(`${w} 40px Inter`)));
await Promise.all(['500 40px Grotesk', '700 40px Grotesk', '500 40px Mono'].map((f) => document.fonts.load(f)));

function loadImg(src) { return new Promise((res) => { const i = new Image(); i.onload = () => res(i); i.onerror = () => res(null); i.src = src; }); }
const assets = { desktop: await loadImg('../assets/portfolio-desktop-long.jpg'), mobile: await loadImg('../assets/portfolio-mobile.jpg') };

// ---------------------------------------------------------------- cues
const norm = (s) => s.toLowerCase().replace(/[^a-z0-9%/$-]/g, '');
const warnings = [];
function makeScene(sc, index) {
  const map = CUES[VIDEO][sc.id] || {};
  const cache = {};
  const resolve = (name) => {
    if (name in cache) return cache[name];
    let spec = name in map ? map[name] : name;
    let v = Infinity;
    if (spec) {
      const m = /^b(\d+)(?::(.+))?$/.exec(spec);
      if (!m) warnings.push(`${sc.id}: bad cue ${name}`);
      else {
        const beat = sc.beats[+m[1]];
        if (!beat) warnings.push(`${sc.id}: no beat for ${name}`);
        else if (!m[2]) v = beat.start - sc.start;
        else {
          const w = beat.words.find((x) => norm(x.w).startsWith(norm(m[2]))) || beat.words.find((x) => norm(x.w).includes(norm(m[2])));
          if (!w) { warnings.push(`${sc.id}: word "${m[2]}" not in beat ${m[1]}`); v = beat.start - sc.start; } else v = w.s - sc.start;
        }
      }
    }
    return (cache[name] = v);
  };
  return {
    id: sc.id, index, start: sc.start, end: sc.end, dur: sc.end - sc.start, chapter: sc.chapter, video: VIDEO, L,
    q: resolve,
    has: (name) => (name in map ? map[name] !== null : true) && resolve(name) !== Infinity,
  };
}
const scenes = timing.scenes.map(makeScene);
scenes.forEach((s) => Object.keys(CUES[VIDEO][s.id] || {}).forEach((k) => s.q(k)));
const chapters = timing.scenes.filter((s) => s.chapter);

// ---------------------------------------------------------------- captions
const MAXC = P ? 22 : 44;
const chunks = [];
for (const sc of timing.scenes) for (const b of sc.beats) {
  let cur = [];
  const flush = () => { if (cur.length) chunks.push(cur); cur = []; };
  for (const w of b.words) {
    const len = cur.map((x) => x.w).join(' ').length;
    if (cur.length && len + w.w.length + 1 > MAXC) flush();
    cur.push(w);
    if (/[.?!]$/.test(w.w) || (/,$/.test(w.w) && cur.map((x) => x.w).join(' ').length > MAXC * 0.55)) flush();
  }
  flush();
}
chunks.forEach((c, i) => { c.s = c[0].s; c.e = Math.min(c[c.length - 1].e + 0.35, chunks[i + 1] ? chunks[i + 1][0].s : Infinity); });

function captions(t) {
  const c = chunks.find((k) => t >= k.s - 0.05 && t < k.e);
  if (!c) return;
  const size = P ? 62 : 40;
  const y = P ? 1500 : 1000;
  const words = c.map((w) => w.w);
  const line = words.join(' ');
  const total = measure(line, size, 800);
  let x = W / 2 - total / 2;
  const appear = eOut(prog(t, c.s - 0.05, 0.18));
  // backing plate
  g.save();
  g.globalAlpha = 0.55 * appear;
  rrect(W / 2 - total / 2 - 28, y - size * 0.82, total + 56, size * 1.64, 18);
  g.fillStyle = '#050816'; g.fill();
  g.restore();
  c.forEach((w) => {
    const active = t >= w.s && t < w.e + 0.08;
    const done = t >= w.e;
    const ww = measure(w.w + ' ', size, 800);
    const k = active ? eOut(prog(t, w.s, 0.12)) : 0;
    withAlpha(appear, () => {
      g.save();
      g.translate(x + measure(w.w, size, 800) / 2, y - (P ? k * 6 : 0));
      g.scale(1 + (P ? 0.06 : 0.02) * k, 1 + (P ? 0.06 : 0.02) * k);
      g.lineWidth = P ? 10 : 7; g.lineJoin = 'round'; g.strokeStyle = 'rgba(5,8,22,0.9)';
      g.font = `800 ${size}px Inter`; g.textAlign = 'center'; g.textBaseline = 'middle';
      g.strokeText(w.w, 0, 0);
      g.fillStyle = active ? (P ? C.lime : C.cyan) : done ? '#ffffff' : 'rgba(255,255,255,0.78)';
      if (active) { g.shadowColor = P ? C.lime : C.cyan; g.shadowBlur = 18; }
      g.fillText(w.w, 0, 0);
      g.restore();
    });
    x += ww;
  });
}

// ---------------------------------------------------------------- HUD
function hud(t, sc) {
  // Progress bar with chapter ticks (long-form "levels").
  const total = timing.duration;
  if (!P) {
    g.fillStyle = 'rgba(255,255,255,0.08)'; g.fillRect(0, 0, W, 6);
    const grad = g.createLinearGradient(0, 0, W, 0); grad.addColorStop(0, C.cyan); grad.addColorStop(1, C.violet);
    g.fillStyle = grad; g.fillRect(0, 0, W * clamp(t / total), 6);
    chapters.forEach((c) => { g.fillStyle = '#050816'; g.fillRect(W * (c.start / total) - 2, 0, 4, 6); });
  }
  if (!sc.chapter) return;
  const n = chapters.findIndex((c) => c.id === sc.id) + 1;
  const lt = t - sc.start;
  // Big chapter card first, then it docks into the corner.
  const intro = 1 - eInOut(prog(lt, 0.9, 0.6));
  const appear = eOut(prog(lt, 0, 0.4));
  const exit = 1 - eOut(prog(lt, sc.dur - 0.4, 0.4));
  const num = String(n).padStart(2, '0');
  const label = sc.chapter.toUpperCase();
  if (intro > 0.01) {
    withAlpha(appear * intro, () => {
      const cy = P ? 900 : H / 2;
      g.save(); g.fillStyle = 'rgba(5,8,22,0.55)'; g.fillRect(0, 0, W, H); g.restore();
      text(`LEVEL ${num}`, W / 2, cy - 70, { size: 30, weight: 500, family: 'mono', color: C.cyan, align: 'center', letter: 10 });
      text(sc.chapter, W / 2, cy + 10, { size: P ? 84 : 96, weight: 800, align: 'center', glow: hexA(C.cyan, 0.6), blur: 40 });
      const lw = measure(sc.chapter, P ? 84 : 96, 800) * eOut(prog(lt, 0.1, 0.6));
      g.fillStyle = C.cyan; g.fillRect(W / 2 - lw / 2, cy + 80, lw, 4);
    });
  }
  const dock = eOut(prog(lt, 1.1, 0.5)) * exit;
  if (dock > 0.01) withAlpha(dock, () => {
    const x = P ? W / 2 : 70, y = P ? 230 : 62;
    const tagW = measure(num, 22, 500, 'mono') + 28;
    const labW = measure(label, 22, 500, 'mono');
    const full = tagW + 16 + labW;
    const x0 = P ? x - full / 2 : x;
    g.save(); rrect(x0, y - 20, tagW, 40, 10); g.fillStyle = C.cyan; g.fill(); g.restore();
    text(num, x0 + tagW / 2, y + 1, { size: 22, weight: 500, family: 'mono', color: '#04101a', align: 'center' });
    text(label, x0 + tagW + 16, y + 1, { size: 22, weight: 500, family: 'mono', color: C.ink, letter: 3 });
  });
}

function brand(t) {
  // Small persistent signature (subtle, top-right on landscape).
  if (P) return;
  withAlpha(0.55, () => {
    icon('sparkle', W - 300, 62, 22, C.cyan);
    text('zahidul-islam.com', W - 70, 63, { size: 20, weight: 500, family: 'mono', color: C.dim, align: 'right' });
  });
}

// Light-streak wipe at scene changes.
function sweep(t) {
  for (const sc of scenes) {
    if (!sc.index) continue;
    const k = (t - sc.start + 0.25) / 0.6;
    if (k < 0 || k > 1) continue;
    const x = lerp(-0.4 * W, 1.4 * W, eInOut(k));
    g.save();
    g.globalCompositeOperation = 'lighter';
    const gr = g.createLinearGradient(x - 300, 0, x + 300, 0);
    gr.addColorStop(0, 'rgba(34,211,238,0)'); gr.addColorStop(0.5, 'rgba(139,92,246,0.35)'); gr.addColorStop(1, 'rgba(34,211,238,0)');
    g.fillStyle = gr;
    g.setTransform(1, 0, -0.35, 1, 0, 0);
    g.fillRect(x - 300 + H * 0.17, 0, 600, H);
    g.restore();
  }
}

function vignette() {
  const r = g.createRadialGradient(W / 2, H / 2, Math.min(W, H) * 0.25, W / 2, H / 2, Math.max(W, H) * 0.75);
  r.addColorStop(0, 'rgba(5,8,22,0.15)'); r.addColorStop(1, 'rgba(5,8,22,0.85)');
  g.fillStyle = r; g.fillRect(0, 0, W, H);
}

export function frame(t) {
  world.render(t);
  g.setTransform(1, 0, 0, 1, 0, 0);
  g.globalAlpha = 1;
  g.drawImage(glCanvas, 0, 0);
  vignette();
  let sc = scenes.find((s) => t >= s.start && t < s.end) || scenes[scenes.length - 1];
  const lt = t - sc.start;
  // Fly-through: content scales up and fades at the end, enters from slightly small.
  const enter = eOut(prog(lt, 0, 0.6));
  const exit = eInOut(prog(lt, sc.dur - 0.45, 0.45));
  const last = sc.index === scenes.length - 1;
  const s = lerp(0.94, 1, enter) * (last ? 1 : lerp(1, 1.12, exit));
  g.save();
  g.globalAlpha = enter * (last ? 1 : 1 - exit);
  g.translate(W / 2, H / 2); g.scale(s, s); g.translate(-W / 2, -H / 2 + (P ? 110 : 0));
  SCENES[sc.id]({ ...sc, lt, t }, assets);
  g.restore();
  hud(t, sc);
  brand(t);
  captions(t);
  sweep(t);
  // Fade from black at start, to black at end.
  const fade = Math.max(1 - prog(t, 0, 0.6), prog(t, timing.duration - 0.8, 0.8));
  if (fade > 0) { g.fillStyle = `rgba(0,0,0,${fade})`; g.fillRect(0, 0, W, H); }
}

window.renderFrame = (t, quality = 0.93) => { frame(t); return out.toDataURL('image/jpeg', quality); };
window.timing = timing;
window.warnings = warnings;
window.sfxEvents = () => {
  const ev = [];
  scenes.forEach((sc) => {
    if (sc.index) ev.push({ t: sc.start - 0.25, k: 'whoosh' });
    if (sc.chapter) ev.push({ t: sc.start + 0.05, k: 'hit' });
  });
  return ev;
};
window.ready = true;
