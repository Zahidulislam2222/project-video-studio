// Scene graphics. Each scene is drawn from its local time and named cues resolved from the
// narration timing, so visuals land on the words that introduce them in both edits.
import {
  C, clamp, lerp, prog, eOut, eInOut, eBack, eExpo, hexA, rng, ctx, withAlpha, withT, text, measure, wrap, para,
  rrect, panel, pill, glowLine, flow, circle, ring, icon, badge, bubble, typing, fmt, along,
} from './kit.js';

// ---------------------------------------------------------------- cue maps
export const CUES = {
  long: {
    hook: { clock: 'b0', ask: 'b1', asleep: 'b2', online: 'b2:store', reply: 'b3', nohuman: 'b4', ai: 'b4:AI' },
    title: { p1: 'b0:customers', p2: 'b0:owners' },
    problem: { qs: 'b0', more: 'b1', repeat: 'b2', hire: 'b3', peak: 'b3:peak', noscale: 'b4' },
    how: { old: 'b0', parts: 'b1', llm: 'b2', kb: 'b3', kbchips: 'b3:Products', tools: 'b4', toolchips: 'b4:inventory', guard: 'b5', handoff: 'b5:handoff', trust: 'b5:trust' },
    customers: { a: 'b0', lang: 'b1:language', b: 'b2', t1: 'b2:track', t2: 'b2:find', t3: 'b2:check', t4: 'b2:book', handoff: 'b3', human: 'b3:human' },
    owners: { a: 'b0', cmd: 'b1', create: 'b1:creates', confirm: 'b1:confirm', docs: 'b2', calc: 'b2:calculate', report: 'b2:report', upd: 'b3', u1: 'b3:price', u2: 'b3:low', u3: 'b3:weekly', sec: 'b4', s1: 'b4:suspicious', s2: 'b4:pending', s3: 'b4:audit', rules: 'b5', daily: 'b5:assistant' },
    proof: { hype: 'b0', kl: 'b1', kl2: 'b1:two-thirds', kl3: 'b1:700', time: 'b2', time2: 'b2:under', study: 'b3', s14: 'b3:14%', s34: 'b3:34%', gartner: 'b4', g80: 'b4:80%' },
    cost: { human: 'b1', double: 'b1:Double', ai: 'b2', fraction: 'b2:fraction', split: 'b3', people: 'b3:people', saving: 'b4', thousand: 'b4:thousand' },
    right: { skip: 'b0', ac: 'b1', pay: 'b1:airline', kl: 'b2', hiring: 'b2:hiring', lesson: 'b3', list: 'b4', l1: 'b4:Ground', l2: 'b4:Limit', l3: 'b4:Ask', l4: 'b4:Log', l5: 'b4:keep', result: 'b5', r1: 'b5:speed', r2: 'b5:lower', r3: 'b5:error' },
    future: { door: 'b0', two: 'b1', owners: 'b1:Owners', flow: 'b2', adopt: 'b3', gap: 'b3:competitors' },
    cta: { pre: 'b0', q: 'b1', site: 'b2', build: 'b2:together' },
  },
  short: {
    hook: { clock: 'b0', ask: 'b0:team', asleep: 'b0:asleep', online: 'b1', reply: 'b1:answering', nohuman: null, ai: null },
    title: { p1: 'b0:app', p2: 'b0:website' },
    customers: { a: 'b0', lang: 'b0:24/7', b: 'b1', t1: 'b1:Order', t2: 'b1:product', t3: 'b1:stock', t4: 'b1:language', handoff: 'b2', human: 'b2:human' },
    owners: { a: 'b0', cmd: 'b1', create: 'b1:describing', confirm: null, docs: 'b2', calc: 'b2:invoices', report: 'b2:reports', upd: 'b3', u1: 'b3:low', u2: 'b3:security', u3: 'b3:automatically', sec: null, rules: 'b4', daily: 'b4:runs' },
    proof: { hype: null, kl: 'b0', kl2: 'b0:two-thirds', kl3: 'b0:700', time: null, study: 'b1', s14: 'b1:14%', s34: null, gartner: 'b2', g80: 'b2:80%' },
    right: { skip: 'b0', ac: 'b1', pay: 'b1:wrong', kl: null, lesson: null, list: 'b2', l1: 'b2:Ground', l2: null, l3: 'b2:confirm', l4: null, l5: 'b2:keep', result: null },
    cta: { pre: null, q: 'b0', site: 'b1', build: 'b1:zahidul' },
  },
};

// 3D world presets per scene (core: x, y, z, scale, opacity).
export const PRESETS = {
  long: {
    hook: { core: [-14, 3, -10, 0.8, 0.55], speed: 4, grid: 0.4, color: '#3b82f6' },
    title: { core: [0, 1.5, 0, 1.25, 1], speed: 10, grid: 0.6 },
    problem: { core: [0, 4, -40, 0.8, 0.35], color: '#f43f5e', color2: '#fb923c', speed: 3, grid: 0.35, shapes: 0.4 },
    how: { core: [0, 2, -30, 0.9, 0.4], speed: 5, grid: 0.4 },
    customers: { core: [16, 4, -20, 0.9, 0.5], color: '#22d3ee', speed: 6 },
    owners: { core: [-16, 4, -25, 0.9, 0.45], color: '#a78bfa', color2: '#22d3ee', speed: 6 },
    proof: { core: [0, 3, -45, 1.1, 0.4], color: '#34d399', color2: '#22d3ee', speed: 5 },
    cost: { core: [14, 6, -40, 0.8, 0.4], color: '#fbbf24', color2: '#34d399', speed: 4 },
    right: { core: [0, 4, -50, 0.9, 0.35], color: '#fbbf24', color2: '#f43f5e', speed: 3, grid: 0.35 },
    future: { core: [0, 1.5, -6, 0.75, 0.55], color: '#22d3ee', speed: 9 },
    cta: { core: [0, 1, 2, 1.3, 1], speed: 7, grid: 0.6 },
  },
  short: {
    hook: { core: [0, 12, -20, 0.8, 0.5], speed: 4, grid: 0.4, color: '#3b82f6' },
    title: { core: [0, 2, 0, 1.0, 1], speed: 10, grid: 0.6 },
    customers: { core: [0, 14, -30, 0.8, 0.45], speed: 6 },
    owners: { core: [0, 14, -30, 0.8, 0.4], color: '#a78bfa', speed: 6 },
    proof: { core: [0, 10, -45, 1, 0.4], color: '#34d399', speed: 5 },
    right: { core: [0, 10, -50, 0.9, 0.35], color: '#fbbf24', color2: '#f43f5e', speed: 3 },
    cta: { core: [0, 4, 0, 1.0, 1], speed: 7, grid: 0.6 },
  },
};

// Scene-specific text that differs between the two edits.
const COPY = {
  long: {
    title: ['Why every app needs', 'an AI chatbot'], titleP: ['Why every app', 'needs an', 'AI chatbot'],
    pills: [['For customers', 'users', C.cyan], ['For owners', 'store', C.violet]],
    tiles: [['truck', 'Track order'], ['search', 'Find product'], ['box', 'Check stock'], ['calendar', 'Book appointment']],
    checklist: ['Ground answers in your real data', 'Limit what it is allowed to do', 'Confirm before important actions', 'Log every action', 'Keep a human one click away'],
  },
  short: {
    title: ['Every app needs', 'an AI chatbot'], titleP: ['Every app', 'needs an', 'AI chatbot'],
    pills: [['Apps', 'layers', C.cyan], ['Websites', 'globe', C.violet]],
    tiles: [['truck', 'Track orders'], ['search', 'Product picks'], ['box', 'Stock checks'], ['globe', 'Any language']],
    checklist: ['Ground it in your own data', null, 'Confirm important actions', null, 'Keep a human one tap away'],
  },
};

// ---------------------------------------------------------------- helpers
const X = () => ctx();
const ap = (S, cue, d = 0.55, delay = 0) => eOut(prog(S.lt, S.q(cue) + delay, d));
const pop = (S, cue, d = 0.5, delay = 0) => eBack(prog(S.lt, S.q(cue) + delay, d));

// Ordered sub-panels inside a scene. Returns {a, off} for the stage keyed `name`.
function stage(S, order, name) {
  const live = order.filter((n) => S.has(n));
  const i = live.indexOf(name);
  if (i < 0) return { a: 0, off: 0, on: false };
  const t0 = i === 0 ? -1 : S.q(name);
  const t1 = i < live.length - 1 ? S.q(live[i + 1]) : Infinity;
  const pin = eOut(prog(S.lt, t0, 0.55));
  const pout = eInOut(prog(S.lt, t1 - 0.3, 0.4));
  return { a: pin * (1 - pout), off: (1 - pin) * 60 - pout * 60, on: pin * (1 - pout) > 0.001 };
}
function inStage(S, st, fn) {
  if (!st.on) return;
  withAlpha(st.a, () => {
    X().save();
    if (S.L.P) X().translate(0, st.off); else X().translate(st.off, 0);
    fn();
    X().restore();
  });
}

function slide(p, fn, dx = 0, dy = 40) {
  if (p <= 0.001) return;
  withAlpha(p, () => { X().save(); X().translate(dx * (1 - p), dy * (1 - p)); fn(); X().restore(); });
}

function heading(S, str, x, y, o = {}) {
  text(str, x, y, { size: o.size || (S.L.P ? 64 : 64), weight: 800, align: o.align || 'center', color: o.color || C.ink, gradient: o.gradient });
}

function kicker(str, x, y, color = C.cyan, align = 'center') {
  text(str.toUpperCase(), x, y, { size: 22, weight: 500, family: 'mono', color, align, letter: 4 });
}

function source(S, str, x, y, p, align = 'center') {
  slide(p, () => {
    const size = S.L.P ? 22 : 20;
    const w = measure(str, size, 500, 'mono') + 50;
    const x0 = align === 'center' ? x - w / 2 : x;
    X().save();
    rrect(x0, y - 20, w, 40, 10);
    X().fillStyle = 'rgba(5,8,22,0.75)'; X().fill();
    X().strokeStyle = 'rgba(148,170,255,0.25)'; X().lineWidth = 1; X().stroke();
    X().restore();
    icon('doc', x0 + 22, y, 18, C.dim, 2);
    text(str, x0 + 38, y + 1, { size, weight: 500, family: 'mono', color: C.dim });
  }, 0, 12);
}

function node(x, y, name, label, color, p, o = {}) {
  if (p <= 0.001) return;
  const r = o.r || 46;
  withAlpha(clamp(p * 1.5), () => {
    withT(x, y, 0.6 + 0.4 * p, () => {
      badge(name, 0, 0, r, color);
      if (label) text(label, 0, r + (o.gap || 30), { size: o.size || 26, weight: 700, align: 'center', color: C.ink });
      if (o.sub) text(o.sub, 0, r + (o.gap || 30) + 32, { size: 20, weight: 500, align: 'center', color: C.dim });
    });
  });
}

function strike(x, y, w, p, color = C.red) {
  if (p <= 0) return;
  glowLine([[x, y], [x + w * eOut(p), y]], color, 5);
}

function stamp(str, x, y, p, color = C.red, size = 64) {
  if (p <= 0) return;
  const s = lerp(1.8, 1, eOut(p));
  withAlpha(clamp(p * 2), () => withT(x, y, s, () => {
    const w = measure(str, size, 800, 'grotesk') + 60;
    X().save();
    X().strokeStyle = color; X().lineWidth = 6; X().shadowColor = color; X().shadowBlur = 20;
    rrect(-w / 2, -size * 0.75, w, size * 1.5, 14); X().stroke();
    X().restore();
    text(str, 0, 4, { size, weight: 700, family: 'grotesk', color, align: 'center', glow: color, blur: 18 });
  }, -0.08));
}

// Simple phone frame; contents drawn by fn in local coordinates (0..w, 0..h).
export function phone(x, y, w, h, fn, o = {}) {
  X().save();
  X().shadowColor = o.glow || 'rgba(59,130,246,0.55)'; X().shadowBlur = 60;
  rrect(x, y, w, h, 56); X().fillStyle = '#0b1028'; X().fill();
  X().shadowBlur = 0;
  X().lineWidth = 6; X().strokeStyle = '#2a3566'; X().stroke();
  rrect(x + 10, y + 10, w - 20, h - 20, 46);
  X().clip();
  const g = X().createLinearGradient(x, y, x, y + h);
  g.addColorStop(0, '#0d1433'); g.addColorStop(1, '#070b1f');
  X().fillStyle = g; X().fillRect(x, y, w, h);
  X().translate(x + 10, y + 10);
  fn(w - 20, h - 20);
  X().restore();
  X().save();
  rrect(x + w / 2 - 60, y + 22, 120, 30, 15); X().fillStyle = '#000'; X().fill();
  X().restore();
}

export function chatHeader(w, title, sub, color = C.green) {
  X().fillStyle = 'rgba(255,255,255,0.04)';
  X().fillRect(0, 0, w, 140);
  badge('bot', 64, 96, 30, C.cyan, { blur: 10 });
  text(title, 112, 84, { size: 28, weight: 700 });
  circle(118, 116, 6, color, { glow: color, blur: 10 });
  text(sub, 132, 117, { size: 20, weight: 500, color: C.dim });
}

// Browser frame with an image scrolled by `scroll` (0..1).
function browser(x, y, w, h, img, url, typed, scroll) {
  X().save();
  X().shadowColor = 'rgba(34,211,238,0.45)'; X().shadowBlur = 70;
  rrect(x, y, w, h, 20); X().fillStyle = '#0d0f14'; X().fill();
  X().shadowBlur = 0; X().strokeStyle = 'rgba(160,190,255,0.35)'; X().lineWidth = 2; X().stroke();
  X().restore();
  const bar = 64;
  [C.red, C.amber, C.green].forEach((c, i) => circle(x + 32 + i * 26, y + bar / 2, 8, c));
  X().save();
  rrect(x + 130, y + 14, w - 260, 36, 18); X().fillStyle = 'rgba(255,255,255,0.07)'; X().fill();
  X().restore();
  icon('lock', x + 156, y + bar / 2, 18, C.green);
  const shown = url.slice(0, Math.round(url.length * typed));
  text(shown, x + 176, y + bar / 2 + 1, { size: 22, weight: 500, family: 'mono', color: C.ink });
  if (img && img.complete) {
    X().save();
    rrect(x + 2, y + bar, w - 4, h - bar - 2, 18); X().clip();
    const scale = (w - 4) / img.width;
    const ih = img.height * scale;
    const maxScroll = Math.max(0, ih - (h - bar));
    X().drawImage(img, x + 2, y + bar - maxScroll * scroll, w - 4, ih);
    X().restore();
  }
}

function personRow(x, y, n, size, color, p, gap = 1.25) {
  for (let i = 0; i < n; i++) {
    const k = clamp(p * n - i);
    if (k <= 0) continue;
    withAlpha(k, () => icon('user', x + i * size * gap, y - (1 - eOut(k)) * 20, size, color, 2.2));
  }
}

// ---------------------------------------------------------------- scenes
export const SCENES = {
  hook(S) {
    const { L, lt } = S;
    const P = L.P;
    // Clock
    const clockP = ap(S, 'clock', 0.8);
    const cx = P ? 540 : 400, cy = P ? 250 : 330;
    slide(clockP, () => {
      icon('moon', cx - (P ? 170 : 170), cy - 4, 56, C.amber, 2.2);
      text('2:00', cx + 10, cy, { size: P ? 120 : 130, weight: 700, family: 'grotesk', align: 'center', glow: C.blue, blur: 30 });
      text('AM', cx + (P ? 150 : 160), cy + 26, { size: 40, weight: 700, family: 'grotesk', color: C.dim });
    });
    // Team / store status cards
    const st = (cue, i, label, val, col, ic) => {
      const p = ap(S, cue, 0.6, i * 0.15);
      const x = P ? 70 + i * 480 : 130;
      const y = P ? 350 : 480 + i * 150;
      const w = P ? 460 : 540;
      slide(p, () => {
        panel(x, y, w, 120, { glow: hexA(col, 0.35), blur: 30 });
        badge(ic, x + 64, y + 60, 34, col);
        text(label, x + 116, y + 44, { size: P ? 24 : 26, weight: 600, color: C.dim });
        text(val, x + 116, y + 82, { size: P ? 32 : 36, weight: 800, color: col });
      }, -30, 0);
    };
    st('asleep', 0, 'Support team', 'Offline', C.red, 'moon');
    st('online', 1, 'Your store', 'Online 24/7', C.green, 'store');

    // Phone with chat
    const pw = P ? 560 : 520, ph = P ? 780 : 820;
    const px = P ? 540 - pw / 2 : 1150, py = P ? 560 : 120;
    const phoneP = eOut(prog(lt, 0.2, 0.9));
    withAlpha(phoneP, () => {
      X().save();
      X().translate(0, (1 - phoneP) * 120);
      phone(px, py, pw, ph, (w, h) => {
        chatHeader(w, 'ShopBot', 'online now');
        let y = 170;
        const askP = ap(S, 'ask', 0.5);
        if (askP > 0) withAlpha(askP, () => { y += bubble(30, y + (1 - askP) * 20, w - 60, 'Is the Classic Hoodie back in stock in size M?', 'r', { size: 25 }) + 18; });
        const rt = S.q('reply');
        if (lt > S.q('ask') + 0.8 && lt < rt + 0.6) withAlpha(1 - prog(lt, rt + 0.3, 0.3), () => { X().save(); rrect(30, y, 110, 52, 26); X().fillStyle = 'rgba(255,255,255,0.09)'; X().fill(); X().restore(); typing(62, y + 26, lt); });
        const r1 = ap(S, 'reply', 0.45, 0.3), r2 = ap(S, 'reply', 0.45, 1.3), r3 = ap(S, 'reply', 0.5, 2.4);
        if (r1 > 0) withAlpha(r1, () => { y += bubble(30, y, w - 70, 'Yes! 14 in stock in size M.', 'l', { size: 25 }) + 14; });
        if (r2 > 0) withAlpha(r2, () => { y += bubble(30, y, w - 70, 'From your past orders, M is your best fit.', 'l', { size: 25 }) + 16; });
        if (r3 > 0) withAlpha(r3, () => {
          const cw = w - 100, chh = 150;
          panel(30, y, cw, chh, { r: 18, glow: hexA(C.cyan, 0.3), blur: 20 });
          X().save(); rrect(46, y + 16, 118, 118, 14); const g = X().createLinearGradient(46, y, 164, y + 134); g.addColorStop(0, '#6366f1'); g.addColorStop(1, '#0ea5e9'); X().fillStyle = g; X().fill(); X().restore();
          icon('tag', 105, y + 75, 54, '#fff');
          text('Classic Hoodie', 184, y + 44, { size: 25, weight: 700 });
          text('$29  ·  Size M', 184, y + 78, { size: 21, weight: 500, color: C.dim });
          X().save(); rrect(184, y + 98, 170, 40, 20); X().fillStyle = C.lime; X().fill(); X().restore();
          text('Checkout  →', 269, y + 119, { size: 20, weight: 800, color: '#0b1020', align: 'center' });
        });
      }, { glow: hexA(C.blue, 0.6) });
      X().restore();
    });
    // Response timer chip
    const tp = ap(S, 'reply', 0.5, 0.2);
    slide(tp, () => {
      const v = Math.min(1.8, Math.max(0, lt - S.q('reply')) * 1.2);
      pill(P ? 540 : px + pw / 2, py - 46, `Answered in ${v.toFixed(1)}s`, { icon: 'bolt', color: C.lime, align: 'center', size: 24, glow: true });
    }, 0, -20);
    // No human involved
    if (S.has('nohuman')) {
      const np = ap(S, 'nohuman', 0.6);
      slide(np, () => {
        const x = P ? 540 : 130, y = P ? 1100 : 810;
        text('0 humans involved.', x, y, { size: P ? 58 : 60, weight: 800, align: P ? 'center' : 'left' });
      }, 0, 30);
      const aip = pop(S, 'ai', 0.7);
      if (aip > 0) withAlpha(clamp(aip), () => {
        const x = P ? 540 : 130, y = P ? 1180 : 880;
        text('Instant. Accurate. Automatic.', x, y, { size: P ? 40 : 40, weight: 700, align: P ? 'center' : 'left', gradient: [C.cyan, C.violet] });
      });
    }
  },

  title(S) {
    const { L, lt } = S;
    const P = L.P;
    const copy = COPY[S.video];
    const lines = P ? copy.titleP : copy.title;
    const size = P ? 112 : 104;
    const y0 = P ? 560 : 430;
    kicker('2026 · The AI era', L.W / 2, y0 - (P ? 150 : 120), C.cyan);
    let wi = 0;
    lines.forEach((line, li) => {
      const words = line.split(' ');
      const total = measure(line, size, 800);
      let x = L.W / 2 - total / 2;
      const last = li === lines.length - 1;
      words.forEach((w) => {
        const ww = measure(w + ' ', size, 800);
        const p = eOut(prog(lt, 0.15 + wi * 0.12, 0.5));
        if (p > 0) withAlpha(p, () => {
          withT(x + measure(w, size, 800) / 2, y0 + li * size * 1.08, lerp(1.35, 1, p), () => {
            text(w, 0, 0, { size, weight: 800, align: 'center', gradient: last ? [C.cyan, C.violet, C.pink] : null, glow: last ? hexA(C.violet, 0.8) : null, blur: 40 });
          });
        });
        x += ww;
        wi++;
      });
    });
    const yb = y0 + lines.length * size * 1.08 + (P ? 40 : 30);
    const pills = copy.pills;
    pills.forEach(([label, ic, col], i) => {
      const p = pop(S, i ? 'p2' : 'p1', 0.6);
      if (p > 0) withAlpha(clamp(p), () => withT(L.W / 2 + (i ? 1 : -1) * (P ? 200 : 220), yb, p, () => pill(0, 0, label, { icon: ic, color: col, align: 'center', size: 32, glow: true })));
    });
  },

  problem(S) {
    const { L, lt } = S;
    const P = L.P;
    const Q = ['Where is my order?', 'How do I reset my password?', 'Do you ship to my country?', 'Can I change my size?', 'Is this in stock?', 'Where is my order?', 'What is your refund policy?', 'How do I reset my password?', 'Where is my order?', 'Do you ship to my country?', 'Is this in stock?', 'Where is my order?'];
    const area = P ? { x: 60, y: 260, w: 960, h: 520 } : { x: 110, y: 170, w: 780, h: 720 };
    kicker('Incoming support tickets', area.x + area.w / 2, area.y - 20, C.red);
    const r = rng(5);
    const t0 = S.q('qs');
    const rep = S.q('repeat');
    const cols = P ? 2 : 2;
    Q.forEach((q, i) => {
      const appear = t0 + 0.3 + i * (S.q('more') + 2.5 - t0) / Q.length;
      const p = eBack(prog(lt, appear, 0.45));
      if (p <= 0) return;
      const col = i % cols, row = Math.floor(i / cols);
      const x = area.x + col * (area.w / cols) + (r() * 30);
      const y = area.y + 40 + row * (P ? 82 : 112) + r() * 10;
      const repeated = /order|password/.test(q);
      const hi = repeated ? eOut(prog(lt, rep, 0.5)) : 0;
      const dimmed = 1 - 0.55 * eOut(prog(lt, rep, 0.5)) * (repeated ? 0 : 1);
      withAlpha(clamp(p) * dimmed, () => withT(x, y, 0.85 + 0.15 * p, () => {
        X().save();
        const w = measure(q, 24, 500) + 60;
        if (hi > 0) { X().shadowColor = C.red; X().shadowBlur = 24 * hi; }
        rrect(0, -28, w, 56, 18);
        X().fillStyle = hi > 0 ? hexA(C.red, 0.12 + 0.12 * hi) : 'rgba(255,255,255,0.08)';
        X().fill();
        X().shadowBlur = 0;
        X().strokeStyle = hi > 0 ? hexA(C.red, 0.7) : 'rgba(255,255,255,0.14)'; X().lineWidth = 1.5; X().stroke();
        X().restore();
        icon('user', 26, 0, 22, C.dim);
        text(q, 46, 1, { size: 24, weight: 500 });
      }));
    });
    // Repeat counters
    const rp = pop(S, 'repeat', 0.6, 0.3);
    if (rp > 0) {
      [['Where is my order?', '× 3,120'], ['Reset password', '× 1,870']].forEach(([lab, n], i) => {
        withAlpha(clamp(rp), () => withT(area.x + area.w / 2 + (i ? 1 : -1) * (P ? 240 : 200), area.y + area.h - (P ? 10 : 40), rp, () => {
          pill(0, 0, n, { color: C.red, align: 'center', size: 30, solid: true });
          text(lab, 0, 46, { size: 20, weight: 500, align: 'center', color: C.dim });
        }));
      });
    }
    // Ticket counter
    const cnt = Math.round(clamp((lt - t0) / Math.max(1, S.q('hire') - t0)) * 4980);
    text(`${fmt(cnt)} tickets today`, area.x + area.w / 2, area.y + area.h + (P ? 70 : 60), { size: 30, weight: 700, family: 'grotesk', color: C.ink, align: 'center' });

    // Cost chart
    const hp = ap(S, 'hire', 0.6);
    if (hp <= 0) return;
    const ch = P ? { x: 140, y: 920, w: 840, h: 300 } : { x: 1030, y: 220, w: 760, h: 560 };
    withAlpha(hp, () => {
      panel(ch.x - 80, ch.y - 70, ch.w + 120, ch.h + 150, { glow: hexA(C.red, 0.2) });
      text('Support cost vs. traffic', ch.x - 40, ch.y - 30, { size: 26, weight: 700 });
      glowLine([[ch.x, ch.y + 10], [ch.x, ch.y + ch.h], [ch.x + ch.w, ch.y + ch.h]], 'rgba(255,255,255,0.35)', 2, { blur: 0 });
      text('Traffic →', ch.x + ch.w, ch.y + ch.h + 34, { size: 20, weight: 500, color: C.dim, align: 'right' });
      const lp = eInOut(prog(lt, S.q('hire') + 0.3, 2.6));
      const pts = [[ch.x, ch.y + ch.h - 10], [ch.x + ch.w * lp, ch.y + ch.h - 10 - (ch.h - 30) * lp]];
      glowLine(pts, C.red, 5);
      const n = Math.floor(lp * 7);
      for (let i = 0; i < n; i++) {
        const f = (i + 1) / 7.5;
        icon('user', ch.x + ch.w * f, ch.y + ch.h - 10 - (ch.h - 30) * f - 34, 30, C.ink, 2.2);
      }
      text('+ hire', ch.x + ch.w * lp + 14, ch.y + ch.h - (ch.h - 30) * lp - 10, { size: 22, weight: 700, color: C.red });
      const pk = ap(S, 'peak', 0.5);
      if (pk > 0) withAlpha(pk, () => {
        pill(ch.x + 20, ch.y + 40, 'Peak hours: slow replies', { icon: 'clock', color: C.amber, size: 22 });
      });
    });
    stamp("DOESN'T SCALE", P ? 540 : 1410, P ? 1070 : 520, prog(lt, S.q('noscale'), 0.45), C.red, P ? 72 : 72);
  },

  how(S) {
    const { L, lt } = S;
    const P = L.P;
    // Old menu bot (beat 0)
    const op = 1 - eInOut(prog(lt, S.q('parts') - 0.2, 0.5));
    withAlpha(op * eOut(prog(lt, 0.3, 0.6)), () => {
      const x = L.W / 2 - 260, y = P ? 480 : 260;
      panel(x, y, 520, 470, { glow: 'rgba(148,163,184,0.25)' });
      text('Old menu bot', x + 40, y + 56, { size: 30, weight: 700, color: C.dim });
      ['1  Orders', '2  Returns', '3  Talk to sales', '4  Other'].forEach((b, i) => {
        X().save(); rrect(x + 40, y + 100 + i * 82, 440, 62, 12); X().fillStyle = 'rgba(148,163,184,0.12)'; X().fill(); X().restore();
        text(b, x + 66, y + 132 + i * 82, { size: 26, weight: 600, family: 'mono', color: '#cbd5e1' });
      });
      const sp = prog(lt, 2.4, 0.5);
      if (sp > 0) { glowLine([[x - 20, y - 20], [x - 20 + 560 * eOut(sp), y - 20 + 510 * eOut(sp)]], C.red, 7); }
      text('Fixed buttons only', L.W / 2, y + 520, { size: 26, weight: 600, color: C.red, align: 'center' });
    });
    if (lt < S.q('parts') - 0.3) return;
    // Architecture
    const G = P
      ? { user: [200, 330], human: [880, 330], hub: [540, 560], llm: [190, 830], kb: [540, 830], tools: [890, 830], chipY: 960 }
      : { user: [210, 470], human: [210, 790], hub: [720, 470], llm: [1240, 230], kb: [1240, 470], tools: [1240, 710], chipX: 1360 };
    const base = S.q('parts');
    const hubP = eBack(prog(lt, base, 0.6));
    const userP = eOut(prog(lt, base + 0.3, 0.5));
    node(...G.user, 'user', 'User', C.ink, userP, { r: 44 });
    flow([G.user, G.hub], lt, base + 0.5, C.cyan, { packets: 2, speed: 0.7 });
    const comps = [['llm', 'brain', 'Language model', C.violet, 'llm'], ['kb', 'db', 'Knowledge base', C.cyan, 'kb'], ['tools', 'wrench', 'Tools & actions', C.lime, 'tools']];
    comps.forEach(([k, ic, label, col, cue]) => {
      const t0 = S.q(cue);
      const p = eBack(prog(lt, t0, 0.6));
      const hint = eOut(prog(lt, base + 0.6, 0.6)) * 0.25;
      const from = G.hub, to = G[k];
      const mid = P ? [[from[0], from[1] + 120], [to[0], from[1] + 120], to] : [[from[0] + 200, from[1]], [from[0] + 200, to[1]], to];
      const pts = [from, ...mid];
      if (p <= 0) {
        withAlpha(hint, () => { glowLine(pts, hexA(col, 0.6), 2, { dash: [8, 10], blur: 0 }); circle(...to, 46, null, { stroke: hexA(col, 0.6), lw: 2 }); });
      } else {
        flow(pts, lt, t0, col, { packets: 2, speed: 0.55 });
        node(...to, ic, label, col, p, { r: 50, size: P ? 24 : 26 });
      }
    });
    node(...G.hub, 'bot', 'AI chatbot', C.cyan, hubP, { r: 68, size: 30 });
    // Chips
    const chipsAt = (list, cue, col, ox, oy) => list.forEach((c, i) => {
      const p = pop(S, cue, 0.45, i * 0.25);
      if (p <= 0) return;
      withAlpha(clamp(p), () => {
        if (P) pill(ox, oy + i * 54, c, { color: col, align: 'center', size: 20 });
        else pill(ox, oy + i * 0 , c, { color: col, size: 20 });
      });
    });
    if (P) {
      chipsAt(['Understands intent'], 'llm', C.violet, G.llm[0], G.chipY);
      chipsAt(['Products', 'Policies', 'Documents'], 'kbchips', C.cyan, G.kb[0], G.chipY);
      chipsAt(['Inventory', 'Orders', 'Payments', 'Admin'], 'toolchips', C.lime, G.tools[0], G.chipY);
    } else {
      const row = (list, cue, col, y) => { let x = G.chipX + 60; list.forEach((c, i) => { const p = pop(S, cue, 0.45, i * 0.25); if (p > 0) withAlpha(clamp(p), () => pill(x, y, c, { color: col, size: 20 })); x += measure(c, 20) + 50; }); };
      row(['Understands intent'], 'llm', C.violet, G.llm[1]);
      row(['Products', 'Policies', 'Docs'], 'kbchips', C.cyan, G.kb[1]);
      row(['Inventory', 'Orders', 'Payments', 'Admin'], 'toolchips', C.lime, G.tools[1]);
    }
    // Guardrails frame
    const gp = eOut(prog(lt, S.q('guard'), 0.9));
    if (gp > 0) {
      const r = P ? { x: 40, y: 450, w: 1000, h: 700 } : { x: 560, y: 130, w: 1335, h: 720 };
      withAlpha(gp, () => {
        X().save();
        X().setLineDash([14, 10]); X().lineDashOffset = -lt * 30;
        X().strokeStyle = C.amber; X().lineWidth = 3; X().shadowColor = C.amber; X().shadowBlur = 16;
        rrect(r.x, r.y, r.w, r.h, 30); X().stroke();
        X().restore();
        X().save(); rrect(r.x + 24, r.y - 24, measure('Guardrails · Permissions · Audit log', 22) + 80, 48, 24); X().fillStyle = '#0a0f2a'; X().fill(); X().restore();
        pill(r.x + 30, r.y, 'Guardrails · Permissions · Audit log', { icon: 'shield', color: C.amber, size: 22, solid: false });
      });
    }
    const hp = eOut(prog(lt, S.q('handoff'), 0.6));
    if (hp > 0) {
      const pts = P ? [G.hub, [G.hub[0] + 200, G.hub[1] - 120], G.human] : [G.hub, [G.hub[0], G.human[1]], G.human];
      flow(pts, lt, S.q('handoff'), C.pink, { packets: 1, speed: 0.5, width: 3 });
      node(...G.human, 'headset', 'Human handoff', C.pink, hp, { r: 44, size: 24 });
    }
    const tp = pop(S, 'trust', 0.6);
    if (tp > 0) withAlpha(clamp(tp), () => withT(P ? 540 : 720, P ? 1215 : 905, tp, () => pill(0, 0, 'An assistant you can trust', { icon: 'shieldcheck', color: C.green, align: 'center', size: 26, glow: true })));
  },

  customers(S) {
    const { L, lt } = S;
    const P = L.P;
    const copy = COPY[S.video];
    const order = ['a', 'b', 'handoff'];
    // A: 24/7 + languages
    inStage(S, stage(S, order, 'a'), () => {
      const cx = P ? 540 : 660, cy = P ? 620 : 500;
      const rp = eOut(prog(lt, 0.2, 1.4));
      ring(cx, cy, 190, rp, C.cyan, 16);
      for (let i = 0; i < 24; i++) {
        const a = (i / 24) * Math.PI * 2 - Math.PI / 2;
        const on = i / 24 < rp;
        circle(cx + Math.cos(a) * 235, cy + Math.sin(a) * 235, 5, on ? C.cyan : 'rgba(255,255,255,0.15)', on ? { glow: C.cyan, blur: 10 } : {});
      }
      text('24/7', cx, cy - 6, { size: 120, weight: 700, family: 'grotesk', align: 'center', glow: C.cyan, blur: 30 });
      text('always on', cx, cy + 70, { size: 26, weight: 600, align: 'center', color: C.dim });
      const lp = ap(S, 'lang', 0.5);
      const langs = [['Hello', 'English'], ['Hola', 'Español'], ['Bonjour', 'Français'], ['Hallo', 'Deutsch'], ['Olá', 'Português'], ['Ciao', 'Italiano']];
      langs.forEach(([hi, name], i) => {
        const p = eBack(prog(lt, S.q('lang') + i * 0.15, 0.5));
        if (p <= 0) return;
        const x = P ? 120 + (i % 3) * 300 : 1080 + (i % 2) * 340;
        const y = P ? 960 + Math.floor(i / 3) * 130 : 270 + Math.floor(i / 2) * 150;
        withAlpha(clamp(p) * lp, () => withT(x + 130, y, p, () => {
          panel(-130, -50, 260, 100, { r: 20 });
          text(hi, 0, -10, { size: 34, weight: 800, align: 'center' });
          text(name, 0, 26, { size: 18, weight: 500, align: 'center', color: C.dim, family: 'mono' });
        }));
      });
    });
    // B: use-case tiles
    inStage(S, stage(S, order, 'b'), () => {
      const tiles = copy.tiles;
      const cue = ['t1', 't2', 't3', 't4'];
      tiles.forEach(([ic, label], i) => {
        const k = cue[i];
        const p = eBack(prog(lt, S.has(k) ? S.q(k) : S.q('b') + 0.4 + i * 0.4, 0.55));
        if (p <= 0) return;
        const col = [C.cyan, C.violet, C.lime, C.pink][i];
        const x = P ? 70 + (i % 2) * 480 : 140 + i * 420;
        const y = P ? 300 + Math.floor(i / 2) * 330 : 300;
        const w = P ? 460 : 390, h = P ? 300 : 360;
        withAlpha(clamp(p), () => withT(x + w / 2, y + h / 2, 0.8 + 0.2 * p, () => {
          panel(-w / 2, -h / 2, w, h, { glow: hexA(col, 0.35), blur: 40 });
          badge(ic, 0, -h / 2 + (P ? 100 : 120), P ? 56 : 62, col);
          text(label, 0, h / 2 - (P ? 70 : 90), { size: P ? 32 : 32, weight: 800, align: 'center' });
          text('no queue', 0, h / 2 - (P ? 32 : 48), { size: 20, weight: 500, align: 'center', color: C.dim, family: 'mono' });
        }));
      });
      const qp = ap(S, 'b', 0.6, 1.0);
      slide(qp, () => pill(L.W / 2, P ? 1000 : 780, 'Answered instantly, no waiting line', { icon: 'bolt', color: C.lime, align: 'center', size: 26 }), 0, 20);
    });
    // C: handoff
    inStage(S, stage(S, order, 'handoff'), () => {
      const a = P ? [540, 380] : [380, 480];
      const b = P ? [540, 1010] : [1540, 480];
      const t0 = S.q('handoff');
      node(...a, 'bot', 'AI chatbot', C.cyan, eBack(prog(lt, t0, 0.6)), { r: 70, size: 30 });
      const hp = eBack(prog(lt, S.q('human'), 0.6));
      const pts = [[a[0] + (P ? 0 : 100), a[1] + (P ? 110 : 0)], [b[0] - (P ? 0 : 100), b[1] - (P ? 110 : 0)]];
      flow(pts, lt, t0 + 0.4, C.pink, { packets: 3, speed: 0.6, width: 4 });
      node(...b, 'headset', 'Human agent', C.pink, hp, { r: 70, size: 30 });
      // Context card travelling along
      const cp = eOut(prog(lt, t0 + 0.6, 0.6));
      if (cp > 0) {
        const m = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
        withAlpha(cp, () => {
          const w = 470, h = 190;
          panel(m[0] - w / 2, m[1] - h / 2 - (P ? 0 : 150), w, h, { glow: hexA(C.pink, 0.35) });
          const y = m[1] - h / 2 - (P ? 0 : 150);
          text('Full context transferred', m[0] - w / 2 + 30, y + 44, { size: 26, weight: 800 });
          ['Order #48213 · delayed', 'Customer upset · priority', 'Steps already tried: 3'].forEach((s, i) => {
            const ip = ap(S, 'handoff', 0.4, 0.9 + i * 0.35);
            withAlpha(ip, () => { icon('check', m[0] - w / 2 + 44, y + 92 + i * 34, 22, C.green, 3); text(s, m[0] - w / 2 + 68, y + 92 + i * 34, { size: 21, weight: 500, color: C.dim }); });
          });
        });
      }
      const np = ap(S, 'human', 0.6, 0.6);
      slide(np, () => text('Nobody repeats themselves.', L.W / 2, P ? 1200 : 820, { size: 40, weight: 800, align: 'center', gradient: [C.pink, C.violet] }), 0, 20);
    });
  },

  owners(S) {
    const { L, lt } = S;
    const P = L.P;
    const order = ['a', 'docs', 'upd', 'sec', 'rules'];
    // Dashboard (talk to admin panel + product upload)
    inStage(S, stage(S, order, 'a'), () => {
      const d = P ? { x: 50, y: 270, w: 980, h: 930 } : { x: 120, y: 140, w: 1680, h: 760 };
      panel(d.x, d.y, d.w, d.h, { glow: hexA(C.violet, 0.3), r: 26 });
      // Top bar
      text('Admin console', d.x + 40, d.y + 46, { size: 26, weight: 800 });
      pill(d.x + d.w - 30, d.y + 46, 'AI assistant on', { icon: 'sparkle', color: C.violet, align: 'right', size: 20 });
      glowLine([[d.x, d.y + 90], [d.x + d.w, d.y + 90]], 'rgba(255,255,255,0.1)', 1, { blur: 0 });
      // Chat input
      const ix = d.x + 30, iw = P ? d.w - 60 : 620, iy = P ? d.y + 120 : d.y + d.h - 110;
      const cmd = 'Add 20 hoodies, sizes S to XL, at $29';
      const tp = prog(lt, S.q('cmd') + 0.2, 2.2);
      X().save(); rrect(ix, iy, iw, 76, 38); X().fillStyle = 'rgba(255,255,255,0.06)'; X().fill(); X().strokeStyle = hexA(C.violet, 0.6); X().lineWidth = 2; X().stroke(); X().restore();
      const shown = tp > 0 ? cmd.slice(0, Math.round(cmd.length * tp)) : '';
      text(shown || 'Tell your store what to do…', ix + 34, iy + 39, { size: P ? 26 : 25, weight: 500, color: shown ? C.ink : C.faint, family: shown ? 'inter' : 'inter' });
      if (tp > 0 && tp < 1 && Math.floor(lt * 3) % 2 === 0) text('|', ix + 34 + measure(shown, P ? 26 : 25, 500), iy + 37, { size: 28, color: C.violet });
      circle(ix + iw - 38, iy + 38, 26, C.violet, { glow: C.violet, blur: 16 });
      icon('send', ix + iw - 39, iy + 39, 26, '#fff');
      // Left: assistant log (landscape)
      const logX = ix, logY = d.y + 130;
      const gp = ap(S, 'a', 0.5, 0.8) * (1 - ap(S, 'cmd', 0.3, 0.3));
      if (gp > 0) withAlpha(gp, () => bubble(P ? d.x + 40 : logX, P ? d.y + 300 : logY, P ? 880 : 600, 'Hi! I can add products, update prices, read invoices and check security. What should I do?', 'l', { size: 25 }));
      if (!P) {
        const lines = [['Understood: 20 × Classic Hoodie', 'create', 0], ['Sizes S, M, L, XL · $29 each', 'create', 0.4], ['Stock set: 5 per size', 'create', 0.8], ['Publish 20 listings?', 'confirm', 0]];
        lines.forEach(([s, cue, dl], i) => {
          const p = ap(S, S.has(cue) ? cue : 'create', 0.45, S.has(cue) ? dl : 1.8);
          if (p <= 0) return;
          withAlpha(p, () => { badge(i === 3 ? 'alert' : 'check', logX + 26, logY + 30 + i * 84, 22, i === 3 ? C.amber : C.green, { blur: 8 }); text(s, logX + 64, logY + 31 + i * 84, { size: 25, weight: 600 }); });
        });
      }
      // Product grid
      const gx = P ? d.x + 40 : d.x + 720, gy = P ? d.y + 270 : d.y + 150, gw = P ? d.w - 80 : d.w - 760;
      const cols = 5, rows = 4, gap = 14;
      const cw = (gw - gap * (cols - 1)) / cols, chh = P ? 120 : 125;
      const sizes = ['S', 'M', 'L', 'XL'];
      const hues = ['#6366f1', '#0ea5e9', '#8b5cf6', '#ec4899', '#14b8a6'];
      const ct = S.q('create');
      for (let i = 0; i < 20; i++) {
        const p = eBack(prog(lt, ct + i * 0.06, 0.45));
        const c = i % cols, r = Math.floor(i / cols);
        const x = gx + c * (cw + gap), y = gy + r * (chh + gap);
        if (p <= 0) {
          X().save(); rrect(x, y, cw, chh, 14); X().fillStyle = 'rgba(255,255,255,0.025)'; X().fill(); X().strokeStyle = 'rgba(160,190,255,0.16)'; X().setLineDash([6, 6]); X().stroke(); X().restore();
          continue;
        }
        withAlpha(clamp(p), () => withT(x + cw / 2, y + chh / 2 - (1 - clamp(p)) * 60, 0.7 + 0.3 * p, () => {
          X().save(); rrect(-cw / 2, -chh / 2, cw, chh, 14); X().fillStyle = 'rgba(255,255,255,0.07)'; X().fill(); X().restore();
          X().save(); rrect(-cw / 2 + 10, -chh / 2 + 10, cw - 20, chh * 0.48, 10); X().fillStyle = hues[c]; X().globalAlpha *= 0.8; X().fill(); X().restore();
          icon('tag', 0, -chh / 2 + 10 + chh * 0.24, 30, '#fff');
          text(`Hoodie · ${sizes[r]}`, -cw / 2 + 12, chh / 2 - 38, { size: 17, weight: 700 });
          text('$29  ·  5 in stock', -cw / 2 + 12, chh / 2 - 16, { size: 15, weight: 500, color: C.dim });
        }));
      }
      const made = Math.round(20 * clamp((lt - ct) / 1.6));
      text(`Products  ${made}`, gx, gy - 30, { size: 22, weight: 700, family: 'mono', color: made ? C.lime : C.dim });
      // Confirm dialog
      const cfT = S.has('confirm') ? S.q('confirm') : ct + 2.2;
      const cp = eBack(prog(lt, cfT, 0.55));
      const okP = prog(lt, cfT + 1.3, 0.3);
      if (cp > 0) withAlpha(clamp(cp), () => withT(gx + gw / 2, gy + (chh + gap) * 2 - gap / 2, cp, () => {
        panel(-250, -95, 500, 190, { glow: hexA(C.amber, 0.5), fill: 'rgba(12,16,40,0.97)', fill2: 'rgba(30,38,80,0.97)' });
        text('Publish 20 listings?', 0, -42, { size: 30, weight: 800, align: 'center' });
        X().save(); rrect(-200, 0, 180, 60, 30); X().fillStyle = 'rgba(255,255,255,0.08)'; X().fill(); X().restore();
        text('Review', -110, 31, { size: 22, weight: 600, align: 'center', color: C.dim });
        X().save(); rrect(20, 0, 180, 60, 30); X().fillStyle = okP > 0 ? C.green : C.lime; X().shadowColor = C.green; X().shadowBlur = 20 * okP; X().fill(); X().restore();
        text(okP > 0 ? 'Published ✓' : 'Confirm', 110, 31, { size: 22, weight: 800, align: 'center', color: '#0b1020' });
      }));
      if (P) {
        const kp = ap(S, 'create', 0.5, 0.2);
        slide(kp, () => pill(540, d.y + d.h - 60, 'Listings + stock created from one sentence', { icon: 'sparkle', color: C.violet, align: 'center', size: 22 }), 0, 20);
      }
    });
    // Documents -> calculations -> report
    inStage(S, stage(S, order, 'docs'), () => {
      const t0 = S.q('docs');
      const A = P ? [540, 470] : [380, 500];
      const B = P ? [540, 900] : [1380, 500];
      // Invoice doc
      const dp = eOut(prog(lt, t0, 0.6));
      withAlpha(dp, () => {
        const w = P ? 520 : 440, h = P ? 330 : 520;
        const x = A[0] - w / 2, y = A[1] - h / 2;
        panel(x, y, w, h, { glow: hexA(C.cyan, 0.3) });
        icon('doc', x + 46, y + 50, 34, C.cyan);
        text('INVOICE  #2041', x + 80, y + 50, { size: 24, weight: 700, family: 'mono' });
        const items = [['Hoodies × 120', 3480], ['Caps × 300', 4200], ['Jackets × 64', 4800]];
        items.forEach(([n, v], i) => {
          const ip = ap(S, 'docs', 0.4, 0.3 + i * 0.25);
          const scan = P ? 0 : 0;
          withAlpha(ip, () => {
            text(n, x + 40, y + 120 + i * (P ? 52 : 70) + scan, { size: 24, weight: 500, color: C.dim });
            text('$' + fmt(v), x + w - 40, y + 120 + i * (P ? 52 : 70), { size: 24, weight: 700, align: 'right', family: 'mono' });
          });
        });
        // Scan line
        const sl = (lt - t0) % 2 / 2;
        if (lt > t0 + 0.5) glowLine([[x + 16, y + 80 + sl * (h - 100)], [x + w - 16, y + 80 + sl * (h - 100)]], hexA(C.cyan, 0.8), 2);
      });
      // Calculation panel
      const cp = eOut(prog(lt, S.q('calc'), 0.6));
      const mid = P ? [540, 700] : [880, 500];
      if (cp > 0) {
        flow([[A[0] + (P ? 0 : 230), A[1] + (P ? 170 : 0)], [B[0] - (P ? 0 : 290), B[1] - (P ? 190 : 0)]], lt, S.q('calc'), C.violet, { packets: 3 });
        withAlpha(cp, () => withT(...mid, 0.85 + 0.15 * cp, () => badge('calc', 0, 0, 52, C.violet)));
      }
      const rp = eOut(prog(lt, S.q('calc') + 0.4, 0.6));
      if (rp > 0) withAlpha(rp, () => {
        const w = P ? 600 : 520, h = P ? 330 : 520;
        const x = B[0] - w / 2, y = B[1] - h / 2;
        panel(x, y, w, h, { glow: hexA(C.lime, 0.3) });
        text('Report', x + 40, y + 50, { size: 28, weight: 800 });
        const k = eOut(prog(lt, S.q('calc') + 0.4, 1.8));
        const rows = [['Subtotal', 12480 * k], ['Tax (8%)', 998.4 * k], ['Total', 13478.4 * k], ['Margin', null]];
        rows.forEach(([n, v], i) => {
          const yy = y + 105 + i * (P ? 50 : 60);
          text(n, x + 40, yy, { size: 24, weight: 500, color: C.dim });
          text(v == null ? `${Math.round(34 * k)}%` : '$' + fmt(v, 2), x + (P ? 330 : w - 40), yy, { size: 25, weight: 700, family: 'mono', align: 'right', color: i === 2 ? C.lime : C.ink });
        });
        // bars
        const bp = eOut(prog(lt, S.q('report'), 0.9));
        const bx = P ? x + 380 : x + 40, by = P ? y + 280 : y + h - 40;
        [0.45, 0.62, 0.55, 0.8, 0.95].forEach((v, i) => {
          const bh = (P ? 190 : 150) * v * bp;
          X().save(); rrect(bx + i * (P ? 40 : 90), by - bh, P ? 26 : 60, bh, 6);
          const g = X().createLinearGradient(0, by - bh, 0, by); g.addColorStop(0, C.lime); g.addColorStop(1, hexA(C.cyan, 0.4)); X().fillStyle = g; X().fill(); X().restore();
        });
      });
    });
    // Regular updates
    inStage(S, stage(S, order, 'upd'), () => {
      const cards = [
        ['u1', 'tag', C.cyan, S.video === 'short' ? 'Low stock: Runner Cap, 3 left' : 'Price updated: Classic Hoodie $32 → $29', S.video === 'short' ? 'Reorder draft prepared' : 'Applied to web + app'],
        ['u2', 'alert', C.amber, S.video === 'short' ? 'Security warning: new-device login' : 'Low stock: Runner Cap, 3 left', S.video === 'short' ? 'Blocked until owner approves' : 'Reorder draft prepared'],
        ['u3', 'chart', C.lime, 'Weekly summary is ready', 'Sent every Monday at 9:00'],
      ];
      kicker('Automatic updates · demo data', L.W / 2, P ? 300 : 190, C.dim);
      cards.forEach(([cue, ic, col, title, sub], i) => {
        const p = eOut(prog(lt, S.q(cue) + (S.video === 'short' && i === 0 ? 0 : 0), 0.55));
        if (p <= 0) return;
        const w = P ? 940 : 1100, h = P ? 200 : 170;
        const x = L.W / 2 - w / 2 + (1 - p) * 200, y = (P ? 380 : 260) + i * (h + 36);
        withAlpha(p, () => {
          panel(x, y, w, h, { glow: hexA(col, 0.35) });
          badge(ic, x + 90, y + h / 2, 48, col);
          text(title, x + 170, y + h / 2 - 22, { size: P ? 32 : 34, weight: 800 });
          text(sub, x + 170, y + h / 2 + 26, { size: 24, weight: 500, color: C.dim });
          if (!P) text('just now', x + w - 40, y + h / 2, { size: 20, weight: 500, family: 'mono', color: C.faint, align: 'right' });
        });
      });
    });
    // Security
    inStage(S, stage(S, order, 'sec'), () => {
      const c = P ? [540, 560] : [520, 510];
      const t0 = S.q('sec');
      const sp = eBack(prog(lt, t0, 0.7));
      // radar
      for (let i = 1; i <= 3; i++) circle(...c, 90 * i, null, { stroke: hexA(C.green, 0.25), lw: 2 });
      const a = lt * 2.2;
      X().save();
      const g = X().createConicGradient ? X().createConicGradient(a, ...c) : null;
      if (g) { g.addColorStop(0, hexA(C.green, 0.35)); g.addColorStop(0.15, hexA(C.green, 0)); g.addColorStop(1, hexA(C.green, 0)); X().fillStyle = g; X().beginPath(); X().arc(...c, 270, 0, Math.PI * 2); X().fill(); }
      X().restore();
      withT(...c, Math.max(0, sp), () => badge('shieldcheck', 0, 0, 80, C.green));
      const ev = [['s1', 'eye', C.red, 'Suspicious login flagged', 'New device · approval required'], ['s2', 'refresh', C.amber, '2 security updates pending', 'Reminder sent to owner'], ['s3', 'layers', C.cyan, 'Audit log', 'Every action recorded']];
      ev.forEach(([cue, ic, col, title, sub], i) => {
        const p = eOut(prog(lt, S.q(cue), 0.5));
        if (p <= 0) return;
        const w = P ? 900 : 860, h = 140;
        const x = P ? 90 : 900 + (1 - p) * 120, y = P ? 900 + i * 0 : 270 + i * 175;
        if (P && i > 0) return;
        withAlpha(p, () => {
          panel(x, y, w, h, { glow: hexA(col, 0.35) });
          badge(ic, x + 75, y + h / 2, 40, col);
          text(title, x + 140, y + h / 2 - 20, { size: 30, weight: 800 });
          text(sub, x + 140, y + h / 2 + 24, { size: 22, weight: 500, color: C.dim });
        });
      });
      if (P) {
        [['s2', '2 updates pending'], ['s3', 'Audit log: every action']].forEach(([cue, s], i) => {
          const p = pop(S, cue, 0.5);
          if (p > 0) withAlpha(clamp(p), () => pill(540, 1080 + i * 70, s, { color: i ? C.cyan : C.amber, align: 'center', size: 24 }));
        });
      }
    });
    // Rules loop
    inStage(S, stage(S, order, 'rules'), () => {
      const t0 = S.q('rules');
      const c = P ? [540, 700] : [960, 500];
      const R = P ? 300 : 260;
      const rp = eOut(prog(lt, t0, 1.0));
      ring(...c, R, rp, C.violet, 6);
      const items = [['gear', 'Your rules'], ['bot', 'AI runs them'], ['check', 'Done'], ['chart', 'Report']];
      items.forEach(([ic, label], i) => {
        const a = (i / items.length) * Math.PI * 2 - Math.PI / 2;
        const p = eBack(prog(lt, t0 + 0.2 + i * 0.3, 0.5));
        node(c[0] + Math.cos(a) * R, c[1] + Math.sin(a) * R, ic, label, [C.violet, C.cyan, C.green, C.lime][i], p, { r: 46, size: 24 });
      });
      if (rp >= 1) {
        const f = ((lt - t0) * 0.35) % 1;
        const a = f * Math.PI * 2 - Math.PI / 2;
        circle(c[0] + Math.cos(a) * R, c[1] + Math.sin(a) * R, 10, '#fff', { glow: C.violet, blur: 20 });
      }
      const dp = ap(S, 'daily', 0.6);
      withAlpha(dp, () => {
        text('Set once.', c[0], c[1] - 24, { size: 52, weight: 800, align: 'center' });
        text('Runs every day.', c[0], c[1] + 40, { size: 40, weight: 800, align: 'center', gradient: [C.cyan, C.violet] });
      });
    });
  },

  proof(S) {
    const { L, lt } = S;
    const P = L.P;
    const order = ['hype', 'kl', 'time', 'study', 'gartner'];
    inStage(S, stage(S, order, 'hype'), () => {
      const g = Math.sin(lt * 40) * (lt < 0.6 ? 6 : 0);
      text('Real', L.W / 2 - 230 + g, L.H / 2 - (P ? 200 : 40), { size: 140, weight: 800, align: 'center', color: C.green, glow: C.green, blur: 40 });
      text('or', L.W / 2, L.H / 2 - (P ? 200 : 40), { size: 60, weight: 600, align: 'center', color: C.dim });
      text('hype?', L.W / 2 + 250 - g, L.H / 2 - (P ? 200 : 40), { size: 140, weight: 800, align: 'center', color: C.pink, glow: C.pink, blur: 40 });
      const np = ap(S, 'hype', 0.6, 1.6);
      slide(np, () => pill(L.W / 2, L.H / 2 + (P ? -40 : 120), "Let's look at the numbers", { icon: 'bars', color: C.cyan, align: 'center', size: 30 }), 0, 20);
    });
    inStage(S, stage(S, order, 'kl'), () => {
      kicker('Klarna AI assistant · first month', L.W / 2, P ? 290 : 180, C.green);
      const cards = [
        ['kl', 2.3, 1, 'M', 'conversations handled', C.cyan, 'chat'],
        ['kl2', 2, 0, '/3', 'of customer service chats', C.violet, 'pie'],
        ['kl3', 700, 0, '', 'full-time agents of work', C.lime, 'users'],
      ];
      cards.forEach(([cue, v, dec, suf, label, col, ic], i) => {
        const t = S.q(cue) + (i === 0 ? 0.6 : 0);
        const p = eBack(prog(lt, t, 0.6));
        if (p <= 0) return;
        const k = eExpo(prog(lt, t, 1.4));
        const w = P ? 900 : 500, h = P ? 250 : 420;
        const x = P ? 90 : 140 + i * 560, y = P ? 360 + i * 285 : 260;
        withAlpha(clamp(p), () => withT(x + w / 2, y + h / 2, 0.85 + 0.15 * p, () => {
          panel(-w / 2, -h / 2, w, h, { glow: hexA(col, 0.4), blur: 40 });
          const num = (i === 2 ? '≈' : '') + (i === 1 ? '2' : fmt(v * k, dec)) + suf;
          if (P) {
            text(num, -w / 2 + 50, -20, { size: 110, weight: 700, family: 'grotesk', color: col, glow: col, blur: 30 });
            text(label, -w / 2 + 52, 72, { size: 28, weight: 600, color: C.dim });
          } else {
            text(num, 0, -60, { size: 120, weight: 700, family: 'grotesk', align: 'center', color: col, glow: col, blur: 30 });
            text(label, 0, 50, { size: 28, weight: 600, align: 'center', color: C.dim });
          }
          if (i === 1) { const rx = P ? w / 2 - 130 : 0, ry = P ? 0 : 130; ring(rx, ry, P ? 70 : 52, 0.667 * k, col, 14); }
          if (i === 2) {
            // 700 dots grid: each dot is one agent's workload
            const cols2 = P ? 35 : 35, sz = P ? 8.5 : 11;
            const gx = P ? w / 2 - 330 : -cols2 * sz / 2, gy = P ? -50 : 100;
            if (P) return;
            for (let d = 0; d < 700; d++) {
              if (d / 700 > k) break;
              circle(gx + (d % cols2) * sz + sz / 2, gy + Math.floor(d / cols2) * sz, sz * 0.32, hexA(col, 0.9));
            }
          }
        }));
      });
      source(S, 'Source: Klarna press release, Feb 27 2024 (company-reported)', L.W / 2, P ? 1220 : 860, ap(S, 'kl', 0.5, 0.8));
    });
    inStage(S, stage(S, order, 'time'), () => {
      kicker('Average time to resolve an issue', L.W / 2, 220, C.green);
      const k = eInOut(prog(lt, S.q('time2'), 1.2));
      const bx = 360, bw = 1200;
      const bars = [['Before', 11, C.red, 1], ['With AI', 11 - 9 * k, C.green, 1 - 0.82 * k]];
      bars.forEach(([label, v, col, f], i) => {
        const y = 400 + i * 220;
        const p = ap(S, 'time', 0.6, i * 0.3);
        withAlpha(p, () => {
          text(label, bx, y - 50, { size: 30, weight: 700, color: C.dim });
          X().save(); rrect(bx, y, bw * f * p, 90, 16); X().fillStyle = col; X().shadowColor = col; X().shadowBlur = 30; X().fill(); X().restore();
          text(i && k > 0.98 ? '< 2 min' : `${Math.round(v)} min`, bx + bw * f * p + 30, y + 46, { size: 54, weight: 700, family: 'grotesk', color: col });
        });
      });
      source(S, 'Source: Klarna press release, Feb 27 2024 (company-reported)', L.W / 2, 860, ap(S, 'time', 0.5, 0.6));
    });
    inStage(S, stage(S, order, 'study'), () => {
      kicker(P ? 'Stanford + MIT study · 5,179 agents' : 'Stanford + MIT study · 5,179 support agents', L.W / 2, P ? 300 : 190, C.green);
      const items = [['s14', 14, 'issues resolved per hour', 'All agents', C.cyan], ['s34', 34, 'issues resolved per hour', 'Newer agents', C.lime]];
      items.forEach(([cue, v, label, who, col], i) => {
        if (!S.has(cue)) return;
        const t = S.q(cue);
        const p = eBack(prog(lt, S.q('study') + 0.4 + i * 0.3, 0.6));
        if (p <= 0) return;
        const k = eExpo(prog(lt, t, 1.2));
        const w = P ? 900 : 700, h = P ? 380 : 480;
        const solo = !S.has('s34');
        const x = P ? 90 : solo ? L.W / 2 - w / 2 : 200 + i * 820, y = P ? 380 + i * 420 : 260;
        withAlpha(clamp(p), () => withT(x + w / 2, y + h / 2, 0.85 + 0.15 * p, () => {
          panel(-w / 2, -h / 2, w, h, { glow: hexA(col, 0.4), blur: 40 });
          text(who, 0, -h / 2 + 60, { size: 28, weight: 700, align: 'center', color: C.dim, family: 'mono' });
          text(`+${Math.round(v * k)}%`, 0, -10, { size: 170, weight: 700, family: 'grotesk', align: 'center', color: col, glow: col, blur: 40 });
          text(label, 0, h / 2 - 70, { size: 30, weight: 600, align: 'center' });
        }));
      });
      source(S, P ? 'Brynjolfsson, Li & Raymond · QJE 2025' : 'Source: Brynjolfsson, Li & Raymond, "Generative AI at Work", Quarterly Journal of Economics, 2025', L.W / 2, P ? 1220 : 860, ap(S, 'study', 0.5, 0.6));
    });
    inStage(S, stage(S, order, 'gartner'), () => {
      const c = P ? [540, 640] : [620, 500];
      const k = eExpo(prog(lt, S.q('gartner') + 0.6, 2.2));
      ring(...c, P ? 260 : 250, 0.8 * k, C.green, 26);
      text(`${Math.round(80 * k)}%`, c[0], c[1] - 10, { size: 150, weight: 700, family: 'grotesk', align: 'center', glow: C.green, blur: 40 });
      text('by 2029', c[0], c[1] + 90, { size: 36, weight: 700, align: 'center', color: C.dim });
      const tp = ap(S, 'gartner', 0.6, 0.3);
      slide(tp, () => {
        const x = P ? 540 : 1000, y = P ? 1000 : 400;
        const al = P ? 'center' : 'left';
        text('of common customer', x, y, { size: 50, weight: 800, align: al });
        text('service issues resolved', x, y + 64, { size: 50, weight: 800, align: al });
        text('by agentic AI, no human needed', x, y + 128, { size: 40, weight: 700, align: al, gradient: [C.green, C.cyan] });
        pill(x, y + 210, 'Prediction, not a result', { icon: 'eye', color: C.amber, align: al === 'center' ? 'center' : 'left', size: 22 });
      }, 40, 0);
      source(S, 'Source: Gartner press release, Mar 5 2025', L.W / 2, P ? 1240 : 870, ap(S, 'gartner', 0.5, 0.8));
    });
  },

  cost(S) {
    const { L, lt } = S;
    const order = ['human', 'split', 'saving'];
    // Chart stage spans human + ai
    inStage(S, stage(S, order, 'human'), () => {
      const ch = { x: 260, y: 200, w: 1300, h: 600 };
      kicker('Illustrative model · not measured data', L.W / 2, 160, C.amber);
      glowLine([[ch.x, ch.y], [ch.x, ch.y + ch.h], [ch.x + ch.w, ch.y + ch.h]], 'rgba(255,255,255,0.4)', 2, { blur: 0 });
      text('Support cost', ch.x - 20, ch.y - 10, { size: 24, weight: 600, color: C.dim, align: 'right' });
      text('Conversations per month →', ch.x + ch.w, ch.y + ch.h + 40, { size: 24, weight: 600, color: C.dim, align: 'right' });
      const hp = eInOut(prog(lt, S.q('human'), 2.2));
      const human = (f) => [ch.x + ch.w * f, ch.y + ch.h - ch.h * 0.92 * f];
      const hpts = []; for (let i = 0; i <= 40; i++) hpts.push(human((i / 40) * hp));
      glowLine(hpts, C.red, 6);
      if (hp > 0.05) {
        const [hx, hy] = human(hp);
        pill(hx - 20, hy - 40, 'Human-only team', { icon: 'users', color: C.red, align: 'right', size: 22 });
      }
      const dp = pop(S, 'double', 0.5);
      if (dp > 0) withAlpha(clamp(dp), () => {
        const [x1, y1] = human(0.4), [x2, y2] = human(0.8);
        glowLine([[x1, ch.y + ch.h], [x1, y1]], 'rgba(255,255,255,0.3)', 2, { dash: [6, 8], blur: 0 });
        glowLine([[x2, ch.y + ch.h], [x2, y2]], 'rgba(255,255,255,0.3)', 2, { dash: [6, 8], blur: 0 });
        text('2× questions', x2, ch.y + ch.h - 30, { size: 22, weight: 700, align: 'center' });
        text('≈ 2× people', x2 + 120, y2 + 10, { size: 24, weight: 800, color: C.red });
      });
      const ap2 = eInOut(prog(lt, S.q('ai'), 2.4));
      if (ap2 > 0) {
        const ai = (f) => [ch.x + ch.w * f, ch.y + ch.h - ch.h * (0.22 + 0.12 * f)];
        const apts = [[ch.x, ch.y + ch.h], [ch.x, ai(0)[1]]]; for (let i = 0; i <= 40; i++) apts.push(ai((i / 40) * ap2));
        glowLine(apts, C.green, 6);
        pill(ch.x + 30, ai(0)[1] - 44, 'Setup cost', { color: C.green, size: 20 });
        if (ap2 > 0.6) withAlpha(prog(ap2, 0.6, 0.3), () => pill(...ai(ap2).map((v, i) => v + (i ? 50 : -10)), 'AI assistant + small team', { icon: 'bot', color: C.green, align: 'right', size: 22 }));
        const fp = ap(S, 'fraction', 0.6);
        if (fp > 0) withAlpha(fp, () => {
          // break-even marker where lines cross: 0.92f = 0.22 + 0.12f -> f = 0.275
          const [bx, by] = human(0.275);
          circle(bx, by, 14, '#fff', { glow: C.amber, blur: 24 });
          pill(bx + 30, by - 50, 'Break-even', { color: C.amber, size: 22 });
          const [sx] = human(0.85);
          glowLine([[sx, human(0.85)[1]], [sx, ai(0.85)[1]]], C.amber, 3, { dash: [8, 8] });
          text('Savings grow with volume', sx - 20, (human(0.85)[1] + ai(0.85)[1]) / 2, { size: 26, weight: 800, align: 'right', color: C.amber });
        });
      }
    });
    inStage(S, stage(S, order, 'split'), () => {
      const t0 = S.q('split');
      const bx = 200, bw = 1520, by = 300, bh = 120;
      const k = eInOut(prog(lt, t0, 1.2));
      kicker('Who handles what · illustrative split', L.W / 2, 220, C.cyan);
      X().save(); rrect(bx, by, bw * 0.72 * k, bh, 20); X().fillStyle = hexA(C.cyan, 0.85); X().shadowColor = C.cyan; X().shadowBlur = 30; X().fill(); X().restore();
      X().save(); rrect(bx + bw * 0.72 * k + 10, by, Math.max(0, bw * 0.28 * k - 10), bh, 20); X().fillStyle = hexA(C.pink, 0.85); X().fill(); X().restore();
      if (k > 0.6) {
        withAlpha(prog(k, 0.6, 0.4), () => {
          icon('bot', bx + 60, by + bh / 2, 44, '#0b1020', 2.4);
          text('Repetitive questions → AI', bx + 100, by + bh / 2, { size: 34, weight: 800, color: '#0b1020' });
          icon('users', bx + bw * 0.72 + 50, by + bh / 2, 40, '#fff', 2.4);
          text('Complex', bx + bw * 0.72 + 90, by + bh / 2, { size: 30, weight: 800 });
        });
      }
      const pp = ap(S, 'people', 0.6);
      const dests = [['dollar', 'Sales', C.lime], ['headset', 'Complex cases', C.pink], ['layers', 'Building the product', C.violet]];
      dests.forEach(([ic, label, col], i) => {
        const p = eBack(prog(lt, S.q('people') + i * 0.3, 0.6));
        if (p <= 0) return;
        const x = 360 + i * 600, y = 640;
        withAlpha(clamp(p), () => withT(x, y, 0.8 + 0.2 * p, () => {
          panel(-240, -120, 480, 240, { glow: hexA(col, 0.35) });
          badge(ic, 0, -40, 46, col);
          text(label, 0, 50, { size: 30, weight: 800, align: 'center' });
          personRow(-60, 92, 3, 26, C.dim, clamp(p), 1.6);
        }));
      });
      withAlpha(pp, () => text('Your people move to higher-value work', L.W / 2, 860, { size: 30, weight: 700, align: 'center', color: C.dim }));
    });
    inStage(S, stage(S, order, 'saving'), () => {
      const t0 = S.q('saving');
      text('Real savings =', L.W / 2, 330, { size: 56, weight: 800, align: 'center', color: C.dim });
      text('not wasting people', L.W / 2, 430, { size: 80, weight: 800, align: 'center', gradient: [C.cyan, C.violet] });
      const tp = ap(S, 'thousand', 0.5);
      withAlpha(tp, () => {
        const w = measure('“Where is my order?” × 1,000', 46, 700) ;
        text('“Where is my order?” × 1,000', L.W / 2, 620, { size: 46, weight: 700, align: 'center', color: C.ink });
        strike(L.W / 2 - w / 2 - 20, 622, w + 40, prog(lt, S.q('thousand') + 0.4, 0.5));
        const bp = pop(S, 'thousand', 0.5, 0.9);
        if (bp > 0) withAlpha(clamp(bp), () => withT(L.W / 2, 740, bp, () => pill(0, 0, 'Handled by AI', { icon: 'bot', color: C.green, align: 'center', size: 28, glow: true })));
      });
    });
  },

  right(S) {
    const { L, lt } = S;
    const P = L.P;
    const copy = COPY[S.video];
    const order = ['skip', 'ac', 'kl', 'lesson', 'list', 'result'];
    inStage(S, stage(S, order, 'skip'), () => {
      const p = pop(S, 'skip', 0.6);
      withT(L.W / 2, P ? 560 : 400, Math.max(0, p), () => badge('alert', 0, 0, 90, C.amber));
      if (S.video !== 'short') text('The part most people skip', L.W / 2, P ? 760 : 590, { size: P ? 70 : 72, weight: 800, align: 'center' });
    });
    const caseCard = (cue, ic, col, kick, title, lines, src, payCue) => {
      const p = eOut(prog(lt, S.q(cue), 0.6));
      const w = P ? 940 : 1300, h = P ? 640 : 520;
      const x = L.W / 2 - w / 2, y = P ? 330 : 190;
      withAlpha(p, () => {
        panel(x, y, w, h, { glow: hexA(col, 0.4) });
        badge(ic, x + 100, y + 110, 60, col);
        text(kick, x + 190, y + 80, { size: 24, weight: 500, family: 'mono', color: col });
        if (P) { para(title, x + 190, y + 130, w - 230, { size: 36, weight: 800 }); } else text(title, x + 190, y + 130, { size: 44, weight: 800 });
        lines.forEach((l, i) => {
          const lp = ap(S, i ? payCue : cue, 0.5, i ? 0 : 0.6);
          slide(lp, () => {
            icon(i ? 'gavel' : 'chat', x + 100, y + (P ? 300 : 260) + i * (P ? 150 : 110), 34, i ? C.red : C.dim);
            para(l, x + 160, y + (P ? 300 : 260) + i * (P ? 150 : 110), w - 220, { size: P ? 32 : 34, weight: 600, color: i ? C.ink : C.dim });
          }, 0, 20);
        });
        source(S, src, L.W / 2, y + h - 50, p, 'center');
      });
    };
    inStage(S, stage(S, order, 'ac'), () => caseCard('ac', 'gavel', C.red, 'FEB 2024 · CANADA', 'Moffatt v. Air Canada', ['Chatbot told a customer the wrong refund policy.', 'Tribunal: the airline is responsible. It had to pay.'], 'Source: BC Civil Resolution Tribunal, 2024 BCCRT 149', 'pay'));
    inStage(S, stage(S, order, 'kl'), () => caseCard('kl', 'users', C.amber, 'MAY 2025 · KLARNA', 'Too much automation hurt quality', ['CEO: cutting human support lowered service quality.', 'Klarna started hiring human agents again.'], 'Source: CEO Sebastian Siemiatkowski to Bloomberg, May 2025', 'hiring'));
    inStage(S, stage(S, order, 'lesson'), () => {
      const p = ap(S, 'lesson', 0.6);
      withAlpha(p, () => {
        text('A chatbot is only as good', L.W / 2, 420, { size: 76, weight: 800, align: 'center' });
        text('as its design.', L.W / 2, 520, { size: 76, weight: 800, align: 'center', gradient: [C.amber, C.pink] });
      });
    });
    inStage(S, stage(S, order, 'list'), () => {
      const items = copy.checklist;
      const cues = ['l1', 'l2', 'l3', 'l4', 'l5'];
      const live = items.map((s, i) => [s, cues[i]]).filter(([s, c]) => s && S.has(c));
      const x = P ? 80 : 420, y0 = P ? 380 : 210, gap = P ? 170 : 130;
      text('Guardrails checklist', P ? 540 : x, y0 - 70, { size: 30, weight: 700, family: 'mono', color: C.amber, align: P ? 'center' : 'left' });
      live.forEach(([s, c], i) => {
        const p = eOut(prog(lt, S.q(c), 0.45));
        const y = y0 + i * gap;
        X().save(); rrect(x, y, P ? 920 : 1080, gap - 24, 22); X().fillStyle = 'rgba(255,255,255,0.05)'; X().fill(); X().restore();
        circle(x + 64, y + (gap - 24) / 2, 30, p > 0 ? hexA(C.green, 0.25 + 0.6 * p) : 'rgba(255,255,255,0.06)', p > 0 ? { glow: C.green, blur: 20 * p } : { stroke: 'rgba(255,255,255,0.2)' });
        if (p > 0) withAlpha(p, () => icon('check', x + 64, y + (gap - 24) / 2, 34 * eBack(clamp(p)), '#fff', 3.5));
        text(s, x + 120, y + (gap - 24) / 2, { size: P ? 34 : 38, weight: 700, color: p > 0 ? C.ink : C.faint });
      });
    });
    inStage(S, stage(S, order, 'result'), () => {
      const res = [['r1', 'bolt', 'Speed', C.cyan], ['r2', 'dollar', 'Lower cost', C.lime], ['r3', 'shieldcheck', 'Low error rate', C.green]];
      res.forEach(([cue, ic, label, col], i) => {
        const p = eBack(prog(lt, S.q(cue), 0.6));
        node(360 + i * 600, 460, ic, label, col, p, { r: 100, size: 40, gap: 60 });
      });
      const tp = ap(S, 'r3', 0.5, 0.8);
      withAlpha(tp, () => text('together.', L.W / 2, 800, { size: 50, weight: 800, align: 'center', gradient: [C.cyan, C.violet] }));
    });
  },

  future(S) {
    const { L, lt } = S;
    const order = ['door', 'flow', 'adopt'];
    const c = [960, 500];
    inStage(S, stage(S, order, 'door'), () => {
      const p = eBack(prog(lt, 0.1, 0.8));
      // App window with the chat as front door
      withAlpha(clamp(p), () => {
        panel(c[0] - 330, c[1] - 290, 660, 560, { glow: hexA(C.cyan, 0.45) });
        text('Your app', c[0] - 290, c[1] - 240, { size: 26, weight: 700, color: C.dim });
        X().save(); rrect(c[0] - 150, c[1] - 170, 300, 360, 150); const g = X().createLinearGradient(0, c[1] - 170, 0, c[1] + 190); g.addColorStop(0, hexA(C.cyan, 0.5)); g.addColorStop(1, hexA(C.violet, 0.3)); X().fillStyle = g; X().shadowColor = C.cyan; X().shadowBlur = 60; X().fill(); X().restore();
        icon('chat', c[0], c[1] + 5, 120, '#fff', 2.2);
        text('The front door', c[0], c[1] + 240, { size: 30, weight: 800, align: 'center' });
      });
      const tp = ap(S, 'two', 0.6);
      [['users', 'Customers', 'get help', -1, 'two', C.cyan], ['store', 'Owners', 'run the business', 1, 'owners', C.violet]].forEach(([ic, label, sub, side, cue, col]) => {
        const pp = eBack(prog(lt, S.q(cue), 0.6));
        const x = c[0] + side * 640;
        node(x, c[1] - 20, ic, label, col, pp, { r: 70, size: 34, sub });
        if (pp > 0) flow(side < 0 ? [[x + 90, c[1] - 20], [c[0] - 350, c[1] - 20]] : [[x - 90, c[1] - 20], [c[0] + 350, c[1] - 20]], lt, S.q(cue) + 0.2, col, { packets: 3, speed: 0.7, width: 4 });
      });
      void tp;
    });
    inStage(S, stage(S, order, 'flow'), () => {
      const t0 = S.q('flow');
      const R = 330;
      const steps = [['cart', 'Order'], ['box', 'Inventory'], ['doc', 'Invoice'], ['chart', 'Report'], ['shield', 'Security'], ['bell', 'Notify']];
      node(...c, 'bot', 'AI assistant', C.cyan, eBack(prog(lt, t0, 0.6)), { r: 80, size: 30 });
      const pts = steps.map((_, i) => { const a = (i / steps.length) * Math.PI * 2 - Math.PI / 2; return [c[0] + Math.cos(a) * R * 1.45, c[1] + Math.sin(a) * R]; });
      steps.forEach(([ic, label], i) => {
        const p = eBack(prog(lt, t0 + 0.3 + i * 0.25, 0.5));
        const a = pts[i], b = pts[(i + 1) % pts.length];
        if (p > 0.9) flow([a, b], lt, t0 + 0.5 + i * 0.25, C.violet, { packets: 1, speed: 0.8, width: 3 });
        if (p > 0) flow([c, a], lt, t0 + 0.3 + i * 0.25, hexA(C.cyan, 1).startsWith('rgba') ? C.cyan : C.cyan, { packets: 0, width: 2 });
        node(...a, ic, label, [C.lime, C.cyan, C.violet, C.amber, C.green, C.pink][i], p, { r: 46, size: 22, gap: 26 });
      });
      const ap2 = ap(S, 'flow', 0.6, 2.4);
      withAlpha(ap2, () => pill(c[0], 900, 'Automated, exactly the way the owner wants', { icon: 'gear', color: C.violet, align: 'center', size: 26 }));
    });
    inStage(S, stage(S, order, 'adopt'), () => {
      const t0 = S.q('adopt');
      const ch = { x: 300, y: 220, w: 1320, h: 560 };
      kicker('The compounding advantage · illustrative', L.W / 2, 160, C.cyan);
      glowLine([[ch.x, ch.y], [ch.x, ch.y + ch.h], [ch.x + ch.w, ch.y + ch.h]], 'rgba(255,255,255,0.35)', 2, { blur: 0 });
      text('Time →', ch.x + ch.w, ch.y + ch.h + 36, { size: 22, weight: 600, color: C.dim, align: 'right' });
      const k = eInOut(prog(lt, t0, 3));
      const curve = (f, a) => [ch.x + ch.w * f, ch.y + ch.h - ch.h * (0.08 + a * Math.pow(f, 1.6))];
      const A = [], B = [];
      for (let i = 0; i <= 50; i++) { A.push(curve((i / 50) * k, 0.85)); B.push(curve((i / 50) * k, 0.25)); }
      glowLine(A, C.cyan, 6); glowLine(B, C.faint, 5, { blur: 0 });
      if (k > 0.3) {
        pill(A[A.length - 1][0] - 10, A[A.length - 1][1] - 40, 'Adopt AI now', { icon: 'bolt', color: C.cyan, align: 'right', size: 22 });
        pill(B[B.length - 1][0] - 10, B[B.length - 1][1] - 40, 'Wait', { color: C.dim, align: 'right', size: 22 });
      }
      const gp = ap(S, 'gap', 0.6);
      if (gp > 0) withAlpha(gp, () => {
        const [x, y1] = A[A.length - 1], y2 = B[B.length - 1][1];
        glowLine([[x + 30, y1], [x + 30, y2]], C.amber, 3, { dash: [8, 8] });
        text('Data + systems', x + 50, (y1 + y2) / 2 - 18, { size: 26, weight: 800, color: C.amber });
        text('years to catch up', x + 50, (y1 + y2) / 2 + 18, { size: 22, weight: 600, color: C.dim });
      });
    });
  },

  cta(S, assets) {
    const { L, lt } = S;
    const P = L.P;
    const order = ['pre', 'q', 'site'];
    inStage(S, stage(S, order, 'pre'), () => {
      text('So, the real question is…', L.W / 2, L.H / 2 - (P ? 150 : 40), { size: P ? 56 : 60, weight: 700, align: 'center', color: C.dim });
    });
    inStage(S, stage(S, order, 'q'), () => {
      const t0 = S.q('q');
      const words = P ? [['Is', 'your', 'app'], ['ready', 'for', 'AI?']] : [['Is', 'your', 'app', 'ready', 'for', 'AI?']];
      const size = P ? 130 : 130;
      let n = 0;
      words.forEach((row, ri) => {
        const line = row.join(' ');
        let x = L.W / 2 - measure(line, size, 800) / 2;
        row.forEach((w) => {
          const p = eOut(prog(lt, t0 + n * 0.13, 0.5));
          const ww = measure(w + ' ', size, 800);
          if (p > 0) withAlpha(p, () => withT(x + measure(w, size, 800) / 2, (P ? 560 : 500) + ri * size * 1.1, lerp(1.5, 1, p), () => {
            text(w, 0, 0, { size, weight: 800, align: 'center', gradient: w === 'AI?' ? [C.cyan, C.violet, C.pink] : null, glow: w === 'AI?' ? C.violet : null, blur: 50 });
          }));
          x += ww; n++;
        });
      });
    });
    inStage(S, stage(S, order, 'site'), () => {
      const t0 = S.q('site');
      const typed = prog(lt, t0 + 0.3, 1.2);
      const scroll = eInOut(prog(lt, t0 + 1.5, Math.max(2, S.dur - (t0 + 1.5) - 1.5))) * 0.35;
      if (P) {
        const bp = eOut(prog(lt, t0, 0.8));
        withAlpha(bp, () => {
          X().save(); X().translate(0, (1 - bp) * 100);
          phone(270, 250, 540, 900, (w, h) => {
            const img = assets.mobile;
            text('zahidul-islam.com'.slice(0, Math.round(17 * typed)), w / 2, 80, { size: 24, weight: 500, family: 'mono', align: 'center', color: C.ink });
            if (img && img.complete) {
              const sc = w / img.width;
              X().save(); X().beginPath(); X().rect(0, 120, w, h - 120); X().clip();
              X().drawImage(img, 0, 120 - (img.height * sc - (h - 120)) * scroll * 1.5, w, img.height * sc);
              X().restore();
            }
          });
          X().restore();
        });
        const cp = pop(S, 'site', 0.6, 0.8);
        if (cp > 0) withAlpha(clamp(cp), () => withT(540, 1230, cp, () => pill(0, 0, 'zahidul-islam.com', { icon: 'globe', color: C.cyan, align: 'center', size: 40, glow: true })));
      } else {
        const bp = eOut(prog(lt, t0, 0.8));
        withAlpha(bp, () => {
          X().save(); X().translate(0, (1 - bp) * 120);
          browser(620, 130, 1180, 760, assets.desktop, 'zahidul-islam.com', typed, scroll);
          X().restore();
        });
        const lp = ap(S, 'site', 0.6, 0.6);
        slide(lp, () => {
          text('Zahidul Islam', 110, 330, { size: 56, weight: 800 });
          text('AI Automation Engineer', 110, 395, { size: 30, weight: 600, color: C.dim });
          ['AI chatbots for apps & websites', 'Customer support automation', 'Inventory, documents & security'].forEach((s, i) => {
            icon('check', 128, 480 + i * 60, 28, C.green, 3);
            text(s, 160, 481 + i * 60, { size: 26, weight: 600 });
          });
        }, -40, 0);
        const cp = pop(S, 'build', 0.6);
        if (cp > 0) withAlpha(clamp(cp), () => withT(330, 760, cp, () => pill(0, 0, "Let's build it together  →", { color: C.lime, align: 'center', size: 30, solid: true, glow: true })));
      }
    });
  },
};
