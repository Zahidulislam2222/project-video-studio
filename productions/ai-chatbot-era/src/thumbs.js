// Thumbnails: same 3D world and kit as the films, composed as single high-contrast stills.
// thumbs.html?id=1..4 ; render via `node src/thumbs-render.js`.
import { World } from './bg3d.js';
import { phone, chatHeader } from './scenes.js';
import { C, bind, hexA, text, measure, rrect, panel, pill, badge, bubble, circle, ring, icon, glowLine, withAlpha } from './kit.js';

const id = +(new URLSearchParams(location.search).get('id') || 1);
const P = id === 4;
const W = P ? 1080 : 1280, H = P ? 1920 : 720;
const gl = document.getElementById('gl'), out = document.getElementById('out');
gl.width = out.width = W; gl.height = out.height = H;
const g = out.getContext('2d');
bind(g);

const PRESET = {
  1: { core: [11, 1, 0, 1.15, 1], color: '#22d3ee', color2: '#8b5cf6', grid: 0.7 },
  2: { core: [-12, 1, -4, 1.0, 0.9], color: '#a3e635', color2: '#22d3ee', grid: 0.6 },
  3: { core: [0, 2, -20, 1.2, 0.6], color: '#fbbf24', color2: '#f43f5e', grid: 0.6 },
  4: { core: [0, 6, -6, 1.0, 1], color: '#22d3ee', color2: '#8b5cf6', grid: 0.7 },
}[id];
const world = new World(gl, W, H, [{ id: 't', start: 0, end: 30 }], { t: PRESET });
await Promise.all(['400 40px Inter', '500 40px Inter', '800 40px Inter', '600 40px Inter', '700 40px Grotesk', '500 40px Mono'].map((f) => document.fonts.load(f)));

world.render(6.2);
g.drawImage(gl, 0, 0);
const vg = g.createRadialGradient(W / 2, H / 2, Math.min(W, H) * 0.3, W / 2, H / 2, Math.max(W, H) * 0.75);
vg.addColorStop(0, 'rgba(5,8,22,0.1)'); vg.addColorStop(1, 'rgba(5,8,22,0.9)');
g.fillStyle = vg; g.fillRect(0, 0, W, H);

// Heavy outlined headline: readable at 168px-wide suggestion size.
function big(str, x, y, size, o = {}) {
  g.save();
  g.font = `800 ${size}px Inter`;
  g.textAlign = o.align || 'left'; g.textBaseline = 'middle';
  if ('letterSpacing' in g) g.letterSpacing = `${-size * 0.03}px`;
  g.lineJoin = 'round'; g.lineWidth = size * 0.14; g.strokeStyle = '#03050f';
  g.strokeText(str, x, y);
  if (o.gradient) {
    const w = g.measureText(str).width;
    const x0 = o.align === 'center' ? x - w / 2 : x;
    const gr = g.createLinearGradient(x0, 0, x0 + w, 0);
    o.gradient.forEach((c, i) => gr.addColorStop(i / (o.gradient.length - 1), c));
    g.fillStyle = gr;
  } else g.fillStyle = o.color || '#fff';
  g.shadowColor = o.glow || 'rgba(0,0,0,0)'; g.shadowBlur = o.glow ? size * 0.45 : 0;
  g.fillText(str, x, y);
  g.restore();
}

function chat(px, py, pw, ph, msgs) {
  phone(px, py, pw, ph, (w) => {
    chatHeader(w, 'AI Assistant', 'online · replies instantly');
    let y = 170;
    for (const [side, s] of msgs) y += bubble(26, y, w - 52, s, side, { size: 25 }) + 16;
  }, { glow: hexA(C.cyan, 0.7) });
}

if (id === 1) {
  // "Your app needs this" + glowing AI chat phone.
  big('YOUR APP', 60, 170, 120);
  big('NEEDS', 60, 300, 120);
  big('THIS', 60, 430, 140, { gradient: [C.cyan, C.violet, C.pink], glow: hexA(C.violet, 0.9) });
  pill(64, 560, 'AI CHATBOT · 24/7', { icon: 'bolt', color: C.lime, size: 34, solid: true, glow: true });
  g.save(); g.translate(780, 40); g.rotate(0.06);
  chat(0, 0, 420, 700, [['r', 'Is this back in stock?'], ['l', 'Yes! 14 left in your size.'], ['l', 'Want me to add it to your cart?'], ['r', 'Yes please']]);
  g.restore();
  glowLine([[660, 500], [770, 430]], C.lime, 8);
  glowLine([[750, 425], [775, 430], [760, 452]], C.lime, 8);
}

if (id === 2) {
  // "700 agents" proof number.
  big('1 AI =', 70, 150, 110, { color: '#fff' });
  big('700', 50, 360, 290, { gradient: [C.lime, '#4ade80', C.cyan], glow: hexA(C.lime, 0.8) });
  big("AGENTS' WORK?", 70, 560, 86, { color: '#fff' });
  // grid of 700 dots = agents
  const gx = 800, gy = 90, s = 15.5, cols = 28;
  for (let i = 0; i < 700; i++) circle(gx + (i % cols) * s, gy + Math.floor(i / cols) * s, 5.2, hexA(i < 467 ? C.lime : C.cyan, 0.9));
  badge('bot', 1018, 300, 92, C.cyan, { blur: 60 });
  pill(70, 655, 'Klarna · 2024 · real data', { icon: 'doc', color: C.dim, size: 24 });
}

if (id === 3) {
  // Wrong vs right split.
  g.fillStyle = hexA(C.red, 0.16); g.fillRect(0, 0, W / 2, H);
  g.fillStyle = hexA(C.green, 0.14); g.fillRect(W / 2, 0, W / 2, H);
  glowLine([[W / 2, 0], [W / 2, H]], '#ffffff', 4);
  big('WRONG', W / 4, 110, 110, { align: 'center', color: C.red, glow: C.red });
  big('RIGHT', (3 * W) / 4, 110, 110, { align: 'center', color: C.green, glow: C.green });
  // left: bad bot
  panel(70, 210, 500, 250, { glow: hexA(C.red, 0.6) });
  badge('bot', 150, 290, 52, C.red);
  text('“Sure, full refund!”', 220, 290, { size: 34, weight: 800 });
  text('wrong policy · company liable', 110, 400, { size: 26, weight: 600, color: '#fda4af' });
  badge('x', 320, 560, 70, C.red, { blur: 50 });
  // right: guarded bot
  panel(710, 210, 500, 250, { glow: hexA(C.green, 0.6) });
  badge('shieldcheck', 790, 290, 52, C.green);
  text('Checked your order.', 860, 278, { size: 32, weight: 800 });
  text('Refund policy: 30 days', 860, 318, { size: 24, weight: 600, color: C.dim });
  text('grounded · logged · human backup', 750, 400, { size: 26, weight: 600, color: '#86efac' });
  badge('check', 960, 560, 70, C.green, { blur: 50 });
  big('AI CHATBOTS', W / 2, 668, 74, { align: 'center', gradient: [C.amber, '#fff', C.cyan] });
}

if (id === 4) {
  // Portrait cover: key text inside the centre 3:4 crop (y 285..1635).
  big('IS YOUR', W / 2, 400, 150, { align: 'center' });
  big('APP READY', W / 2, 560, 150, { align: 'center' });
  big('FOR AI?', W / 2, 730, 180, { align: 'center', gradient: [C.cyan, C.violet, C.pink], glow: hexA(C.violet, 0.9) });
  g.save(); g.translate(270, 860);
  chat(0, 0, 540, 720, [['r', 'Where is my order?'], ['l', 'Out for delivery, arriving by 6 PM.'], ['r', 'Can I change the size?'], ['l', 'Done. Size M confirmed.']]);
  g.restore();
  pill(W / 2, 1650, 'Works 24/7 · no queue', { icon: 'bolt', color: C.lime, align: 'center', size: 40, solid: true, glow: true });
}

window.png = () => out.toDataURL('image/png');
window.ready = true;
