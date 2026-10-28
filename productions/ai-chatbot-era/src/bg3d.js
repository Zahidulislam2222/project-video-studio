// Persistent 3D world behind the graphics: a neural "AI core", a travelling grid floor,
// floating glass solids and a star tunnel. The camera keeps flying forward; each scene
// sets a preset (core placement, colour, speed) and the world blends between presets.
import * as THREE from 'three';
import { rng, clamp, eInOut, lerp } from './kit.js';

const DEFAULT = { core: [0, 0, 0, 1, 1], color: '#22d3ee', color2: '#8b5cf6', grid: 0.55, shapes: 0.7, speed: 6, stars: 1, camY: 2, tilt: 0 };

export class World {
  constructor(canvas, W, H, scenes, presets) {
    this.W = W; this.H = H;
    this.portrait = H > W;
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
    this.renderer.setPixelRatio(1);
    this.renderer.setSize(W, H, false);
    this.renderer.setClearColor(0x050816, 1);
    this.scene = new THREE.Scene();
    this.scene.fog = new THREE.FogExp2(0x050816, 0.012);
    this.camera = new THREE.PerspectiveCamera(this.portrait ? 72 : 45, W / H, 0.1, 600);
    this.timeline = scenes.map((s) => ({ start: s.start, end: s.end, p: { ...DEFAULT, ...(presets[s.id] || {}) } }));
    this.buildTravel();
    this.buildStars();
    this.buildGrid();
    this.buildCore();
    this.buildShapes();
  }

  // Integrate camera speed so blended speed changes never jump.
  buildTravel() {
    const end = this.timeline[this.timeline.length - 1].end + 2;
    this.dt = 0.05;
    this.travel = [0];
    for (let t = 0; t < end; t += this.dt) this.travel.push(this.travel[this.travel.length - 1] + this.preset(t).speed * this.dt);
  }
  distance(t) {
    const i = clamp(t / this.dt, 0, this.travel.length - 2);
    const k = Math.floor(i);
    return lerp(this.travel[k], this.travel[k + 1], i - k);
  }

  preset(t) {
    const tl = this.timeline;
    let i = tl.findIndex((s) => t < s.end);
    if (i < 0) i = tl.length - 1;
    const cur = tl[i].p;
    const blend = 1.4;
    if (i > 0 && t < tl[i].start + blend * 0.5) {
      const k = eInOut(clamp((t - (tl[i].start - blend * 0.5)) / blend));
      return mix(tl[i - 1].p, cur, k);
    }
    if (i < tl.length - 1 && t > tl[i].end - blend * 0.5) {
      const k = eInOut(clamp((t - (tl[i].end - blend * 0.5)) / blend));
      return mix(cur, tl[i + 1].p, k);
    }
    return cur;
  }

  buildStars() {
    const r = rng(7);
    const n = 1800;
    this.starBase = new Float32Array(n * 3);
    for (let i = 0; i < n; i++) {
      const a = r() * Math.PI * 2;
      const rad = 14 + r() * 90;
      this.starBase[i * 3] = Math.cos(a) * rad;
      this.starBase[i * 3 + 1] = Math.sin(a) * rad * 0.7 + 10;
      this.starBase[i * 3 + 2] = -r() * 320;
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(n * 3), 3));
    this.starMat = new THREE.PointsMaterial({ size: 0.5, color: 0x9fb4ff, transparent: true, opacity: 0.8, sizeAttenuation: true, map: dotTexture(), depthWrite: false, blending: THREE.AdditiveBlending });
    this.stars = new THREE.Points(geo, this.starMat);
    this.scene.add(this.stars);
  }

  buildGrid() {
    const size = 400, div = 80;
    this.cell = size / div;
    const grid = new THREE.GridHelper(size, div, 0x3b82f6, 0x1e3a8a);
    grid.material.transparent = true;
    grid.material.depthWrite = false;
    grid.position.y = -9;
    this.grid = grid;
    this.scene.add(grid);
    // Horizon glow plane.
    const glow = new THREE.Mesh(new THREE.PlaneGeometry(600, 120), new THREE.MeshBasicMaterial({ map: gradientTexture(), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, fog: false }));
    glow.position.set(0, 10, -260);
    this.horizon = glow;
    this.scene.add(glow);
  }

  buildCore() {
    const g = new THREE.Group();
    const n = 520;
    const pts = [];
    for (let i = 0; i < n; i++) {
      const y = 1 - (i / (n - 1)) * 2;
      const rad = Math.sqrt(1 - y * y);
      const th = Math.PI * (3 - Math.sqrt(5)) * i;
      pts.push(new THREE.Vector3(Math.cos(th) * rad * 6, y * 6, Math.sin(th) * rad * 6));
    }
    const pgeo = new THREE.BufferGeometry().setFromPoints(pts);
    this.coreDots = new THREE.PointsMaterial({ size: 0.32, color: 0x22d3ee, map: dotTexture(), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending });
    g.add(new THREE.Points(pgeo, this.coreDots));
    const seg = [];
    const r = rng(11);
    for (let i = 0; i < n; i++) {
      for (let j = i + 1; j < n; j++) {
        if (pts[i].distanceTo(pts[j]) < 1.15 && r() < 0.55) seg.push(pts[i], pts[j]);
      }
    }
    this.coreLines = new THREE.LineBasicMaterial({ color: 0x3b82f6, transparent: true, opacity: 0.35, depthWrite: false, blending: THREE.AdditiveBlending });
    g.add(new THREE.LineSegments(new THREE.BufferGeometry().setFromPoints(seg), this.coreLines));
    this.inner = new THREE.Mesh(new THREE.IcosahedronGeometry(3.1, 1), new THREE.MeshBasicMaterial({ color: 0x8b5cf6, wireframe: true, transparent: true, opacity: 0.55, blending: THREE.AdditiveBlending, depthWrite: false }));
    g.add(this.inner);
    this.halo = new THREE.Sprite(new THREE.SpriteMaterial({ map: haloTexture(), color: 0x22d3ee, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending }));
    this.halo.scale.set(26, 26, 1);
    g.add(this.halo);
    this.rings = [];
    for (let k = 0; k < 3; k++) {
      const ring = new THREE.Mesh(new THREE.TorusGeometry(8 + k * 1.6, 0.04, 6, 160), new THREE.MeshBasicMaterial({ color: 0x22d3ee, transparent: true, opacity: 0.5, blending: THREE.AdditiveBlending, depthWrite: false }));
      ring.rotation.x = 1.2 + k * 0.35;
      ring.rotation.y = k * 0.7;
      this.rings.push(ring);
      g.add(ring);
    }
    this.core = g;
    this.scene.add(g);
  }

  buildShapes() {
    const r = rng(23);
    this.shapes = [];
    const geos = [new THREE.BoxGeometry(2, 2, 2), new THREE.OctahedronGeometry(1.5), new THREE.IcosahedronGeometry(1.3), new THREE.TorusGeometry(1.1, 0.35, 10, 28)];
    for (let i = 0; i < 26; i++) {
      const geo = geos[i % geos.length];
      const col = [0x22d3ee, 0x8b5cf6, 0x3b82f6, 0xec4899][i % 4];
      const body = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: 0.08, depthWrite: false }));
      const edges = new THREE.LineSegments(new THREE.EdgesGeometry(geo), new THREE.LineBasicMaterial({ color: col, transparent: true, opacity: 0.7 }));
      const m = new THREE.Group();
      m.add(body, edges);
      const side = i % 2 ? 1 : -1;
      const base = { x: side * (16 + r() * 30), y: -4 + r() * 22, z: -r() * 300, rx: r() * 3, ry: r() * 3, spin: 0.2 + r() * 0.6, s: 0.6 + r() * 1.2 };
      this.shapes.push({ m, body, edges, base });
      this.scene.add(m);
    }
  }

  render(t) {
    const p = this.preset(t);
    const dist = this.distance(t);
    const cam = this.camera;
    cam.position.set(Math.sin(t * 0.13) * 1.2, p.camY + Math.sin(t * 0.21) * 0.5, 30);
    cam.lookAt(0, p.camY * 0.4 + p.tilt, 0);

    // Star tunnel moves toward the camera.
    const pos = this.stars.geometry.attributes.position.array;
    for (let i = 0; i < pos.length; i += 3) {
      pos[i] = this.starBase[i];
      pos[i + 1] = this.starBase[i + 1];
      pos[i + 2] = ((this.starBase[i + 2] + dist * 1.6) % 320 + 320) % 320 - 290;
    }
    this.stars.geometry.attributes.position.needsUpdate = true;
    this.starMat.opacity = 0.75 * p.stars;

    this.grid.position.z = (dist % this.cell) - 40;
    this.grid.material.opacity = p.grid;
    this.horizon.material.opacity = 0.55 * p.grid + 0.15;

    const [cx, cy, cz, cs, co] = p.core;
    this.core.position.set(cx, cy + Math.sin(t * 0.8) * 0.3, cz);
    this.core.scale.setScalar(cs * (1 + Math.sin(t * 1.7) * 0.015));
    this.core.rotation.y = t * 0.22;
    this.core.rotation.x = Math.sin(t * 0.1) * 0.25;
    this.inner.rotation.set(-t * 0.4, t * 0.3, 0);
    this.rings.forEach((ring, k) => (ring.rotation.z = t * (0.3 + k * 0.15) * (k % 2 ? -1 : 1)));
    const c1 = new THREE.Color(p.color), c2 = new THREE.Color(p.color2);
    this.coreDots.color.copy(c1);
    this.coreDots.opacity = co;
    this.coreLines.color.copy(c1).lerp(c2, 0.4);
    this.coreLines.opacity = 0.32 * co;
    this.inner.material.color.copy(c2);
    this.inner.material.opacity = 0.5 * co;
    this.halo.material.color.copy(c1);
    this.halo.material.opacity = 0.42 * co;
    this.rings.forEach((ring) => { ring.material.color.copy(c1); ring.material.opacity = 0.45 * co; });
    this.core.visible = co > 0.01;

    for (const s of this.shapes) {
      const b = s.base;
      const z = ((b.z + dist) % 300 + 300) % 300 - 270;
      s.m.position.set(b.x, b.y, z);
      s.m.rotation.set(b.rx + t * b.spin, b.ry + t * b.spin * 0.7, 0);
      s.m.scale.setScalar(b.s);
      const fade = clamp((z + 270) / 60) * clamp((25 - z) / 20);
      s.edges.material.opacity = 0.65 * p.shapes * fade;
      s.body.material.opacity = 0.08 * p.shapes * fade;
    }
    this.renderer.render(this.scene, cam);
  }
}

function mix(a, b, k) {
  const out = {};
  for (const key of Object.keys(a)) {
    if (Array.isArray(a[key])) out[key] = a[key].map((v, i) => lerp(v, b[key][i], k));
    else if (typeof a[key] === 'number') out[key] = lerp(a[key], b[key], k);
    else if (typeof a[key] === 'string' && a[key][0] === '#') out[key] = '#' + new THREE.Color(a[key]).lerp(new THREE.Color(b[key]), k).getHexString();
    else out[key] = k < 0.5 ? a[key] : b[key];
  }
  return out;
}

function canvasTexture(size, draw) {
  const c = document.createElement('canvas');
  c.width = c.height = size;
  draw(c.getContext('2d'), size);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}
function dotTexture() {
  return canvasTexture(64, (g, s) => {
    const r = g.createRadialGradient(s / 2, s / 2, 0, s / 2, s / 2, s / 2);
    r.addColorStop(0, 'rgba(255,255,255,1)'); r.addColorStop(0.35, 'rgba(255,255,255,0.6)'); r.addColorStop(1, 'rgba(255,255,255,0)');
    g.fillStyle = r; g.fillRect(0, 0, s, s);
  });
}
function haloTexture() {
  return canvasTexture(256, (g, s) => {
    const r = g.createRadialGradient(s / 2, s / 2, 0, s / 2, s / 2, s / 2);
    r.addColorStop(0, 'rgba(255,255,255,0.9)'); r.addColorStop(0.2, 'rgba(255,255,255,0.35)'); r.addColorStop(1, 'rgba(255,255,255,0)');
    g.fillStyle = r; g.fillRect(0, 0, s, s);
  });
}
function gradientTexture() {
  return canvasTexture(256, (g, s) => {
    const r = g.createLinearGradient(0, 0, 0, s);
    r.addColorStop(0, 'rgba(0,0,0,0)'); r.addColorStop(0.6, 'rgba(59,130,246,0.35)'); r.addColorStop(0.75, 'rgba(139,92,246,0.5)'); r.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = r; g.fillRect(0, 0, s, s);
  });
}
