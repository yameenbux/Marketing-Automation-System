/* Bolton Vouched — the shutter goes up on a local shopfront; recommendations stop scrolling away. */
function thump(cam, t, at) {             // stamp impact: a short, decaying shake
  const k = prog(t, at, 0.35);
  if (k <= 0 || k >= 1) return "";
  const a = (1 - k) * 1.6;
  return ` translate(${Math.sin(k * 60) * a}%, ${Math.cos(k * 47) * a}%)`;
}

window.STYLE = {
  transition: "shutter", transitionDur: 0.9, grain: 0.06,
  leaks: [{ color: "rgba(224,176,74,.22)", size: 45, range: 20, speed: .22, opacity: .6 }],
  scenes: {
    hook: {
      build(cam, s) {
        const c = el("div", "center", cam), sign = el("div", "sign", c);
        el("div", "t1", sign, "Bolton<br>Vouched");
        const t2 = kinetic(el("div", "t2", sign), "local people, vouched for", "rise");
        const sh = el("div", "hookshutter", cam);
        return { sign, t2, sh };
      },
      render(cam, t, s, st) {
        const up = E.inOut(prog(t, 0.5, 1.1));
        st.sh.style.transform = `translateY(${-up * 105}%)`;
        const k = E.outBack(prog(t, 1.4, 0.45));
        st.sign.style.transform = `scale(${lerp(1.25, 1, k)})`;
        cam.style.transform = "scale(1.03)" + thump(cam, t, 1.5);
        kineticAt(st.t2, t, 1.9);
      },
    },
    problem: {
      build(cam, s) {
        el("div", "eyebrow", cam, "Every week");
        const h = kinetic(el("div", "headline", cam), s.on_screen, "slam");
        const v = el("div", "visual", cam), chat = el("div", "chat", v);
        el("div", "head", chat, "Local group chat");
        const feed = el("div", "feed", chat);
        const asks = ["Anyone know a good electrician in BL3?", "Can anyone recommend a plumber?", "Need a man and van Saturday", "Who did your roof?",
                      "Anyone know a good electrician in BL3?", "Joiner recommendations please", "anyone??", "Mechanic near Farnworth?", "Bump"];
        const bs = asks.map((a, i) => el("div", "bubble" + (i % 3 === 2 ? " alt" : ""), feed, esc(a)));
        illus(cam);
        return { h, feed, bs };
      },
      render(cam, t, s, st) {
        camera(cam, t, s.dur, "handheld", .6);
        kineticAt(st.h, t, 0.15);
        st.bs.forEach((b, i) => { b.style.opacity = E.out3(prog(t, 0.3 + i * 0.3, 0.25)); });
        st.feed.style.transform = `translateY(${-E.inExpo(prog(t, 1.4, s.dur - 1.2)) * 140}%)`;   // ...and away they scroll
      },
    },
    feature: {
      build(cam, s) {
        const cats = /categor|groups/i.test(s.narration);
        el("div", "eyebrow", cam, cats ? "What's in it" : "One tap");
        const h = kinetic(el("div", "headline", cam), s.on_screen, "slam");
        const v = el("div", "visual", cam);
        illus(cam);
        if (cats) {
          const box = el("div", "", v), n = el("div", "count", box, "0"), st = el("div", "stickers", box);
          const groups = ["Home & trades", "Repairs", "Moving", "Events", "Lessons", "Vehicles", "Transport"];  // the seven groups (verified)
          return { h, cats, n, ss: groups.map(g => el("div", "sticker", st, esc(g))) };
        }
        const p = el("div", "picker", v);
        const picks = [["Trade", "Plumber"], ["Area", "BL3"]].map(([a, b]) => el("div", "pick", p, `<span>${a}</span><span>${b}</span>`));
        const btns = el("div", "btns", p);
        const call = el("div", "btn", btns, "Call"), wa = el("div", "btn", btns, "WhatsApp");
        const rip = el("div", "rip", wa);
        return { h, cats, picks, call, wa, rip };
      },
      render(cam, t, s, st) {
        kineticAt(st.h, t, 0.15);
        if (st.cats) {
          const k = E.out5(prog(t, 0.4, 1.6));
          st.n.textContent = Math.round(43 * k);
          cam.style.transform = "scale(1.02)" + thump(cam, t, 2.0);
          st.ss.forEach((x, i) => { const q = E.outBack(prog(t, 2.0 + i * 0.22, 0.3)); x.style.opacity = clamp(q * 2); x.style.transform = `scale(${lerp(1.8, 1, q)}) rotate(${(i % 2 ? 3 : -3) * q}deg)`; });
        } else {
          camera(cam, t, s.dur, "handheld", .3);
          st.picks.forEach((x, i) => { const q = E.out3(prog(t, 0.4 + i * 0.35, 0.4)); x.style.opacity = q; x.style.transform = `translateX(${(1 - q) * -30}%)`; });
          const tap = prog(t, 1.9, 0.7);
          st.rip.style.transform = `scale(${tap * 60})`; st.rip.style.opacity = tap > 0 && tap < 1 ? 1 - tap : 0;
          st.wa.style.transform = tap > 0 && tap < 0.2 ? "scale(.96)" : "none";
        }
      },
    },
    value: {
      build(cam, s) {
        el("div", "eyebrow", cam, "The rule");
        const h = kinetic(el("div", "headline", cam), s.on_screen, "slam");
        const v = el("div", "visual", cam), stack = el("div", "stack", v);
        const ls = [0, 1, 2, 3].map(() => { const l = el("div", "listing", stack); el("i", "", l); el("b", "", l); return l; });
        const coin = el("div", "coin", stack, "£");
        illus(cam);
        return { h, ls, coin };
      },
      render(cam, t, s, st) {
        kineticAt(st.h, t, 0.15);
        st.ls.forEach((l, i) => { l.style.opacity = E.out3(prog(t, 0.3 + i * 0.12, 0.4)); });
        // the coin flies at the bottom listing, bounces off, and nothing moves up
        const fly = prog(t, 1.4, 0.7), back = prog(t, 2.1, 0.9);
        const x = fly < 1 ? lerp(110, 60, E.inOut(fly)) : lerp(60, 130, E.out3(back));
        const y = fly < 1 ? lerp(-40, 72, E.inOut(fly)) : lerp(72, -60, E.out3(back));
        st.coin.style.left = x + "%"; st.coin.style.top = y + "%"; st.coin.style.transform = `rotate(${(fly + back) * 540}deg)`;
        cam.style.transform = "scale(1.02)" + thump(cam, t, 2.1);
      },
    },
    cta: {
      build(cam, s) {
        const c = el("div", "center", cam), sign = el("div", "sign", c);
        el("div", "t1", sign, "Bolton<br>Vouched").style.fontSize = "calc(var(--u)*8)";
        const stamp = el("div", "stamp", c, "FREE · NO SIGN-UP"); stamp.style.marginTop = "calc(var(--u)*4)";
        const u = kinetic(el("div", "url", c), s.on_screen.replace("https://", ""), "type");
        return { sign, stamp, u };
      },
      render(cam, t, s, st) {
        const k = E.outBack(prog(t, 0.7, 0.3));
        st.stamp.style.opacity = clamp(k * 2); st.stamp.style.transform = `rotate(-6deg) scale(${lerp(2.2, 1, k)})`;
        cam.style.transform = "scale(1.02)" + thump(cam, t, 0.8);
        kineticAt(st.u, t, 1.2, 1.4);
      },
    },
  },
};
STYLE.scenes.default = STYLE.scenes.feature;
