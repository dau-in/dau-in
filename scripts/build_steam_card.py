"""
Builds assets/steam_card.png from live Steam data.

Requires STEAM_API_KEY in the environment (get one free, tied to your own account,
at https://steamcommunity.com/dev/apikey -- never commit it, only ever pass it as an
env var / GitHub Actions secret).

STEAM_ID below is just a public numeric SteamID64, not a secret -- safe to hardcode.
"""
import base64
import json
import os
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
STEAM_API_KEY = os.environ['STEAM_API_KEY']
STEAM_ID = '76561199194382282'


def steam_api(interface, method, version, **params):
    params['key'] = STEAM_API_KEY
    url = f'https://api.steampowered.com/{interface}/{method}/{version}/?' + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=15) as r:
        return json.loads(r.read())


def fetch_data():
    summary = steam_api('ISteamUser', 'GetPlayerSummaries', 'v0002', steamids=STEAM_ID)
    player = summary['response']['players'][0]

    level = steam_api('IPlayerService', 'GetSteamLevel', 'v1', steamid=STEAM_ID)
    player_level = level['response']['player_level']

    owned = steam_api('IPlayerService', 'GetOwnedGames', 'v1', steamid=STEAM_ID,
                       include_appinfo=True, include_played_free_games=True)
    games = owned['response'].get('games', [])
    games_count = owned['response'].get('game_count', len(games))

    last_played = None
    if games:
        last_played = max(games, key=lambda g: g.get('rtime_last_played', 0))

    return {
        'persona_name': player['personaname'],
        'avatar_url': player['avatarfull'],
        'level': player_level,
        'games_count': games_count,
        'last_played_name': last_played['name'] if last_played else None,
        'last_played_icon_url': (
            f"https://media.steampowered.com/steamcommunity/public/images/apps/"
            f"{last_played['appid']}/{last_played['img_icon_url']}.jpg"
        ) if last_played and last_played.get('img_icon_url') else None,
    }


def download(url, dest):
    urllib.request.urlretrieve(url, dest)


STEAM_LOGO = '''<svg width="16" height="16" viewBox="0 0 24 24" style="vertical-align:-3px;margin-right:5px;" fill="#a7a0a7">
<path d="M11.979 0C5.678 0 0.511 4.86.022 11.037l6.432 2.658c.545-.371 1.203-.591 1.912-.591.063 0 .125.004.188.006l2.861-4.142V8.91c0-2.505 2.038-4.543 4.543-4.543 2.505 0 4.543 2.039 4.543 4.545 0 2.506-2.038 4.545-4.543 4.545h-.101l-4.076 2.909c.001.053.003.106.003.159 0 1.9-1.544 3.444-3.444 3.444-1.669 0-3.061-1.19-3.379-2.766l-4.6-1.902C1.547 19.298 6.242 24 11.979 24c6.626 0 11.999-5.373 11.999-12S18.605 0 11.979 0zM7.54 18.21l-1.473-.61c.262.542.714.999 1.314 1.25 1.297.539 2.793-.076 3.332-1.375.263-.63.264-1.319.005-1.949s-.75-1.121-1.377-1.383c-.624-.26-1.29-.249-1.878-.03l1.523.63c.956.4 1.409 1.5 1.009 2.455-.398.957-1.497 1.41-2.454 1.012zm11.415-9.303c0-1.665-1.353-3.017-3.015-3.017-1.665 0-3.015 1.353-3.015 3.017 0 1.665 1.35 3.015 3.015 3.015 1.663 0 3.015-1.35 3.015-3.015zm-5.273-.005c0-1.252 1.013-2.266 2.265-2.266 1.249 0 2.266 1.014 2.266 2.266 0 1.251-1.017 2.265-2.266 2.265-1.253 0-2.265-1.014-2.265-2.265z"/>
</svg>'''

# designed natively compact (not a shrunk-down version of a wider card) -- this
# card sits side-by-side with the spotify one at a narrow display width, so its
# own font sizes need to already read fine around 250-260px wide.
CSS = '''
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,500,600,700;1,400&display=swap');
body { background:#000; margin:0; padding:20px; font-family:Inter,-apple-system,Segoe UI,Helvetica,Arial,sans-serif; }
.card { width:260px; background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.08); border-radius:16px; padding:14px 16px; }
.row { display:flex; align-items:center; gap:10px; }
.avatar { width:42px; height:42px; border-radius:50%; flex-shrink:0; }
.name { font-weight:700; font-size:17px; color:#fff; line-height:1.15; display:flex; align-items:center; gap:6px; flex-wrap:wrap; }
.level { font-size:9px; font-weight:700; color:#a7a0a7; border:1px solid rgba(255,255,255,0.15); border-radius:999px; padding:1px 6px; }
.games { font-size:11px; color:#a7a0a7; margin-top:2px; }
.divider { height:1px; background:rgba(255,255,255,0.08); margin:12px 0; }
.last-label { font-size:9px; color:#666; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:7px; }
.last-row { display:flex; align-items:center; gap:8px; }
.last-icon { width:30px; height:30px; border-radius:5px; flex-shrink:0; }
.last-name { font-size:12px; color:#e5e5e5; font-weight:600; line-height:1.25; }
.brand { display:flex; align-items:center; justify-content:flex-end; font-size:10px; color:#a7a0a7; margin-top:12px; }
.brand svg { width:12px; height:12px; }
'''


def build_html(data, avatar_b64, icon_b64):
    last_played_block = ''
    if data['last_played_name']:
        icon_tag = f'<img class="last-icon" src="data:image/jpeg;base64,{icon_b64}"/>' if icon_b64 else ''
        last_played_block = f'''
<div class="divider"></div>
<div class="last-label">last played</div>
<div class="last-row">
{icon_tag}
<div class="last-name">{data['last_played_name']}</div>
</div>'''

    return f'''<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="card">
<div class="row">
<img class="avatar" src="data:image/png;base64,{avatar_b64}"/>
<div>
<div class="name">𝓓` <span class="level">Lv. {data['level']}</span></div>
<div class="games">{data['games_count']} games in library</div>
</div>
</div>
{last_played_block}
<div class="brand">{STEAM_LOGO}steamcommunity.com/id/dauin</div>
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
        '--force-device-scale-factor=2', '--window-size=340,280',
        f'--screenshot={raw}', f'file:///{html_path.as_posix()}',
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

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)

        avatar_path = tmp / 'avatar.png'
        download(data['avatar_url'], avatar_path)
        avatar_b64 = base64.b64encode(avatar_path.read_bytes()).decode()

        icon_b64 = None
        if data['last_played_icon_url']:
            icon_path = tmp / 'icon.jpg'
            download(data['last_played_icon_url'], icon_path)
            icon_b64 = base64.b64encode(icon_path.read_bytes()).decode()

        html_path = tmp / 'card.html'
        html_path.write_text(build_html(data, avatar_b64, icon_b64), encoding='utf-8')

        out_path = HERE.parent / 'assets' / 'steam_card.png'
        render(html_path, tmp, out_path, find_chrome())
        print('written', out_path)


if __name__ == '__main__':
    main()
