/* Tidemark — noisy weigh-ins, and a trend that glides through them like a tide line. */
function waves(parent) {
  const g = svg(parent, "0 0 100 100", "waves"); g.setAttribute("preserveAspectRatio", "none");
  return [0, 1, 2, 3, 4].map(i => sv(g, "path", { d: "" }));
}
function wavesAt(ps, t) {
  ps.forEach((p, i) => {
    let d = "";
    for (let x = 0; x <= 100; x += 2) { const y = 70 + i * 6 + Math.sin(x * 0.09 + t * (0.6 + i * 0.15) + i) * (2 + i * .6); d += (x ? "L" : "M") + x + "," + y; }
    p.setAttribute("d", d);
  });
}
// Illustrative series: near-level with day-to-day swings (no real user data, and no implied weight-loss outcome).
function series(n = 28) {
  const r = rng(77), raw = [], trend = [], ma = [];
  let lvl = 60, slope = -0.05, b = 0;
  for (let i = 0; i < n; i++) raw.push(60 - i * 0.05 + (r() - 0.5) * 7 + (i % 7 === 5 ? 3 : 0));
  raw.forEach((y, i) => {                        // Holt's linear smoothing, the method the product uses
    if (i === 0) { lvl = y; b = slope; } else { const pl = lvl; lvl = 0.3 * y + 0.7 * (lvl + b); b = 0.1 * (lvl - pl) + 0.9 * b; }
    trend.push(lvl);
    const w = raw.slice(Math.max(0, i - 6), i + 1); ma.push(w.reduce((a, c) => a + c, 0) / w.length);
  });
  return { raw, trend, ma };
}
function chart(parent, withTrend) {
  const c = el("div", "chart", parent), g = svg(c, "0 0 100 70");
  g.setAttribute("preserveAspectRatio", "none");
  sv(g, "line", { class: "axis", x1: 0, y1: 68, x2: 100, y2: 68 });
  const S = series(), X = i => 4 + i * 92 / (S.raw.length - 1), Y = v => 70 - (v - 40) * 2.4;
  const dots = S.raw.map((v, i) => sv(g, "circle", { class: "dot", cx: X(i), cy: Y(v), r: 0.9 }));
  const path = arr => "M" + arr.map((v, i) => `${X(i).toFixed(2)},${Y(v).toFixed(2)}`).join("L");
  const ma = withTrend ? sv(g, "path", { class: "ma", d: path(S.ma) }) : null;
  const tr = withTrend ? sv(g, "path", { class: "trend", d: path(S.trend) }) : null;
  if (withTrend) { const l1 = sv(g, "text", { class: "lab", x: 70, y: Y(S.trend[22]) - 4 }); l1.textContent = "trend"; const l2 = sv(g, "text", { class: "lab", x: 62, y: 64, opacity: .6 }); l2.textContent = "- - moving average"; }
  return { c, dots, ma, tr, S, Y };
}

window.STYLE = {
  transition: "wave", transitionDur: 0.85, grain: 0.04,
  leaks: [{ color: "rgba(255,107,94,.20)", size: 40, range: 15, speed: .15, opacity: .6 }],
  scenes: {
    hook: {
      build(cam, s) {
        const w = waves(cam), c = el("div", "center", cam);
        const m = kinetic(el("div", "wordmark", c), s.on_screen, "rise");
        const tl = el("div", "tideline", c);
        const sub = kinetic(el("div", "sub", c), "the trend, not the noise", "type");
        return { w, m, tl, sub };
      },
      render(cam, t, s, st) {
        camera(cam, t, s.dur, "dolly", .6); wavesAt(st.w, t);
        kineticAt(st.m, t, 0.4); st.tl.style.width = (E.inOut(prog(t, 1.0, 1.2)) * 55) + "%"; kineticAt(st.sub, t, 1.8);
      },
    },
    problem: {
      build(cam, s) {
        const w = waves(cam);
        el("div", "eyebrow", cam, "one number a day");
        const h = kinetic(el("div", "headline", cam), s.on_screen, "rise");
        const v = el("div", "visual", cam), ch = chart(v, false);
        const ro = el("div", "readout", v);
        illus(cam);
        return { w, h, ch, ro };
      },
      render(cam, t, s, st) {
        camera(cam, t, s.dur, "handheld", .35); wavesAt(st.w, t); kineticAt(st.h, t, 0.2);
        const shown = Math.floor(clamp(t / (s.dur * 0.85)) * st.ch.dots.length);
        st.ch.dots.forEach((d, i) => { d.style.opacity = i < shown ? 1 : 0; d.setAttribute("r", i === shown - 1 ? 1.8 : 0.9); });
        const v = st.ch.S.raw[Math.max(0, shown - 1)];
        st.ro.innerHTML = `${v.toFixed(1)}<small> kg</small>`;
      },
    },
    feature: {
      build(cam, s, F) {
        const w = waves(cam);
        const smooth = /smooth|moving average|direction/i.test(s.narration);
        el("div", "eyebrow", cam, smooth ? "Holt's linear smoothing" : "Trend tab");
        const h = kinetic(el("div", "headline", cam), s.on_screen, "rise");
        const v = el("div", "visual", cam);
        if (smooth) { const ch = chart(v, true); illus(cam); return { w, h, ch, smooth }; }
        const d = device(v, F.assets.mobile || s.shot || F.assets.hero, "phone");   // phone frame gets the real mobile capture
        return { w, h, d, smooth };
      },
      render(cam, t, s, st) {
        wavesAt(st.w, t); kineticAt(st.h, t, 0.2);
        if (st.smooth) {
          camera(cam, t, s.dur, "dolly", .8);
          st.ch.dots.forEach(d => d.style.opacity = 0.55);
          drawPath(st.ch.tr, E.inOut(prog(t, 0.6, s.dur * 0.6)));
          drawPath(st.ch.ma, E.inOut(prog(t, 1.0, s.dur * 0.65)));     // the moving average lags behind
        } else {
          camera(cam, t, s.dur, "push", .8);
          const p = E.out3(prog(t, 0.2, 0.8)); st.d.style.transform = `translateY(${(1 - p) * 30}%) rotate(${(1 - p) * -6}deg)`; st.d.style.opacity = p;
          deviceAt(st.d, t, s.dur, 0.25);
        }
      },
    },
    value: {
      build(cam, s) {
        const w = waves(cam), c = el("div", "center", cam);
        const b = kinetic(el("div", "big", c), s.on_screen, "rise");
        const tl = el("div", "tideline", c);
        return { w, b, tl };
      },
      render(cam, t, s, st) { camera(cam, t, s.dur, "pull", .5); wavesAt(st.w, t); kineticAt(st.b, t, 0.2); st.tl.style.width = (E.inOut(prog(t, 1.2, 1)) * 40) + "%"; },
    },
    cta: {
      build(cam, s) {
        const w = waves(cam), c = el("div", "center", cam);
        const m = kinetic(el("div", "wordmark", c), "Tidemark", "rise"); m.style.fontSize = "calc(var(--u)*9)";
        el("div", "tideline", c).style.width = "40%";
        const u = kinetic(el("div", "url", c), s.on_screen.replace("https://", ""), "type");
        u.style.marginTop = "calc(var(--u)*2.4)";
        return { w, m, u };
      },
      render(cam, t, s, st) { camera(cam, t, s.dur, "push", .5); wavesAt(st.w, t); kineticAt(st.m, t, 0.1); kineticAt(st.u, t, 0.7, 1.5); },
    },
  },
};
STYLE.scenes.default = STYLE.scenes.feature;
