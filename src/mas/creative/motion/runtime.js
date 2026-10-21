/* Deterministic motion runtime. Everything is a pure function of time t (seconds), so
 * Playwright can call renderAt(t) for each frame and screenshot it. No timers, no CSS animations. */
"use strict";

const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const prog = (t, start, dur) => clamp((t - start) / dur);
const lerp = (a, b, p) => a + (b - a) * p;
const E = {
  lin: p => p,
  out3: p => 1 - Math.pow(1 - p, 3),
  out5: p => 1 - Math.pow(1 - p, 5),
  inOut: p => (p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2),
  outExpo: p => (p >= 1 ? 1 : 1 - Math.pow(2, -10 * p)),
  outBack: p => { const c1 = 1.9, c3 = c1 + 1; return 1 + c3 * Math.pow(p - 1, 3) + c1 * Math.pow(p - 1, 2); },
  inExpo: p => (p <= 0 ? 0 : Math.pow(2, 10 * p - 10)),
};
function rng(seed) { let s = seed >>> 0 || 1; return () => { s = (Math.imul(s, 1664525) + 1013904223) >>> 0; return s / 4294967296; }; }
function noise1(x, seed = 7) {           // smooth value noise for handheld camera
  const i = Math.floor(x), f = x - i, h = n => { const r = rng(n * 9973 + seed); return r() * 2 - 1; };
  const u = f * f * (3 - 2 * f);
  return lerp(h(i), h(i + 1), u);
}
const el = (tag, cls, parent, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; if (parent) parent.appendChild(e); return e; };
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

/* ---------- kinetic type ---------- */
function kinetic(parent, text, mode, cls) {
  const box = el("div", "kt kt-" + mode + (cls ? " " + cls : ""), parent);
  const words = String(text).split(/\s+/).filter(Boolean);
  box._units = [];
  words.forEach((w, wi) => {
    const wrap = el("span", "kw", box);
    if (mode === "letters" || mode === "type") {
      [...w].forEach(ch => box._units.push(el("span", "kc", wrap, esc(ch))));
    } else if (mode === "mask") {
      wrap.style.overflow = "hidden"; wrap.style.display = "inline-block"; wrap.style.verticalAlign = "top";
      box._units.push(el("span", "kc", wrap, esc(w)));
    } else {
      box._units.push(el("span", "kc", wrap, esc(w)));
    }
    if (wi < words.length - 1) box.appendChild(document.createTextNode(" "));
  });
  box._mode = mode;
  return box;
}
function kineticAt(box, t, start = 0, speed = 1) {
  const m = box._mode, n = box._units.length;
  box._units.forEach((u, i) => {
    let st, p;
    switch (m) {
      case "rise":
        p = E.out3(prog(t, start + i * 0.07 / speed, 0.45));
        u.style.opacity = p; u.style.transform = `translateY(${(1 - p) * 0.55}em)`; break;
      case "mask":
        p = E.out5(prog(t, start + i * 0.06 / speed, 0.6));
        u.style.transform = `translateY(${(1 - p) * 110}%)`; break;
      case "letters":
        p = E.out3(prog(t, start + i * 0.022 / speed, 0.55));
        u.style.opacity = p; u.style.filter = `blur(${(1 - p) * 10}px)`;
        u.style.transform = `translateY(${(1 - p) * 0.25}em) scale(${1.15 - 0.15 * p})`; break;
      case "slam":
        p = prog(t, start + i * 0.09 / speed, 0.28);
        st = E.outBack(p);
        u.style.opacity = clamp(p * 3); u.style.transform = `scale(${lerp(2.4, 1, st)}) rotate(${(1 - p) * -4}deg)`; break;
      case "type":
        u.style.opacity = t >= start + i * 0.035 / speed ? 1 : 0; break;
      default:
        p = E.out3(prog(t, start + i * 0.05, 0.5)); u.style.opacity = p;
    }
  });
  return box._units.length ? (m === "type" ? start + n * 0.035 / speed : start + n * 0.07 / speed + 0.5) : start;
}

/* ---------- camera moves ---------- */
function camera(node, t, dur, move, amt = 1) {
  const p = clamp(t / Math.max(dur, 0.01));
  let tf = "";
  switch (move) {
    case "push": tf = `scale(${1 + 0.07 * amt * E.inOut(p)})`; break;
    case "pull": tf = `scale(${1.08 - 0.08 * amt * E.inOut(p)})`; break;
    case "crane": tf = `translateY(${(0.5 - E.inOut(p)) * 4 * amt}%) scale(1.06)`; break;
    case "dolly": tf = `translateX(${(0.5 - E.inOut(p)) * 6 * amt}%) scale(1.08)`; break;
    case "handheld": tf = `translate(${noise1(t * 1.3, 3) * 0.5 * amt}%, ${noise1(t * 1.1, 11) * 0.5 * amt}%) rotate(${noise1(t * 0.9, 5) * 0.5 * amt}deg) scale(1.04)`; break;
    case "drift": tf = `translate(${Math.sin(t * 0.4) * 0.6 * amt}%, ${Math.cos(t * 0.33) * 0.6 * amt}%) scale(1.03)`; break;
    default: tf = "none";
  }
  node.style.transform = tf;
}

/* ---------- devices (real product screenshots) ---------- */
function device(parent, src, kind) {
  const d = el("div", "device device-" + kind, parent);
  const scr = el("div", "screen", d);
  const img = el("img", "", scr); img.src = src; d._img = img;
  if (kind === "phone") el("div", "notch", d);
  if (kind === "laptop") el("div", "base", d);
  return d;
}
function deviceAt(d, t, dur, scroll = 0.35) {   // slow scroll inside the screen, like a real recording
  const p = E.inOut(clamp(t / Math.max(dur, 0.1)));
  d._img.style.transform = `translateY(${-p * scroll * 100}%)`;
}

/* ---------- illustrative scenes are labelled; real screenshots are not ---------- */
const illus = parent => el("div", "illus", parent, "Illustration");

/* ---------- SVG ---------- */
const SVGNS = "http://www.w3.org/2000/svg";
function svg(parent, vb, cls) { const s = document.createElementNS(SVGNS, "svg"); s.setAttribute("viewBox", vb); if (cls) s.setAttribute("class", cls); parent.appendChild(s); return s; }
function sv(parent, tag, attrs) { const e = document.createElementNS(SVGNS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); parent.appendChild(e); return e; }
function drawPath(p, frac) {            // stroke-draw animation for any SVG geometry
  if (p._len == null) { p._len = p.getTotalLength ? p.getTotalLength() : 1000; p.style.strokeDasharray = p._len; }
  p.style.strokeDashoffset = p._len * (1 - clamp(frac));
}

/* ---------- texture: grain, vignette, light leaks ---------- */
let grainCanvas, grainCtx, grainData;
function grainAt(frame, amount) {
  if (!amount) return;
  if (!grainCanvas) {
    grainCanvas = el("canvas", "grain", document.getElementById("stage"));
    grainCanvas.width = 270; grainCanvas.height = 480;
    grainCtx = grainCanvas.getContext("2d"); grainData = grainCtx.createImageData(270, 480);
  }
  const r = rng(frame * 7919 + 13), d = grainData.data;
  for (let i = 0; i < d.length; i += 4) { const v = r() * 255; d[i] = d[i + 1] = d[i + 2] = v; d[i + 3] = amount * 255; }
  grainCtx.putImageData(grainData, 0, 0);
}
function leaksAt(t, leaks) {
  (leaks || []).forEach((lk, i) => {
    if (!lk._el) lk._el = el("div", "leak", document.getElementById("stage"));
    const x = 50 + Math.sin(t * lk.speed + i * 2.1) * lk.range, y = 50 + Math.cos(t * lk.speed * 0.8 + i) * lk.range;
    lk._el.style.background = `radial-gradient(circle at ${x}% ${y}%, ${lk.color} 0%, transparent ${lk.size}%)`;
    lk._el.style.opacity = lk.opacity * (0.7 + 0.3 * Math.sin(t * 0.7 + i));
  });
}

/* ---------- transitions (applied to outgoing A and incoming B, p in 0..1) ---------- */
function starPolygon(r, cx = 50, cy = 50, points = 8, inner = 0.72, aspect = window.ASPECT || 1) {
  const pts = [];
  for (let i = 0; i < points * 2; i++) {
    const a = (Math.PI / points) * i - Math.PI / 2, rr = i % 2 ? r * inner : r;
    pts.push(`${cx + Math.cos(a) * rr}% ${cy + Math.sin(a) * rr * aspect}%`);
  }
  return `polygon(${pts.join(",")})`;
}
const TRANSITIONS = {
  fade(A, B, p) { B.style.opacity = E.inOut(p); },
  lattice(A, B, p) {   // 8-point star iris opens from the centre
    const r = E.inOut(p) * 120;
    B.style.clipPath = starPolygon(Math.max(r, 0.01)); B.style.opacity = 1;
    A.style.filter = `brightness(${1 - 0.4 * p})`;
  },
  route(A, B, p) {     // a line sweeps across and leaves the new scene behind it
    const x = E.inOut(p) * 100;
    B.style.clipPath = `inset(0 ${100 - x}% 0 0)`; B.style.opacity = 1;
    const ln = document.getElementById("wipe-line"); ln.style.left = x + "%"; ln.style.opacity = p > 0 && p < 1 ? 1 : 0;
  },
  bloom(A, B, p) {     // overexposed flash, like a ring light
    const k = Math.sin(p * Math.PI);
    A.style.opacity = 1 - E.inOut(p); B.style.opacity = E.inOut(p);
    document.getElementById("flash").style.opacity = k * 0.85;
    A.style.filter = `blur(${p * 12}px) brightness(${1 + k})`; B.style.filter = `blur(${(1 - p) * 12}px)`;
  },
  wave(A, B, p) {      // a tide line rises and floods the frame
    const lvl = 110 - E.inOut(p) * 120, pts = [];
    for (let i = 0; i <= 24; i++) { const x = i / 24 * 100; pts.push(`${x}% ${lvl + Math.sin(i * 0.8 + p * 9) * 3}%`); }
    B.style.clipPath = `polygon(${pts.join(",")}, 100% 100%, 0% 100%)`; B.style.opacity = 1;
  },
  shutter(A, B, p) {   // a roller shutter comes down, then goes back up on the next scene
    const s = document.getElementById("shutter");
    const down = p < 0.5 ? E.out3(p * 2) : 1 - E.inOut((p - 0.5) * 2);
    s.style.transform = `translateY(${(down - 1) * 100}%)`;
    A.style.opacity = p < 0.5 ? 1 : 0; B.style.opacity = p < 0.5 ? 0 : 1;
  },
  whip(A, B, p) {
    const q = E.inOut(p);
    A.style.transform = `translateX(${-q * 60}%)`; A.style.filter = `blur(${Math.sin(p * Math.PI) * 24}px)`;
    B.style.transform = `translateX(${(1 - q) * 60}%)`; B.style.filter = `blur(${Math.sin(p * Math.PI) * 24}px)`; B.style.opacity = 1;
  },
};

/* ---------- film assembly ---------- */
const FILM = window.FILM;
const STYLE = window.STYLE;
let SCENES = [];

function captionsAt(t) {
  const cap = document.getElementById("cap");
  let txt = "";
  for (const s of FILM.scenes) {
    if (t >= s.start && t < s.start + s.dur) {
      const lt = t - s.start;
      const c = (s.captions || []).find(c => lt >= c[0] && lt < c[1]);
      txt = c ? c[2] : "";
    }
  }
  if (cap._txt !== txt) { cap._txt = txt; cap.innerHTML = txt ? `<span>${esc(txt)}</span>` : ""; }
}

function build() {
  const stage = document.getElementById("stage");
  document.body.classList.add("f-" + FILM.format, "p-" + FILM.slug);
  window.ASPECT = FILM.width / FILM.height;
  FILM.scenes.forEach((s, i) => {
    const root = el("section", "scene role-" + s.role, stage);
    const cam = el("div", "cam", root);
    root._cam = cam; root._scene = s; root.style.opacity = 0;
    const builder = (STYLE.scenes[s.role] || STYLE.scenes.default);
    root._state = builder.build(cam, s, FILM) || {};
    SCENES.push(root);
  });
  el("div", "vignette", stage);
  el("div", "", stage).id = "flash";
  el("div", "", stage).id = "wipe-line";
  const sh = el("div", "", stage); sh.id = "shutter";
  el("div", "", stage).id = "cap";
  el("div", "progress", stage).id = "bar";
  if (STYLE.init) STYLE.init(stage, FILM);
}

/* Auto-fit: shrink any headline that would collide with its scene's visual (runs once, after fonts load). */
let FITTED = false;
function fitHeadlines() {
  SCENES.forEach(root => {
    const h = root.querySelector(".headline"), v = root.querySelector(".visual");
    if (!h) return;
    const H = FILM.height;
    const beside = v && v.offsetLeft >= h.offsetLeft + h.offsetWidth * 0.9;      // landscape: visual is to the right
    const limit = !v ? H * 0.4 : beside ? H * 0.58 : (v.offsetTop - h.offsetTop - H * 0.02);
    let size = parseFloat(getComputedStyle(h).fontSize), guard = 0;
    while (h.offsetHeight > limit && size > 14 && guard++ < 40) { size *= 0.94; h.style.fontSize = size + "px"; }
  });
  FITTED = true;
}

window.renderAt = function (t) {
  if (!FITTED) fitHeadlines();
  const frame = Math.round(t * FILM.fps);
  const TR = STYLE.transitionDur || 0.6;
  const trans = TRANSITIONS[STYLE.transition] || TRANSITIONS.fade;
  SCENES.forEach(root => { root.style.opacity = 0; root.style.clipPath = "none"; root.style.filter = "none"; root.style.transform = "none"; });
  document.getElementById("flash").style.opacity = 0;
  document.getElementById("wipe-line").style.opacity = 0;
  document.getElementById("shutter").style.transform = "translateY(-100%)";
  SCENES.forEach((root, i) => {
    const s = root._scene, lt = t - s.start;
    if (lt < -TR || lt > s.dur) return;
    root.style.opacity = 1;
    const builder = (STYLE.scenes[s.role] || STYLE.scenes.default);
    builder.render(root._cam, Math.max(0, lt), s, root._state, FILM, frame);
  });
  // transition window at the start of each scene (except the first)
  SCENES.forEach((root, i) => {
    if (i === 0) return;
    const s = root._scene, lt = t - s.start;
    if (lt >= 0 && lt < TR) {
      const A = SCENES[i - 1]; A.style.opacity = 1;
      trans(A, root, lt / TR);
    } else if (lt >= 0 && lt < s.dur) {
      SCENES[i - 1].style.opacity = 0;
    }
  });
  captionsAt(t);
  document.getElementById("bar").style.width = (clamp(t / FILM.total) * 100) + "%";
  leaksAt(t, STYLE.leaks);
  grainAt(frame, STYLE.grain || 0);
  if (STYLE.after) STYLE.after(t, frame);
  return true;
};

window.addEventListener("DOMContentLoaded", () => { build(); window.READY = document.fonts.ready.then(() => true); });
