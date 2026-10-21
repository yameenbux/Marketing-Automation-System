/* Domi — a cancelled slot, a route line across the round, a refilled diary. */
const TIMES = ["09:00", "10:00", "11:00", "12:30", "14:00", "15:30"];

function diary(parent, gapIndex) {
  const d = el("div", "diary", parent), slots = [];
  TIMES.forEach((tm, i) => {
    el("div", "time", d, tm);
    const s = el("div", "slot" + (i === gapIndex ? " gap" : ""), d, i === gapIndex ? "" : "Home visit");
    slots.push(s);
  });
  return slots;
}

window.STYLE = {
  transition: "route", transitionDur: 0.7, grain: 0.035,
  leaks: [{ color: "rgba(229,139,95,.18)", size: 45, range: 25, speed: .2, opacity: .6 }],
  scenes: {
    hook: {
      build(cam, s) {
        const c = el("div", "center", cam);
        const b = el("div", "brandmark", c, 'Domi<span class="dot">.</span>');
        const line = kinetic(el("div", "annot", c), "the diary that refills itself", "type");
        line.style.textAlign = "center";
        return { b, line };
      },
      render(cam, t, s, st) {
        camera(cam, t, s.dur, "push", 0.8);
        const p = E.outExpo(prog(t, 0.2, 0.9));
        st.b.style.opacity = p; st.b.style.transform = `translateY(${(1 - p) * 30}px)`; st.b.style.letterSpacing = `${(1 - p) * 0.3 - 0.02}em`;
        kineticAt(st.line, t, 1.1);
      },
    },
    problem: {
      build(cam, s) {
        el("div", "eyebrow", cam, "11:00 — cancelled");
        const h = kinetic(el("div", "headline", cam), s.on_screen, "rise");
        const v = el("div", "visual", cam);
        const slots = diary(v, -1);
        const strike = el("div", "strike", slots[2]);
        illus(cam);
        return { h, slots, strike };
      },
      render(cam, t, s, st) {
        camera(cam, t, s.dur, "handheld", .5);
        kineticAt(st.h, t, 0.15);
        st.slots.forEach((sl, i) => { const p = E.out3(prog(t, 0.2 + i * 0.07, 0.4)); sl.style.opacity = p; sl.style.transform = `translateX(${(1 - p) * 20}%)`; });
        const k = E.inOut(prog(t, 1.2, 0.5));
        st.strike.style.transform = `scaleX(${k})`;
        st.slots[2].style.opacity = 1 - 0.55 * k;
      },
    },
    feature: {
      build(cam, s, F, idx) {
        const isRefill = /rank|candidate/i.test(s.narration);
        el("div", "eyebrow", cam, isRefill ? "Refill engine" : "Cancel by text");
        const h = kinetic(el("div", "headline", cam), s.on_screen, "mask");
        const v = el("div", "visual", cam);
        if (isRefill) {
          const m = el("div", "map", v), g = svg(m, "0 0 100 100");
          g.setAttribute("preserveAspectRatio", "xMidYMid meet");
          const r = rng(42), houses = [];
          for (let i = 0; i < 42; i++) houses.push(sv(g, "rect", { class: "house", x: 4 + r() * 88, y: 4 + r() * 70, width: 2.2, height: 2.2, rx: .4 }));
          const pts = [[8, 44], [22, 60], [38, 34], [54, 56], [70, 28], [86, 46]];   // a winding round, not a chart
          const route = sv(g, "path", { class: "route", d: "M" + pts.map(p => p.join(",")).join("L") });
          const van = sv(g, "circle", { class: "van", r: 2.2, cx: 8, cy: 44 });
          const chips = el("div", "chips", v);
          const labels = ["clinical priority", "locality", "days waiting", "preferred clinician"];   // the verified ranking criteria
          const cs = labels.map(l => el("div", "chip", chips, l));
          illus(cam);
          return { h, route, van, cs, isRefill };
        }
        const slots = diary(v, 2);
        const sms = el("div", "sms", v, "CANCEL");
        const fill = el("div", "fill", slots[2], "Refilled");
        illus(cam);
        return { h, slots, sms, fill, isRefill };
      },
      render(cam, t, s, st) {
        kineticAt(st.h, t, 0.15);
        if (st.isRefill) {
          camera(cam, t, s.dur, "drift", 1.2);
          const p = E.inOut(prog(t, 0.5, s.dur * 0.6));
          drawPath(st.route, p);
          const L = st.route.getTotalLength(), pt = st.route.getPointAtLength(L * p);
          st.van.setAttribute("cx", pt.x); st.van.setAttribute("cy", pt.y);
          st.cs.forEach((c, i) => { const q = E.outBack(prog(t, 1.2 + i * 0.45, 0.4)); c.style.opacity = clamp(q); c.style.transform = `scale(${0.6 + 0.4 * q})`; });
        } else {
          camera(cam, t, s.dur, "push", .6);
          const a = E.outBack(prog(t, 0.4, 0.5)); st.sms.style.transform = `scale(${a})`; st.sms.style.opacity = clamp(a);
          st.fill.style.transform = `scaleX(${E.inOut(prog(t, 1.8, 0.8))})`;
        }
      },
    },
    value: {
      build(cam, s) {
        const c = el("div", "center", cam);
        const b = kinetic(el("div", "big", c), s.on_screen, "mask");
        const a = kinetic(el("div", "annot", c), "find who fits → ask by text → book the first yes", "type");
        return { b, a };
      },
      render(cam, t, s, st) { camera(cam, t, s.dur, "dolly", .6); kineticAt(st.b, t, 0.2); kineticAt(st.a, t, 1.6, 1.6); },
    },
    cta: {
      build(cam, s) {
        const c = el("div", "center", cam);
        el("div", "brandmark", c, 'Domi<span class="dot">.</span>').style.fontSize = "calc(var(--u)*8)";
        const u = kinetic(el("div", "url", c), s.on_screen.replace("https://", ""), "rise");
        const ln = el("div", "", c); ln.style.cssText = "height:3px;background:var(--accent);margin-top:calc(var(--u)*2)";
        return { u, ln };
      },
      render(cam, t, s, st) { camera(cam, t, s.dur, "push", .5); kineticAt(st.u, t, 0.2); st.ln.style.width = (E.inOut(prog(t, 0.6, 0.8)) * 60) + "%"; },
    },
  },
};
STYLE.scenes.default = STYLE.scenes.feature;
