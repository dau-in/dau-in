# -*- coding: utf-8 -*-
"""
Builds assets/passport_card.png -- the profile card for passportdex.com/dauin.

Not run by CI, unlike the four dynamic cards. passportdex has no public API
and blocks automated fetches (confirmed with them directly, and confirmed
again since: an embedded/automated browser gets "couldn't open it here --
try again in a browser" instead of the page). So the handful of facts below
are transcribed by hand from the live profile, and this script is re-run
manually whenever they change.

To refresh: open https://passportdex.com/dauin in a normal signed-in
browser, read off the "now watching" title, the starred pick and its
caption, and the four library counts, update the PROFILE block, and run
this. The cover art doesn't need transcribing -- the URLs below point at
the same IGDB/TMDB images the profile itself renders, and the script fetches
and squares them at build time.

This used to live in design-assets/ (gitignored scratch), which meant the
source of a published image wasn't tracked anywhere. It is tracked now.
"""
import base64
import io
import json
import os
import shutil
import sys
import tempfile
import urllib.request
from pathlib import Path

# Shared retry wrapper -- see http_retry.py for what gets another go and
# what is taken at its word. Imported by name because Python puts a
# script's own directory on sys.path, and these are always run as
# `python scripts/build_x.py`.
from http_retry import urlopen_retry
# The shared look (ambient background, path labels, transparent render) --
# see card_skin.py.
import card_skin

HERE = Path(__file__).parent
OUT_PATH = HERE.parent / 'assets' / 'passport_card.png'

# --- transcribed from passportdex.com/dauin -------------------------------
PROFILE = {
    # No @handle next to the name: the passportdex.com/dauin link at the foot
    # of the card already says it.
    'name': '\U0001D4D3`',
    'quote': '"Every letter deserves to be delivered."',
    'now_watching': {
        'title': 'Violet Evergarden',
        'art': 'https://image.tmdb.org/t/p/w500/61EwFPqc0r1uJo6la49J55F8bQ8.jpg',
    },
    'top_pick': {
        'title': 'NieR: Automata',
        'caption': '"my eternal masterpiece"',
        'art': 'https://images.igdb.com/igdb/image/upload/t_cover_big_2x/co5jbj.jpg',
    },
    # The counts row used to be one line reading "89 games . 33 music . 26
    # films . 18 books" with middots between. No dot separators anywhere on
    # these cards any more -- it's a four-column strip now, which also lets
    # the numbers carry the same mono treatment every other card gives a
    # figure, instead of sitting in running text.
    'counts': [
        ('89', 'games'),
        ('33', 'music'),
        ('26', 'film & tv'),
        ('18', 'books'),
    ],
    'avatar': 'https://cdn.passportdex.com/avatars/'
              '4bc68f9d-dbb1-4caf-a1c2-c20c924daeb0/1781649789548-qhdgqud3.jpg',
}

# passportdex.com's actual palette, pulled from their live computed styles:
#   background #000  |  body text #e5e5e5  |  accent #a7a0a7
#   panel rgba(255,255,255,.05) on rgba(255,255,255,.08) border, ~18px radius
# Their mark is a white five-point star in a black circle; redrawn as SVG so
# it stays crisp at any size rather than embedding their low-res raster icon.
PANEL_RGB = (13, 13, 13)
STAR_LOGO = '''<svg class="star" width="15" height="15" viewBox="0 0 100 100">
<circle cx="50" cy="50" r="50" fill="#fff"/>
<path d="M 46 8 L 60 42 L 92 46 L 64 62 L 74 92 L 46 70 L 20 88 L 30 58 L 8 40 L 40 38 Z" fill="#000"/>
</svg>'''


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    return urlopen_retry(req, timeout=30)


def art_box(raw, width, height, circle=False):
    # Both covers are cropped to fill one shared 2:3 portrait frame rather
    # than letterboxed into a square. Letterboxing was the old approach and
    # it left bands of panel colour down the sides of every poster, which
    # got more obvious once the art grew. A poster is natively 2:3 and a
    # game cover 3:4, so filling the frame costs the game cover a sliver off
    # each side and costs the poster nothing -- a better trade than framing
    # every row in empty space. The avatar is masked to a circle in CSS, so
    # it takes a square centre crop and nothing outside the mask shows.
    from PIL import Image
    img = Image.open(io.BytesIO(raw)).convert('RGB')
    if circle:
        width = height = min(width, height)
    scale = max(width / img.width, height / img.height)
    img = img.resize((max(round(img.width * scale), width),
                      max(round(img.height * scale), height)), Image.LANCZOS)
    left = (img.width - width) // 2
    top = (img.height - height) // 2
    img = img.crop((left, top, left + width, top + height))
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode()


CSS = '''
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,400;0,500;0,600;0,700;1,400&family=JetBrains+Mono:wght@400;500;700&family=Fraunces:ital@1&display=swap');
body { margin:0; padding:20px; font-family:Inter,-apple-system,Segoe UI,Helvetica,Arial,sans-serif; }
.card { width:420px; border:1px solid rgba(255,255,255,0.08); border-radius:18px; padding:20px 22px; }
.row { display:flex; align-items:center; gap:14px; }
.avatar { width:64px; height:64px; border-radius:50%; flex-shrink:0; }
.name { font-weight:700; font-size:22px; color:#fff; line-height:1.1; }
.quote { margin-top:13px; font-family:'Fraunces', Georgia, serif; font-style:italic; font-size:15px; color:#e5e5e5; }
.divider { height:1px; margin:15px 0; }
.stat-label { margin-bottom:9px; }
.stat-row { display:flex; align-items:center; gap:12px; }
.stat-img { width:50px; height:75px; border-radius:6px; flex-shrink:0; }
.stat-name { font-size:14px; color:#e5e5e5; font-weight:600; }
.stat-sub { font-family:'Fraunces', Georgia, serif; font-style:italic; font-size:12.5px; color:#a7a0a7; margin-top:2px; }
.counts { display:flex; margin-top:16px; border-top:1px solid rgba(255,255,255,0.1); padding-top:14px; }
.count { flex:1; }
.count-num { font-family:"JetBrains Mono",monospace; font-weight:700; font-size:17px; color:#e5e5e5; line-height:1.1; }
.count-label { font-size:10px; color:#6f6a6f; text-transform:uppercase; letter-spacing:0.07em; margin-top:3px; }
.brand { display:flex; align-items:center; justify-content:flex-end; gap:7px; font-size:12px; color:#a7a0a7; margin-top:16px; }
.star { vertical-align:-2px; }
'''


def build_html(images):
    counts = '\n'.join(
        f'<div class="count"><div class="count-num">{n}</div>'
        f'<div class="count-label">{label}</div></div>'
        for n, label in PROFILE['counts']
    )
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>{CSS}{card_skin.CSS}</style></head><body>
<div class="card">{card_skin.ambient(card_skin.data_url(images['avatar']))}
<div class="row">
<img class="avatar" src="data:image/png;base64,{images['avatar']}"/>
<div class="name">{PROFILE['name']}</div>
</div>
<div class="quote">{PROFILE['quote']}</div>
<div class="divider"></div>
<div class="stat-label">{card_skin.label('passport', 'now-watching')}</div>
<div class="stat-row">
<img class="stat-img" src="data:image/png;base64,{images['watching']}"/>
<div class="stat-name">{PROFILE['now_watching']['title']}</div>
</div>
<div class="divider"></div>
<div class="stat-label">{card_skin.label('passport', 'top-pick')}</div>
<div class="stat-row">
<img class="stat-img" src="data:image/png;base64,{images['top_pick']}"/>
<div>
<div class="stat-name">{PROFILE['top_pick']['title']}</div>
<div class="stat-sub">{PROFILE['top_pick']['caption']}</div>
</div>
</div>
<div class="counts">
{counts}
</div>
<div class="brand">{STAR_LOGO}passportdex.com/dauin</div>
</div>
</body></html>'''


def find_chrome():
    for candidate in (
        os.environ.get('CHROME_PATH'),
        shutil.which('chrome'),
        shutil.which('chromium'),
        shutil.which('google-chrome'),
        'C:/Program Files/Google/Chrome/Application/chrome.exe',
    ):
        if candidate and Path(candidate).exists():
            return candidate
    sys.exit('No Chrome/Chromium binary found -- set CHROME_PATH')


def render(html_path, tmp_dir, out_path, chrome):
    card_skin.render(chrome, html_path, out_path, '520,760')


def main():
    images = {
        'avatar': art_box(fetch(PROFILE['avatar']), 128, 128, circle=True),
        'watching': art_box(fetch(PROFILE['now_watching']['art']), 100, 150),
        'top_pick': art_box(fetch(PROFILE['top_pick']['art']), 100, 150),
    }
    print(json.dumps({k: v['title'] for k, v in PROFILE.items() if isinstance(v, dict) and 'title' in v},
                     indent=2, ensure_ascii=False))

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        html_path = tmp / 'card.html'
        html_path.write_text(build_html(images), encoding='utf-8')
        render(html_path, tmp, OUT_PATH, find_chrome())
        print('written', OUT_PATH)


if __name__ == '__main__':
    main()
