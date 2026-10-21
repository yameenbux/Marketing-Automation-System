/* MasjidOne — the khatam (8-point star) lattice draws itself, then becomes a window onto the product. */
function khatam(cx, cy, r) {             // two squares, one rotated 45°: the classic eight-point star
  const sq = a => [0, 1, 2, 3].map(k => { const ang = a + k * Math.PI / 2; return [cx + Math.cos(ang) * r, cy + Math.sin(ang) * r]; });
  const d = pts => "M" + pts.map(p => p.join(",")).join("L") + "Z";
  return d(sq(Math.PI / 4)) + d(sq(0));
}
function latticeSVG(parent, cls, cols = 6) {
  const s = svg(parent, "0 0 100 100", "lattice " + (cls || ""));
  s.setAttribute("preserveAspectRatio", "xMidYMid slice");
  const step = 100 / cols, paths = [];
  for (let y = -1; y <= cols + 1; y++) for (let x = -1; x <= cols + 1; x++) {
    const cx = x * step, cy = y * step;                 // square grid; star points meet their neighbours
    const p = sv(s, "path", { d: khatam(cx, cy, step * 0.54) });
    p._dist = Math.hypot(cx - 50, cy - 50) / 70;
    paths.push(p);
  }
  return paths;
}

window.STYLE = {
  transition: "lattice", transitionDur: 0.9, grain: 0.07,
  leaks: [{ color: "rgba(242,198,109,.35)", size: 55, range: 18, speed: .25, opacity: .55 }],
  scenes: {
    hook: {
      build(cam, s) {
        const paths = latticeSVG(cam);
        const c = el("div", "center", cam);
        const b = kinetic(c, s.on_screen, "letters", "brand");
        const r = el("div", "rule", c);
        return { paths, b, r };
      },
      render(cam, t, s, st) {
        camera(cam, t, s.dur, "crane");
        const recede = 1 - 0.7 * E.inOut(prog(t, 2.0, 1.2));   // lattice steps back once the name arrives
        st.paths.forEach(p => { drawPath(p, E.out3(prog(t, p._dist * 1.2, 1.4))); p.style.opacity = recede; });
        kineticAt(st.b, t, 1.0);
        st.r.style.width = (E.inOut(prog(t, 1.6, 1)) * 40) + "%";
      },
    },
    problem: {
      build(cam, s) {
        latticeSVG(cam, "faint", 5);
        el("div", "eyebrow", cam, "The week, today");
        const h = kinetic(el("div", "headline", cam), s.on_screen, "mask");
        const v = el("div", "visual", cam), wrap = el("div", "tools", v);
        const lines = svg(wrap, "0 0 100 100"); lines.setAttribute("preserveAspectRatio", "none");
        const names = ["Registers", "Fees", "Prayer times", "Donations", "Website", "Hall screens"];
        const pos = [[8, 12], [58, 6], [30, 40], [70, 46], [6, 72], [52, 82]];
        const tools = names.map((n, i) => { const d = el("div", "tool", wrap, n); d.style.left = pos[i][0] + "%"; d.style.top = pos[i][1] + "%"; return d; });
        const ls = [[0, 2], [1, 3], [2, 4], [3, 5], [0, 1], [4, 5]].map(([a, b]) => sv(lines, "line", { x1: pos[a][0] + 12, y1: pos[a][1] + 5, x2: pos[b][0] + 12, y2: pos[b][1] + 5 }));
        illus(cam);
        return { h, tools, ls, pos };
      },
      render(cam, t, s, st) {
        camera(cam, t, s.dur, "drift");
        kineticAt(st.h, t, 0.2);
        st.tools.forEach((d, i) => {   // tools drift apart; the links between them break
          const p = E.out3(prog(t, 0.4 + i * 0.12, 0.6)), drift = E.inOut(prog(t, 1.6, s.dur));
          d.style.opacity = p; d.style.transform = `translate(${(st.pos[i][0] - 35) * drift * 0.25}%, ${(st.pos[i][1] - 45) * drift * 0.6}%)`;
        });
        st.ls.forEach((l, i) => { l.style.opacity = clamp(1 - prog(t, 1.2 + i * 0.25, 0.5)); });
      },
    },
    feature: {
      build(cam, s, F) {
        el("div", "eyebrow", cam, "One system");
        const h = kinetic(el("div", "headline", cam), s.on_screen, "mask");
        const v = el("div", "visual", cam), w = el("div", "window", v), pane = el("div", "pane", w);
        const img = el("img", "", pane); img.src = s.shot || F.assets.hero;
        const frame = svg(w, "0 0 100 100"), star = sv(frame, "path", { d: khatam(50, 50, 49) });
        return { h, pane, img, star };
      },
      render(cam, t, s, st) {
        camera(cam, t, s.dur, "push");
        kineticAt(st.h, t, 0.25);
        const p = E.inOut(prog(t, 0.3, 1.4));
        drawPath(st.star, E.out3(prog(t, 0.1, 1.2)));
        st.pane.style.clipPath = starPolygon(Math.max(0.1, p * 50), 50, 50, 8, 0.72, 1);
        st.img.style.transform = `translateY(${-E.inOut(prog(t, 0.6, s.dur)) * 18}%)`;
      },
    },
    value: {
      build(cam, s) {
        latticeSVG(cam, "faint", 4);
        const c = el("div", "center", cam);
        el("div", "rule", c).style.width = "18%";
        const b = kinetic(el("div", "big", c), s.on_screen, "letters");
        const r = el("div", "rule", c); r.style.width = "18%";
        return { b };
      },
      render(cam, t, s, st) { camera(cam, t, s.dur, "pull"); kineticAt(st.b, t, 0.2, 2.2); },
    },
    cta: {
      build(cam, s) {
        const paths = latticeSVG(cam, "faint", 5);
        const c = el("div", "center", cam);
        el("div", "eyebrow", c, "Find out more").style.position = "static";
        const u = kinetic(el("div", "url", c), s.on_screen.replace("https://", ""), "rise");
        el("div", "rule", c).style.width = "30%";
        const b = kinetic(el("div", "brand", c), "MasjidOne", "letters");
        b.style.fontSize = "calc(var(--u)*5)";
        return { paths, u, b };
      },
      render(cam, t, s, st) {
        camera(cam, t, s.dur, "push", .6);
        st.paths.forEach(p => drawPath(p, 1));
        kineticAt(st.u, t, 0.2); kineticAt(st.b, t, 0.8);
      },
    },
  },
};
STYLE.scenes.default = STYLE.scenes.feature;
