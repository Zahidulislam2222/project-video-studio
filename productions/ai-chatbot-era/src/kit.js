// Drawing kit: easing, text, glass panels, line icons, connectors. Everything is a pure
// function of the arguments so any frame can be rendered independently.

export const C = {
  bg: '#050816', bg2: '#0a1030', ink: '#f4f7ff', dim: '#9aa6c7', faint: '#5b6690',
  cyan: '#22d3ee', blue: '#3b82f6', violet: '#8b5cf6', pink: '#ec4899',
  lime: '#a3e635', green: '#34d399', amber: '#fbbf24', red: '#f43f5e',
  panel: 'rgba(16,24,58,0.72)', line: 'rgba(148,170,255,0.22)',
};

export const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
export const lerp = (a, b, t) => a + (b - a) * t;
export const prog = (t, a, d) => clamp((t - a) / d);
export const eOut = (t) => 1 - Math.pow(1 - t, 3);
export const eIn = (t) => t * t * t;
export const eInOut = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
export const eExpo = (t) => (t >= 1 ? 1 : 1 - Math.pow(2, -10 * t));
export const eBack = (t) => { const c = 1.70158, c3 = c + 1; return 1 + c3 * Math.pow(t - 1, 3) + c * Math.pow(t - 1, 2); };

export function rng(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function hexA(hex, a) {
  const n = parseInt(hex.slice(1), 16);
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
}

let X = null;
export function bind(ctx) { X = ctx; }
export const ctx = () => X;

export function withAlpha(a, fn) {
  if (a <= 0.001) return;
  X.save(); X.globalAlpha *= clamp(a); fn(); X.restore();
}

export function withT(x, y, s, fn, rot = 0) {
  X.save(); X.translate(x, y); if (rot) X.rotate(rot); X.scale(s, s); fn(); X.restore();
}

const FAM = { inter: 'Inter', grotesk: 'Grotesk', mono: 'Mono' };
export function font(size, weight = 600, family = 'inter') {
  X.font = `${weight} ${size}px ${FAM[family] || family}`;
}

export function text(str, x, y, o = {}) {
  const size = o.size || 32;
  font(size, o.weight || 600, o.family || 'inter');
  X.textAlign = o.align || 'left';
  X.textBaseline = o.baseline || 'middle';
  if ('letterSpacing' in X) X.letterSpacing = (o.letter || 0) + 'px';
  if (o.glow) { X.shadowColor = o.glow; X.shadowBlur = o.blur || size * 0.6; }
  if (o.gradient) {
    const w = X.measureText(str).width;
    const x0 = o.align === 'center' ? x - w / 2 : o.align === 'right' ? x - w : x;
    const g = X.createLinearGradient(x0, 0, x0 + w, 0);
    o.gradient.forEach((c, i) => g.addColorStop(i / (o.gradient.length - 1), c));
    X.fillStyle = g;
  } else X.fillStyle = o.color || C.ink;
  X.fillText(str, x, y);
  X.shadowBlur = 0;
  if ('letterSpacing' in X) X.letterSpacing = '0px';
}

export function measure(str, size, weight = 600, family = 'inter') {
  font(size, weight, family);
  return X.measureText(str).width;
}

export function wrap(str, maxW, size, weight = 600, family = 'inter') {
  font(size, weight, family);
  const words = str.split(' ');
  const lines = [];
  let cur = '';
  for (const w of words) {
    const t = cur ? cur + ' ' + w : w;
    if (X.measureText(t).width > maxW && cur) { lines.push(cur); cur = w; } else cur = t;
  }
  if (cur) lines.push(cur);
  return lines;
}

export function para(str, x, y, maxW, o = {}) {
  const size = o.size || 30;
  const lines = wrap(str, maxW, size, o.weight || 500, o.family || 'inter');
  const lh = size * (o.lh || 1.3);
  lines.forEach((l, i) => text(l, x, y + i * lh, { ...o, size }));
  return lines.length * lh;
}

export function rrect(x, y, w, h, r) {
  r = Math.min(r, w / 2, h / 2);
  X.beginPath();
  X.moveTo(x + r, y);
  X.arcTo(x + w, y, x + w, y + h, r);
  X.arcTo(x + w, y + h, x, y + h, r);
  X.arcTo(x, y + h, x, y, r);
  X.arcTo(x, y, x + w, y, r);
  X.closePath();
}

// Glass card: dark translucent fill, top highlight, hairline border and optional colored glow.
export function panel(x, y, w, h, o = {}) {
  const r = o.r ?? 22;
  X.save();
  if (o.glow) { X.shadowColor = o.glow; X.shadowBlur = o.blur ?? 40; }
  rrect(x, y, w, h, r);
  const g = X.createLinearGradient(x, y, x, y + h);
  g.addColorStop(0, o.fill2 || 'rgba(30,42,92,0.82)');
  g.addColorStop(1, o.fill || 'rgba(10,16,44,0.86)');
  X.fillStyle = g;
  X.fill();
  X.shadowBlur = 0;
  X.lineWidth = o.lw || 1.5;
  const s = X.createLinearGradient(x, y, x + w, y + h);
  s.addColorStop(0, o.stroke || 'rgba(160,190,255,0.45)');
  s.addColorStop(1, o.stroke2 || 'rgba(160,190,255,0.08)');
  X.strokeStyle = s;
  X.stroke();
  X.restore();
}

export function pill(x, y, label, o = {}) {
  const size = o.size || 24;
  const padX = size * 0.75;
  const iconW = o.icon ? size * 1.25 : 0;
  const w = measure(label, size, o.weight || 600) + padX * 2 + iconW;
  const h = size * 1.9;
  const x0 = o.align === 'center' ? x - w / 2 : o.align === 'right' ? x - w : x;
  const col = o.color || C.cyan;
  X.save();
  rrect(x0, y - h / 2, w, h, h / 2);
  X.fillStyle = o.solid ? col : hexA(col, 0.14);
  if (o.glow) { X.shadowColor = col; X.shadowBlur = 24; }
  X.fill();
  X.shadowBlur = 0;
  X.strokeStyle = hexA(col, 0.6);
  X.lineWidth = 1.5;
  X.stroke();
  X.restore();
  if (o.icon) icon(o.icon, x0 + padX + size * 0.45, y, size * 0.95, o.solid ? C.bg : col);
  text(label, x0 + padX + iconW, y + 1, { size, weight: o.weight || 600, color: o.solid ? C.bg : o.text || C.ink });
  return w;
}

export function glowLine(pts, color, width = 3, o = {}) {
  X.save();
  X.lineCap = 'round'; X.lineJoin = 'round';
  X.strokeStyle = color; X.lineWidth = width;
  if (o.dash) { X.setLineDash(o.dash); X.lineDashOffset = o.offset || 0; }
  X.shadowColor = color; X.shadowBlur = o.blur ?? 14;
  X.beginPath();
  pts.forEach(([px, py], i) => (i ? X.lineTo(px, py) : X.moveTo(px, py)));
  X.stroke();
  X.restore();
}

// Point along a polyline at fraction f (0..1).
export function along(pts, f) {
  let total = 0;
  const seg = [];
  for (let i = 1; i < pts.length; i++) {
    const d = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
    seg.push(d); total += d;
  }
  let target = clamp(f) * total;
  for (let i = 0; i < seg.length; i++) {
    if (target <= seg[i] || i === seg.length - 1) {
      const k = seg[i] ? target / seg[i] : 0;
      return [lerp(pts[i][0], pts[i + 1][0], k), lerp(pts[i][1], pts[i + 1][1], k)];
    }
    target -= seg[i];
  }
  return pts[pts.length - 1];
}

// Partial polyline (draw-on effect).
export function partial(pts, f) {
  if (f >= 1) return pts;
  let total = 0;
  for (let i = 1; i < pts.length; i++) total += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
  let left = clamp(f) * total;
  const out = [pts[0]];
  for (let i = 1; i < pts.length; i++) {
    const d = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
    if (left >= d) { out.push(pts[i]); left -= d; } else {
      const k = d ? left / d : 0;
      out.push([lerp(pts[i - 1][0], pts[i][0], k), lerp(pts[i - 1][1], pts[i][1], k)]);
      break;
    }
  }
  return out;
}

// Connector with draw-on, then travelling packets.
export function flow(pts, t, start, color, o = {}) {
  const draw = eOut(prog(t, start, o.drawDur ?? 0.6));
  if (draw <= 0) return;
  glowLine(pts, hexA(color, 0.35), o.width || 3, { blur: 0 });
  glowLine(partial(pts, draw), hexA(color, 0.85), o.width || 3, { blur: 10 });
  if (draw >= 1 && o.packets !== 0) {
    const n = o.packets || 2;
    const speed = o.speed || 0.6;
    for (let i = 0; i < n; i++) {
      const f = ((t - start) * speed + i / n) % 1;
      const [px, py] = along(pts, o.reverse ? 1 - f : f);
      X.save();
      X.fillStyle = '#ffffff';
      X.shadowColor = color; X.shadowBlur = 18;
      X.beginPath(); X.arc(px, py, (o.width || 3) * 1.9, 0, Math.PI * 2); X.fill();
      X.restore();
    }
  }
}

export function circle(x, y, r, fill, o = {}) {
  X.save();
  if (o.glow) { X.shadowColor = o.glow; X.shadowBlur = o.blur || r; }
  X.beginPath(); X.arc(x, y, r, 0, Math.PI * 2);
  if (fill) { X.fillStyle = fill; X.fill(); }
  if (o.stroke) { X.shadowBlur = 0; X.strokeStyle = o.stroke; X.lineWidth = o.lw || 2; X.stroke(); }
  X.restore();
}

export function ring(x, y, r, f, color, lw, o = {}) {
  X.save();
  X.lineCap = 'round';
  X.lineWidth = lw;
  X.strokeStyle = o.track || 'rgba(255,255,255,0.08)';
  X.beginPath(); X.arc(x, y, r, 0, Math.PI * 2); X.stroke();
  X.strokeStyle = color; X.shadowColor = color; X.shadowBlur = 20;
  X.beginPath(); X.arc(x, y, r, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * clamp(f)); X.stroke();
  X.restore();
}

// Lucide-style line icons drawn in a 24x24 box centered on (x, y).
export function icon(name, x, y, s, color = C.ink, lw = 2) {
  const d = ICONS[name];
  if (!d) return;
  X.save();
  X.translate(x, y); X.scale(s / 24, s / 24); X.translate(-12, -12);
  X.strokeStyle = color; X.fillStyle = color;
  X.lineWidth = lw; X.lineCap = 'round'; X.lineJoin = 'round';
  d(X);
  X.restore();
}

const P = (c, cmds) => { c.beginPath(); cmds(); c.stroke(); };
const ICONS = {
  chat: (c) => { P(c, () => { rr(c, 3, 4, 18, 13, 4); }); P(c, () => { c.moveTo(8, 17); c.lineTo(6, 21); c.lineTo(12, 17); }); },
  bot: (c) => { P(c, () => rr(c, 4, 8, 16, 12, 4)); P(c, () => { c.moveTo(12, 8); c.lineTo(12, 4); }); dot(c, 12, 3.5, 1.4); dot(c, 9, 14, 1.5); dot(c, 15, 14, 1.5); P(c, () => { c.moveTo(2, 13); c.lineTo(2, 16); c.moveTo(22, 13); c.lineTo(22, 16); }); },
  user: (c) => { P(c, () => c.arc(12, 8, 4, 0, 7)); P(c, () => { c.moveTo(4, 21); c.bezierCurveTo(4, 15, 20, 15, 20, 21); }); },
  users: (c) => { P(c, () => c.arc(9, 8, 3.5, 0, 7)); P(c, () => { c.moveTo(2, 20); c.bezierCurveTo(2, 14, 16, 14, 16, 20); }); P(c, () => { c.moveTo(16, 4.5); c.arc(16, 8, 3.5, -1.5, 1.5); c.moveTo(18, 14.5); c.bezierCurveTo(21, 15.5, 22, 17, 22, 20); }); },
  cart: (c) => { P(c, () => { c.moveTo(2, 3); c.lineTo(5, 3); c.lineTo(8, 15); c.lineTo(19, 15); c.lineTo(21, 7); c.lineTo(6, 7); }); dot(c, 9, 19.5, 1.6); dot(c, 18, 19.5, 1.6); },
  box: (c) => { P(c, () => { c.moveTo(12, 2.5); c.lineTo(21, 7); c.lineTo(21, 17); c.lineTo(12, 21.5); c.lineTo(3, 17); c.lineTo(3, 7); c.closePath(); c.moveTo(3, 7); c.lineTo(12, 11.5); c.lineTo(21, 7); c.moveTo(12, 11.5); c.lineTo(12, 21.5); }); },
  shield: (c) => { P(c, () => { c.moveTo(12, 2.5); c.lineTo(20, 5.5); c.lineTo(20, 11); c.bezierCurveTo(20, 16, 16.5, 19.5, 12, 21.5); c.bezierCurveTo(7.5, 19.5, 4, 16, 4, 11); c.lineTo(4, 5.5); c.closePath(); }); },
  shieldcheck: (c) => { ICONS.shield(c); P(c, () => { c.moveTo(8.5, 12); c.lineTo(11, 14.5); c.lineTo(15.5, 9.5); }); },
  doc: (c) => { P(c, () => { c.moveTo(14, 2.5); c.lineTo(6, 2.5); c.lineTo(5, 3.5); c.lineTo(5, 21); c.lineTo(19, 21); c.lineTo(19, 7.5); c.closePath(); c.moveTo(14, 2.5); c.lineTo(14, 7.5); c.lineTo(19, 7.5); c.moveTo(8.5, 12); c.lineTo(15.5, 12); c.moveTo(8.5, 16); c.lineTo(15.5, 16); }); },
  chart: (c) => { P(c, () => { c.moveTo(3, 3); c.lineTo(3, 21); c.lineTo(21, 21); c.moveTo(7, 16); c.lineTo(11, 11); c.lineTo(14, 14); c.lineTo(20, 6); }); },
  bars: (c) => { P(c, () => { c.moveTo(6, 20); c.lineTo(6, 13); c.moveTo(12, 20); c.lineTo(12, 5); c.moveTo(18, 20); c.lineTo(18, 9); }); },
  globe: (c) => { P(c, () => c.arc(12, 12, 9.5, 0, 7)); P(c, () => { c.moveTo(2.5, 12); c.lineTo(21.5, 12); c.ellipse(12, 12, 4.2, 9.5, 0, 0, 7); }); },
  lock: (c) => { P(c, () => rr(c, 4, 11, 16, 10, 2.5)); P(c, () => { c.moveTo(8, 11); c.lineTo(8, 7.5); c.arc(12, 7.5, 4, Math.PI, 0); c.lineTo(16, 11); }); },
  bolt: (c) => { P(c, () => { c.moveTo(13, 2); c.lineTo(4, 14); c.lineTo(12, 14); c.lineTo(11, 22); c.lineTo(20, 10); c.lineTo(12, 10); c.closePath(); }); },
  clock: (c) => { P(c, () => c.arc(12, 12, 9.5, 0, 7)); P(c, () => { c.moveTo(12, 6.5); c.lineTo(12, 12); c.lineTo(15.5, 14); }); },
  db: (c) => { P(c, () => c.ellipse(12, 5.5, 8, 3, 0, 0, 7)); P(c, () => { c.moveTo(4, 5.5); c.lineTo(4, 18.5); c.ellipse(12, 18.5, 8, 3, 0, Math.PI, 0, true); c.lineTo(20, 5.5); c.moveTo(4, 12); c.ellipse(12, 12, 8, 3, 0, Math.PI, 0, true); }); },
  brain: (c) => { P(c, () => { c.moveTo(12, 4.5); c.bezierCurveTo(9, 2, 4.5, 3.5, 5, 7.5); c.bezierCurveTo(2, 8.5, 2, 13, 4.5, 14); c.bezierCurveTo(3.5, 18, 8, 21, 12, 19); c.bezierCurveTo(16, 21, 20.5, 18, 19.5, 14); c.bezierCurveTo(22, 13, 22, 8.5, 19, 7.5); c.bezierCurveTo(19.5, 3.5, 15, 2, 12, 4.5); c.moveTo(12, 4.5); c.lineTo(12, 19); c.moveTo(8, 9); c.bezierCurveTo(9.5, 9.5, 10.5, 10.5, 12, 12); c.moveTo(16, 9); c.bezierCurveTo(14.5, 9.5, 13.5, 10.5, 12, 12); }); },
  gear: (c) => { P(c, () => c.arc(12, 12, 3.2, 0, 7)); P(c, () => { for (let i = 0; i < 8; i++) { const a = (i * Math.PI) / 4; c.moveTo(12 + Math.cos(a) * 6.5, 12 + Math.sin(a) * 6.5); c.lineTo(12 + Math.cos(a) * 9.5, 12 + Math.sin(a) * 9.5); } c.moveTo(18.5, 12); c.arc(12, 12, 6.5, 0, 7); }); },
  bell: (c) => { P(c, () => { c.moveTo(6, 16); c.lineTo(6, 10); c.bezierCurveTo(6, 3, 18, 3, 18, 10); c.lineTo(18, 16); c.lineTo(20, 18); c.lineTo(4, 18); c.closePath(); c.moveTo(10, 21); c.lineTo(14, 21); }); },
  check: (c) => { P(c, () => { c.moveTo(4.5, 12.5); c.lineTo(9.5, 17.5); c.lineTo(19.5, 6.5); }); },
  x: (c) => { P(c, () => { c.moveTo(6, 6); c.lineTo(18, 18); c.moveTo(18, 6); c.lineTo(6, 18); }); },
  moon: (c) => { P(c, () => { c.moveTo(20, 14.5); c.bezierCurveTo(14, 17, 7.5, 12, 9.5, 4); c.bezierCurveTo(4.5, 5.5, 2.5, 12, 6, 17); c.bezierCurveTo(9.5, 21.5, 17, 21, 20, 14.5); }); },
  search: (c) => { P(c, () => c.arc(10.5, 10.5, 6.5, 0, 7)); P(c, () => { c.moveTo(15.5, 15.5); c.lineTo(21, 21); }); },
  card: (c) => { P(c, () => rr(c, 2.5, 5, 19, 14, 2.5)); P(c, () => { c.moveTo(2.5, 10); c.lineTo(21.5, 10); c.moveTo(6, 15); c.lineTo(10, 15); }); },
  wrench: (c) => { P(c, () => { c.moveTo(14.5, 6); c.bezierCurveTo(13.5, 3, 17, 1.5, 19.5, 3); c.lineTo(16.5, 6); c.lineTo(18, 7.5); c.lineTo(21, 4.5); c.bezierCurveTo(22.5, 7, 21, 10.5, 18, 9.5); c.lineTo(7, 20.5); c.bezierCurveTo(5.5, 22, 2, 18.5, 3.5, 17); c.closePath(); }); },
  alert: (c) => { P(c, () => { c.moveTo(12, 3); c.lineTo(22, 20); c.lineTo(2, 20); c.closePath(); c.moveTo(12, 9.5); c.lineTo(12, 13.5); }); dot(c, 12, 16.8, 1.2); },
  gavel: (c) => { P(c, () => { c.moveTo(14, 4); c.lineTo(20, 10); c.moveTo(11, 7); c.lineTo(17, 13); c.moveTo(12.5, 5.5); c.lineTo(18.5, 11.5); c.moveTo(14, 10); c.lineTo(5, 19); c.moveTo(3, 21); c.lineTo(13, 21); }); },
  refresh: (c) => { P(c, () => { c.arc(12, 12, 8, -2.6, 1.9); }); P(c, () => { c.moveTo(3.5, 3.5); c.lineTo(4.8, 8); c.lineTo(9.2, 6.6); }); },
  calc: (c) => { P(c, () => rr(c, 5, 2.5, 14, 19, 2.5)); P(c, () => { c.moveTo(8, 6.5); c.lineTo(16, 6.5); }); [9, 12, 15].forEach((xx) => [11, 14.5, 18].forEach((yy) => dot(c, xx, yy, 1))); },
  tag: (c) => { P(c, () => { c.moveTo(3, 3); c.lineTo(11, 3); c.lineTo(21, 13); c.lineTo(13, 21); c.lineTo(3, 11); c.closePath(); }); dot(c, 7.5, 7.5, 1.5); },
  headset: (c) => { P(c, () => { c.moveTo(4, 15); c.lineTo(4, 12); c.bezierCurveTo(4, 2, 20, 2, 20, 12); c.lineTo(20, 15); }); P(c, () => rr(c, 2.5, 12.5, 4.5, 6.5, 1.5)); P(c, () => rr(c, 17, 12.5, 4.5, 6.5, 1.5)); P(c, () => { c.moveTo(19, 19); c.bezierCurveTo(19, 21, 16, 21.5, 13, 21.5); }); },
  store: (c) => { P(c, () => { c.moveTo(3, 9); c.lineTo(5, 3.5); c.lineTo(19, 3.5); c.lineTo(21, 9); c.lineTo(3, 9); c.moveTo(4.5, 9); c.lineTo(4.5, 20.5); c.lineTo(19.5, 20.5); c.lineTo(19.5, 9); c.moveTo(9.5, 20.5); c.lineTo(9.5, 14.5); c.lineTo(14.5, 14.5); c.lineTo(14.5, 20.5); }); },
  dollar: (c) => { P(c, () => { c.moveTo(12, 2); c.lineTo(12, 22); c.moveTo(17, 6); c.bezierCurveTo(15, 4, 7, 4, 7, 8.5); c.bezierCurveTo(7, 13, 17, 11, 17, 15.5); c.bezierCurveTo(17, 20, 9, 20, 7, 18); }); },
  layers: (c) => { P(c, () => { c.moveTo(12, 3); c.lineTo(21.5, 8); c.lineTo(12, 13); c.lineTo(2.5, 8); c.closePath(); c.moveTo(2.5, 12.5); c.lineTo(12, 17.5); c.lineTo(21.5, 12.5); c.moveTo(2.5, 17); c.lineTo(12, 22); c.lineTo(21.5, 17); }); },
  eye: (c) => { P(c, () => { c.moveTo(2, 12); c.bezierCurveTo(6, 4, 18, 4, 22, 12); c.bezierCurveTo(18, 20, 6, 20, 2, 12); }); P(c, () => c.arc(12, 12, 3, 0, 7)); },
  key: (c) => { P(c, () => c.arc(7.5, 15.5, 4.5, 0, 7)); P(c, () => { c.moveTo(10.8, 12.2); c.lineTo(20, 3); c.moveTo(16, 7); c.lineTo(19, 10); c.moveTo(18.5, 4.5); c.lineTo(21, 7); }); },
  arrow: (c) => { P(c, () => { c.moveTo(4, 12); c.lineTo(20, 12); c.moveTo(14, 6); c.lineTo(20, 12); c.lineTo(14, 18); }); },
  send: (c) => { P(c, () => { c.moveTo(21.5, 2.5); c.lineTo(2.5, 10); c.lineTo(10.5, 13.5); c.lineTo(14, 21.5); c.closePath(); c.moveTo(10.5, 13.5); c.lineTo(21.5, 2.5); }); },
  sparkle: (c) => { P(c, () => { c.moveTo(12, 2); c.bezierCurveTo(12.5, 8, 16, 11.5, 22, 12); c.bezierCurveTo(16, 12.5, 12.5, 16, 12, 22); c.bezierCurveTo(11.5, 16, 8, 12.5, 2, 12); c.bezierCurveTo(8, 11.5, 11.5, 8, 12, 2); c.closePath(); }); },
  menu: (c) => { P(c, () => { c.moveTo(4, 6); c.lineTo(20, 6); c.moveTo(4, 12); c.lineTo(20, 12); c.moveTo(4, 18); c.lineTo(20, 18); }); },
  truck: (c) => { P(c, () => { c.moveTo(2, 5); c.lineTo(14, 5); c.lineTo(14, 17); c.lineTo(2, 17); c.closePath(); c.moveTo(14, 9); c.lineTo(18.5, 9); c.lineTo(22, 13); c.lineTo(22, 17); c.lineTo(14, 17); }); P(c, () => c.arc(6.5, 18, 2, 0, 7)); P(c, () => c.arc(17.5, 18, 2, 0, 7)); },
  calendar: (c) => { P(c, () => rr(c, 3, 4.5, 18, 17, 2.5)); P(c, () => { c.moveTo(3, 9.5); c.lineTo(21, 9.5); c.moveTo(8, 2.5); c.lineTo(8, 6.5); c.moveTo(16, 2.5); c.lineTo(16, 6.5); }); },
};
function rr(c, x, y, w, h, r) { c.moveTo(x + r, y); c.arcTo(x + w, y, x + w, y + h, r); c.arcTo(x + w, y + h, x, y + h, r); c.arcTo(x, y + h, x, y, r); c.arcTo(x, y, x + w, y, r); c.closePath(); }
function dot(c, x, y, r) { c.beginPath(); c.arc(x, y, r, 0, 7); c.fill(); }

// Round icon badge with glow.
export function badge(name, x, y, r, color, o = {}) {
  X.save();
  X.shadowColor = color; X.shadowBlur = o.blur ?? r * 0.9;
  X.beginPath(); X.arc(x, y, r, 0, Math.PI * 2);
  const g = X.createRadialGradient(x, y - r * 0.4, r * 0.1, x, y, r);
  g.addColorStop(0, hexA(color, 0.45)); g.addColorStop(1, hexA(color, 0.12));
  X.fillStyle = g; X.fill();
  X.shadowBlur = 0;
  X.lineWidth = 2; X.strokeStyle = hexA(color, 0.85); X.stroke();
  X.restore();
  icon(name, x, y, r * 1.05, o.iconColor || '#ffffff', o.lw || 2);
}

// Chat bubble: side 'l' (incoming) or 'r' (outgoing). Returns its height.
export function bubble(x, y, maxW, str, side, o = {}) {
  const size = o.size || 26;
  const lines = wrap(str, maxW - size * 1.6, size, 500);
  const lh = size * 1.32;
  let w = 0;
  font(size, 500);
  lines.forEach((l) => (w = Math.max(w, X.measureText(l).width)));
  w += size * 1.6;
  const h = lines.length * lh + size * 1.0;
  const x0 = side === 'r' ? x + maxW - w : x;
  X.save();
  rrect(x0, y, w, h, size * 0.8);
  if (side === 'r') {
    const g = X.createLinearGradient(x0, y, x0 + w, y + h);
    g.addColorStop(0, o.c1 || '#2563eb'); g.addColorStop(1, o.c2 || '#7c3aed');
    X.fillStyle = g;
  } else X.fillStyle = o.fill || 'rgba(255,255,255,0.09)';
  if (o.glow) { X.shadowColor = o.glow; X.shadowBlur = 24; }
  X.fill();
  X.shadowBlur = 0;
  if (side !== 'r') { X.strokeStyle = 'rgba(255,255,255,0.12)'; X.lineWidth = 1.2; X.stroke(); }
  X.restore();
  lines.forEach((l, i) => text(l, x0 + size * 0.8, y + size * 0.5 + lh * (i + 0.5), { size, weight: 500, color: o.color || C.ink }));
  return h;
}

export function typing(x, y, t, color = C.dim, s = 1) {
  for (let i = 0; i < 3; i++) {
    const k = 0.5 + 0.5 * Math.sin(t * 9 - i * 0.9);
    circle(x + i * 16 * s, y - k * 5 * s, 5 * s, hexA('#c7d2fe', 0.35 + k * 0.5));
  }
}

// Number formatting for counters.
export function fmt(v, dec = 0) {
  return v.toLocaleString('en-US', { minimumFractionDigits: dec, maximumFractionDigits: dec });
}
