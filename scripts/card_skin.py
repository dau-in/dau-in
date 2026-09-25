# -*- coding: utf-8 -*-
"""
The look every card shares, in one place.

Adopted 2026-09-25 after a long round of mockups (kept in design-assets/):
the "ambient" skin. Each card keeps its own structure -- platform avatar up
top, same sections, same order -- and gets three things on top of it:

  - its background is the platform avatar itself, blurred and greyscale, so
    the card reads as yours without adding a colour to the interface. The
    avatars are black-and-white art already, so the result stays monochrome.
  - section labels are small terminal paths (~/steam/recent, --6mo) in
    JetBrains Mono, a nod to the whoami.cpp box above the cards.
  - the interface itself is black/white/grey. Colour only comes from
    content: covers, game art, language icons. That's why wakatime's pink
    accent is gone while the python icon stays yellow and blue.

It also renders every card onto a transparent page instead of a black one.
The old black margin showed as a dark frame around each card against
GitHub's own background (and much worse in light mode); now the rounded
corners sit directly on whatever the page is.

Each builder appends CSS to its own stylesheet (same-specificity rules later
in the sheet win, so nothing here needs !important), wraps its avatar with
ambient(), writes labels with label(), and hands rendering to render().
"""
import base64
import re
import subprocess

from http_retry import urlopen_retry

# Builders' own @import lines must include JetBrains Mono 400/500 for the
# labels -- an @import appended after other rules is ignored by the browser.
# The card's own background is opaque on purpose: the ambient layers sit
# above it anyway (negative z-index inside the isolated card), and if the
# avatar download fails, a translucent card would turn light grey on
# GitHub's light theme now that the page behind it is transparent.
CSS = '''
body { background:transparent; }
.card { position:relative; overflow:hidden; isolation:isolate; background:#0e0e0e; }
.amb { position:absolute; inset:-80px; background-size:cover; background-position:center 30%;
  filter:grayscale(1) blur(40px) brightness(0.36) contrast(1.35); z-index:-2; }
.veil { position:absolute; inset:0; z-index:-1;
  background:linear-gradient(180deg, rgba(0,0,0,0) 0%, rgba(0,0,0,0.55) 45%, rgba(0,0,0,0.8) 100%); }
.stat-label { font-family:"JetBrains Mono",monospace; font-size:12.5px; font-weight:400; color:#d6d6d6;
  text-transform:none; letter-spacing:0; }
.stat-label .path { color:#8a8a8a; }
.range-tag { font-family:"JetBrains Mono",monospace; font-size:11.5px; font-weight:500; color:#8a8a8a;
  text-transform:none; letter-spacing:0; }
.divider { background:rgba(255,255,255,0.1); }
'''


def label(platform, name):
    """A section label as a path: ~/steam/ dimmed, the section name bright."""
    return f'<span class="path">~/{platform}/</span>{name}'


def ambient(avatar_data_url):
    """The two background layers, placed first inside .card. With no avatar
    (a failed download) the card simply renders without them."""
    if not avatar_data_url:
        return ''
    return (f'<div class="amb" style="background-image:url({avatar_data_url})"></div>'
            '<div class="veil"></div>')


def data_url(b64, mime='image/png'):
    return f'data:{mime};base64,{b64}' if b64 else None


def github_avatar(username):
    """The GitHub avatar as a data URL, for the cards with no avatar of their
    own. None on failure: a missing background is not worth failing a card."""
    try:
        raw = urlopen_retry(f'https://avatars.githubusercontent.com/{username}?s=256', timeout=20)
    except Exception:
        return None
    return data_url(base64.b64encode(raw).decode())


# --- dark devicon icons ------------------------------------------------------
# Some devicon "original" icons are black or near-black (markdown, rust,
# github...) and vanish on a dark card. An icon counts as dark when even its
# lightest colour is dark -- or when it declares no colour at all, which SVG
# paints black. Those get a light fill forced over every shape; icons with
# real colour (python, js...) are left exactly as they are.
_HEX = re.compile(r'(?:fill|stop-color|color)\s*[:=]\s*"?\s*#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b')


def _luminance(hex_color):
    if len(hex_color) == 3:
        hex_color = ''.join(c * 2 for c in hex_color)
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def lighten_if_dark(svg_bytes):
    svg = svg_bytes.decode('utf-8', 'replace')
    colours = _HEX.findall(svg)
    named_light = re.search(r'fill\s*[:=]\s*"?\s*(white|#fff\b)', svg, re.I)
    lightest = max((_luminance(c) for c in colours), default=0.0)
    if named_light or lightest >= 0.25:
        return svg_bytes
    patch = '<style>*{fill:#d4d4d4 !important;}</style>'
    return re.sub(r'(<svg\b[^>]*>)', r'\1' + patch, svg, count=1).encode('utf-8')


# --- rendering -----------------------------------------------------------------
PAD = 28  # transparent margin kept around the card; README sizing assumes it


def render(chrome, html_path, out_path, window_size):
    """Screenshot the page on a transparent background and crop to the card
    plus PAD, keeping the alpha channel."""
    raw = html_path.parent / 'raw.png'
    subprocess.run([
        chrome, '--headless', '--disable-gpu', '--no-sandbox',
        '--force-device-scale-factor=2', f'--window-size={window_size}',
        '--default-background-color=00000000', '--hide-scrollbars',
        '--virtual-time-budget=4000', f'--screenshot={raw}', f'file:///{html_path.as_posix()}',
    ], check=True)

    from PIL import Image
    img = Image.open(raw).convert('RGBA')
    l, t, r, b = img.getchannel('A').getbbox()
    l, t = max(l - PAD, 0), max(t - PAD, 0)
    r, b = min(r + PAD, img.width), min(b + PAD, img.height)
    img.crop((l, t, r, b)).save(out_path)
