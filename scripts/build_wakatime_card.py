"""
Builds assets/wakatime_card.png from WakaTime's Stats API: total coding time
and top languages (by %) over the last 7 days.

Requires WAKATIME_API_KEY in the environment (from
https://wakatime.com/settings/api-key -- never commit it, only ever pass it
as an env var / GitHub Actions secret, same as every other card here).

NOT YET WIRED into build_readme.py or update-widgets.yml -- written against
WakaTime's public API docs, not a real response, since no account/data
exists yet. Field names (languages[].name/percent/text, data.total_seconds,
etc.) may need adjusting once there's an actual key to test against; run
this standalone first and check the printed output before trusting the
rendered card.
"""
import base64
import json
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
API_KEY = os.environ['WAKATIME_API_KEY']
RANGE = 'last_7_days'

# Same GitHub-linguist-derived colors as build_last_commit_card.py -- kept
# as its own copy rather than a shared import since every card script here
# is deliberately self-contained (see e.g. how Steam/Spotify don't share
# code either).
LANGUAGE_COLORS = {
    'Python': '#3572A5',
    'Go': '#00ADD8',
    'JavaScript': '#f1e05a',
    'TypeScript': '#3178c6',
    'HTML': '#e34c26',
    'CSS': '#563d7c',
    'Shell': '#89e051',
    'Rust': '#dea584',
    'C': '#555555',
    'C++': '#f34b7d',
    'C#': '#178600',
    'Java': '#b07219',
    'Lua': '#000080',
    'Dockerfile': '#384d54',
    'PowerShell': '#012456',
}
DEFAULT_LANGUAGE_COLOR = '#8b8b8b'


def wakatime_api(path):
    auth = base64.b64encode(API_KEY.encode()).decode()
    req = urllib.request.Request(
        f'https://wakatime.com/api/v1{path}',
        headers={'Authorization': f'Basic {auth}'},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def fetch_data():
    stats = wakatime_api(f'/users/current/stats/{RANGE}')['data']

    languages = [
        {
            'name': lang['name'],
            'percent': lang['percent'],
            'color': LANGUAGE_COLORS.get(lang['name'], DEFAULT_LANGUAGE_COLOR),
        }
        for lang in stats.get('languages', [])[:5]
    ]

    return {
        'human_readable_total': stats.get('human_readable_total', '0 secs'),
        'daily_average': stats.get('human_readable_daily_average', ''),
        'languages': languages,
    }


CSS = '''
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap');
body { background:#000; margin:0; padding:20px; overflow:hidden; font-family:Inter,-apple-system,Segoe UI,Helvetica,Arial,sans-serif; }
.card { width:340px; background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.08); border-radius:18px; padding:22px 24px; }
.stat-label { font-size:11px; color:#666; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:4px; }
.hero { display:flex; align-items:baseline; gap:9px; }
.hero-num { font-size:38px; font-weight:800; color:#fff; line-height:1; }
.hero-sub { font-size:12px; color:#a7a0a7; margin-top:4px; }
.divider { height:1px; background:rgba(255,255,255,0.08); margin:18px 0; }
.lang-row { display:flex; align-items:center; gap:10px; }
.lang-row + .lang-row { margin-top:10px; }
.lang-dot { width:9px; height:9px; border-radius:50%; flex-shrink:0; }
.lang-name { font-size:14px; color:#e5e5e5; font-weight:600; width:100px; flex-shrink:0; }
.bar-track { flex:1; height:6px; background:rgba(255,255,255,0.08); border-radius:999px; overflow:hidden; }
.bar-fill { height:100%; border-radius:999px; }
.lang-pct { font-size:12px; color:#a7a0a7; width:38px; text-align:right; flex-shrink:0; }
.brand { display:flex; align-items:center; justify-content:flex-end; font-size:12px; color:#a7a0a7; margin-top:18px; }
'''


def build_html(data):
    lang_rows = '\n'.join(f'''<div class="lang-row">
<span class="lang-dot" style="background:{l['color']};"></span>
<span class="lang-name">{l['name']}</span>
<span class="bar-track"><span class="bar-fill" style="width:{l['percent']}%; background:{l['color']};"></span></span>
<span class="lang-pct">{l['percent']:.0f}%</span>
</div>''' for l in data['languages'])

    return f'''<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="card">
<div class="stat-label">coding time &middot; last 7 days</div>
<div class="hero"><div class="hero-num">{data['human_readable_total']}</div></div>
<div class="hero-sub">{data['daily_average']} daily average</div>
<div class="divider"></div>
<div class="stat-label">top languages</div>
{lang_rows}
<div class="brand">wakatime.com</div>
</div>
</body></html>'''


def find_chrome():
    for candidate in (
        os.environ.get('CHROME_PATH'),
        shutil.which('chrome'),
        shutil.which('chromium'),
        shutil.which('google-chrome'),
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    ):
        if candidate and Path(candidate).exists():
            return candidate
    sys.exit('No Chrome/Chromium binary found -- set CHROME_PATH')


def render(html_path, tmp_dir, out_path, chrome):
    raw = tmp_dir / 'raw.png'
    subprocess.run([
        chrome, '--headless', '--disable-gpu', '--no-sandbox',
        '--force-device-scale-factor=2', '--window-size=460,500',
        '--virtual-time-budget=4000', f'--screenshot={raw}', f'file:///{html_path.as_posix()}',
    ], check=True)

    from PIL import Image, ImageChops
    img = Image.open(raw).convert('RGB')
    bg = Image.new('RGB', img.size, (0, 0, 0))
    diff = ImageChops.difference(img, bg)
    bbox = diff.getbbox()
    pad = 28
    l, t, r, b = bbox
    l, t = max(l - pad, 0), max(t - pad, 0)
    r, b = min(r + pad, img.width), min(b + pad, img.height)
    img.crop((l, t, r, b)).save(out_path)


def main():
    import tempfile

    data = fetch_data()
    print(json.dumps(data, indent=2, ensure_ascii=False))  # sanity-check the shape before trusting the render

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        html_path = tmp / 'card.html'
        html_path.write_text(build_html(data), encoding='utf-8')

        out_path = HERE.parent / 'assets' / 'wakatime_card.png'
        render(html_path, tmp, out_path, find_chrome())
        print('written', out_path)


if __name__ == '__main__':
    main()
