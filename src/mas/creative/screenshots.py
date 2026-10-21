"""Screenshots of the products' own public pages via headless Chromium (Playwright).

SSRF guard: HTTPS only, host must be one of the product's verified hosts (or
explicitly allow-listed in settings), and it must not resolve to a private,
loopback or link-local address. Only GET navigation; no forms, no clicks, no logins.
"""
from __future__ import annotations

import ipaddress
import socket
from pathlib import Path
from urllib.parse import urlparse

from ..policy import Action, Policy


class UnsafeURL(ValueError):
    pass


def check_url(url: str, allowed_hosts: set[str], resolve=socket.getaddrinfo) -> str:
    u = urlparse(url)
    if u.scheme != "https":
        raise UnsafeURL("only https URLs may be captured")
    if u.username or u.password or (u.port not in (None, 443)):
        raise UnsafeURL("credentials/ports not allowed in capture URLs")
    host = (u.hostname or "").lower()
    if host not in allowed_hosts:
        raise UnsafeURL(f"host {host!r} is not a verified product host")
    try:
        infos = resolve(host, 443)
    except socket.gaierror as e:
        raise UnsafeURL(f"cannot resolve {host}: {e}") from e
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise UnsafeURL(f"{host} resolves to non-public address {ip}")
    return url


def is_blank(img, threshold: float = 8.0) -> bool:
    """True when an image is (nearly) one flat colour — e.g. a section not yet revealed by scroll animation."""
    from PIL import ImageStat
    return ImageStat.Stat(img.convert("L")).stddev[0] < threshold


def capture(policy: Policy, url: str, out: Path, allowed_hosts: set[str], *,
            width: int = 1440, height: int = 900, mobile: bool = False, full_page: bool = False,
            scroll_sections: int = 0) -> list[Path]:
    """Capture the viewport (or full page). With scroll_sections=N, also scroll down N viewports, waiting for
    scroll-triggered reveals, and save each as <out stem>_sN.png. Returns the saved paths (empty if blocked)."""
    extra = set(policy.settings["integrations"]["playwright_screenshots"].get("allowed_hosts", []))
    check_url(url, allowed_hosts | extra)
    if not policy.authorize(Action.FETCH_EXTERNAL, "playwright_screenshots", detail={"url": url}).allowed:
        return []
    saved: list[Path] = []
    from playwright.sync_api import sync_playwright  # optional dependency

    out.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            ctx = browser.new_context(
                viewport={"width": 390 if mobile else width, "height": 844 if mobile else height},
                device_scale_factor=2 if mobile else 1, is_mobile=mobile, java_script_enabled=True,
                accept_downloads=False, service_workers="block")
            page = ctx.new_page()

            def guard(route):  # block navigation to anything off the allowed host list
                host = urlparse(route.request.url).hostname or ""
                if route.request.is_navigation_request() and host not in allowed_hosts | extra:
                    return route.abort()
                return route.continue_()

            page.route("**/*", guard)
            page.goto(url, wait_until="networkidle", timeout=45_000)
            page.wait_for_timeout(800)
            page.screenshot(path=str(out), full_page=full_page)
            saved.append(out)
            vh = page.viewport_size["height"] if page.viewport_size else height
            for i in range(1, scroll_sections + 1):
                page.mouse.wheel(0, vh)   # real scroll so IntersectionObserver reveals fire
                page.wait_for_timeout(1200)
                p = out.with_name(f"{out.stem}_s{i}{out.suffix}")
                page.screenshot(path=str(p))
                saved.append(p)
        finally:
            browser.close()
    return saved
