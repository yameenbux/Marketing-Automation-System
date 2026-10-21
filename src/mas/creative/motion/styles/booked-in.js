/* Booked In — DMs pile up after midnight; then a page that is hers alone. */
function bokeh(parent, n, seed) {
  const b = el("div", "bokeh", parent), r = rng(seed), dots = [];
  for (let i = 0; i < n; i++) {
    const d = el("i", "", b), s = 6 + r() * 22;
    d.style.width = d.style.height = `calc(var(--u)*${s})`;
    dots.push({ d, x: r() * 100, y: r() * 100, sp: 0.4 + r() * 1.2, ph: r() * 6 });
  }
  return dots;
}
function bokehAt(dots, t, focus) {   // rack focus: blur the background more while text is sharp
  dots.forEach(o => {
    o.d.style.left = (o.x + Math.sin(t * 0.2 * o.sp + o.ph) * 4) + "%";
    o.d.style.top = (o.y - t * o.sp * 0.8) % 110 + "%";
    o.d.style.filter = `blur(${6 + 10 * focus}px)`; o.d.style.opacity = 0.35 + 0.35 * Math.sin(t * o.sp + o.ph) ** 2;
  });
}

window.STYLE = {
  transition: "bloom", transitionDur: 0.8, grain: 0.05,
  leaks: [{ color: "rgba(231,166,176,.28)", size: 50, range: 20, speed: .3, opacity: .7 },
          { color: "rgba(210,165,106,.22)", size: 40, range: 30, speed: .18, opacity: .5 }],
  scenes: {
    hook: {
      build(cam, s) {
        const dots = bokeh(cam, 18, 3), c = el("div", "center", cam);
        const w = kinetic(el("div", "wordmark", c), s.on_screen, "letters");
        const sw = el("div", "swash", c);
        const sub = kinetic(el("div", "wordmark-sub", c), "a booking page that's yours", "rise");
        return { dots, w, sw, sub };
      },
      render(cam, t, s, st) {
        camera(cam, t, s.dur, "push", .7); bokehAt(st.dots, t, 1 - E.inOut(prog(t, 0, 1.5)) * .5);
        kineticAt(st.w, t, 0.3, 1.4); st.sw.style.width = (E.inOut(prog(t, 1.2, 1)) * 50) + "%"; kineticAt(st.sub, t, 1.6);
      },
    },
    problem: {
      build(cam, s) {
        const dots = bokeh(cam, 10, 9);
        el("div", "eyebrow", cam, "23:47");
        const h = kinetic(el("div", "headline", cam), s.on_screen, "rise");
        const v = el("div", "visual", cam), th = el("div", "thread", v);
        const msgs = [["are you free thursday?", "23:41"], ["what time do you finish?", "23:44"], ["is 6 ok? x", "23:52"], ["?", "00:31"]];
        const dms = msgs.map(([m, ts]) => el("div", "dm", th, `${esc(m)}<span class="ts">${ts}</span>`));
        const seen = el("div", "seen", th, "Seen");
        illus(cam);
        return { dots, h, dms, seen };
      },
      render(cam, t, s, st) {
        camera(cam, t, s.dur, "handheld", .4); bokehAt(st.dots, t, 1);
        kineticAt(st.h, t, 0.2);
        st.dms.forEach((d, i) => { const p = E.outBack(prog(t, 0.6 + i * 0.55, 0.4)); d.style.opacity = clamp(p); d.style.transform = `scale(${0.7 + 0.3 * p})`; });
        const fade = E.inOut(prog(t, s.dur - 1.4, 0.9));
        st.dms.forEach(d => d.style.filter = `grayscale(${fade}) blur(${fade * 1.5}px)`);
        st.seen.style.opacity = 0.6 * fade;
      },
    },
    feature: {
      build(cam, s) {
        const dots = bokeh(cam, 8, 21);
        const live = /live|save/i.test(s.narration);
        el("div", "eyebrow", cam, live ? "Her page" : "Thursday, 14:00");
        const h = kinetic(el("div", "headline", cam), s.on_screen, "rise");
        const v = el("div", "visual", cam);
        illus(cam);
        if (live) {
          const card = el("div", "card", v);
          ["Lash lift", "Infills", "Brow lamination"].forEach(n => el("div", "row", card, `<span>${n}</span><span style="opacity:.6">—</span>`));
          const r = el("div", "row", card); el("span", "", r, "Changes"); const pill = el("span", "pill", r, "Save");
          const rip = el("div", "ripple", card); rip.style.right = "4%"; rip.style.bottom = "2%";
          return { dots, h, live, pill, rip, card };
        }
        const slot = el("div", "slotbig", v, "Thu 14:00");
        const a = el("div", "hand", v, "Client A"), b = el("div", "hand", v, "Client B");
        const taken = el("div", "taken", v, "Booked · second request refused");
        return { dots, h, live, slot, a, b, taken };
      },
      render(cam, t, s, st) {
        bokehAt(st.dots, t, 1); kineticAt(st.h, t, 0.2);
        if (st.live) {
          camera(cam, t, s.dur, "push", .8);
          const tap = prog(t, 1.4, 0.8);
          st.rip.style.transform = `scale(${0.2 + tap * 1.6})`; st.rip.style.opacity = tap > 0 && tap < 1 ? 1 - tap : 0;
          const on = t > 1.6;
          st.pill.classList.toggle("on", on); st.pill.textContent = on ? "Live" : "Save";
          st.card.style.opacity = E.out3(prog(t, 0.3, 0.6));
        } else {
          camera(cam, t, s.dur, "drift", .8);
          const p = E.inOut(prog(t, 0.5, 1.2));
          st.a.style.left = lerp(-10, 18, p) + "%"; st.b.style.right = lerp(-10, 18, p) + "%";
          const bounce = E.outBack(prog(t, 1.8, 0.5));
          st.b.style.transform = `translateX(${bounce * 40}%)`; st.b.style.opacity = 1 - 0.6 * bounce;
          st.a.style.background = t > 1.8 ? "var(--accent)" : ""; st.a.style.color = t > 1.8 ? "var(--plum)" : "";
          st.taken.style.opacity = E.out3(prog(t, 2.0, 0.5));
        }
      },
    },
    value: {
      build(cam, s) {
        const dots = bokeh(cam, 14, 33), c = el("div", "center lines", cam);
        const parts = s.narration.replace(/\.$/, "").split(/,\s*(?:and\s+)?/);   // "no commission", "no marketplace", "nobody else…"
        const lns = parts.map(p => { const d = el("div", "", c); return el("span", "ln", d, esc(p.trim())); });
        return { dots, lns };
      },
      render(cam, t, s, st) {
        camera(cam, t, s.dur, "pull", .6); bokehAt(st.dots, t, 1);
        st.lns.forEach((l, i) => { const p = E.out3(prog(t, 0.3 + i * 0.9, 0.7)); l.style.opacity = p; l.style.transform = `translateY(${(1 - p) * 20}px)`; l.style.setProperty("--k", E.inOut(prog(t, 0.7 + i * 0.9, 0.6))); });
      },
    },
    cta: {
      build(cam, s) {
        const dots = bokeh(cam, 18, 5), c = el("div", "center", cam);
        const w = kinetic(el("div", "wordmark", c), "Booked In", "letters");
        el("div", "swash", c).style.width = "50%";
        const sub = kinetic(el("div", "wordmark-sub", c), s.on_screen.replace(/\.$/, ""), "rise");
        return { dots, w, sub };
      },
      render(cam, t, s, st) { camera(cam, t, s.dur, "push", .5); bokehAt(st.dots, t, .6); kineticAt(st.w, t, 0.1, 1.6); kineticAt(st.sub, t, 0.9); },
    },
  },
};
STYLE.scenes.default = STYLE.scenes.feature;
