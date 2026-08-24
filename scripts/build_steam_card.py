"""
Builds assets/steam_card.png from live Steam data: level, games count, activity
status, most-played game (all time), and the 3 most recently played games (each
with playtime in the last 2 weeks).

Requires STEAM_API_KEY in the environment (get one free, tied to your own account,
at https://steamcommunity.com/dev/apikey -- never commit it, only ever pass it as an
env var / GitHub Actions secret).

STEAM_ID below is just a public numeric SteamID64, not a secret -- safe to hardcode.

TODO (research, not yet done): pull in Darwin's equipped avatar frame (animated,
if he has one) and a sliver of his profile background for the card art -- neither
is in GetPlayerSummaries; likely needs IPlayerService/GetProfileItemsEquipped or
scraping the profile page. Unconfirmed whether the frame's actual asset URL/format
is easy to composite into our own CSS card. Investigate before promising it.
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

STATUS_MAP = {
    0: ('offline', '#666'),
    1: ('online', '#3ba55d'),
    2: ('busy', '#ed4245'),
    3: ('away', '#faa61a'),
    4: ('snooze', '#faa61a'),
    5: ('looking to trade', '#3ba55d'),
    6: ('looking to play', '#3ba55d'),
}


def steam_api(interface, method, version, **params):
    params['key'] = STEAM_API_KEY
    url = f'https://api.steampowered.com/{interface}/{method}/{version}/?' + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=15) as r:
        return json.loads(r.read())


def icon_url(game):
    if not game or not game.get('img_icon_url'):
        return None
    return (f"https://media.steampowered.com/steamcommunity/public/images/apps/"
            f"{game['appid']}/{game['img_icon_url']}.jpg")


def fetch_data():
    summary = steam_api('ISteamUser', 'GetPlayerSummaries', 'v0002', steamids=STEAM_ID)
    player = summary['response']['players'][0]

    level = steam_api('IPlayerService', 'GetSteamLevel', 'v1', steamid=STEAM_ID)
    player_level = level['response']['player_level']

    owned = steam_api('IPlayerService', 'GetOwnedGames', 'v1', steamid=STEAM_ID,
                       include_appinfo=True, include_played_free_games=True)
    games = owned['response'].get('games', [])
    games_count = owned['response'].get('game_count', len(games))

    most_played = max(games, key=lambda g: g.get('playtime_forever', 0)) if games else None
    recent = sorted(games, key=lambda g: g.get('rtime_last_played', 0), reverse=True)[:3] if games else []
    hours_2weeks_total = round(sum(g.get('playtime_2weeks', 0) for g in games) / 60, 1)

    status_text, status_color = STATUS_MAP.get(player.get('personastate', 0), STATUS_MAP[0])

    return {
        'persona_name': player['personaname'],
        'avatar_url': player['avatarfull'],
        'level': player_level,
        'games_count': games_count,
        'status_text': status_text,
        'status_color': status_color,
        'hours_2weeks_total': hours_2weeks_total,
        'most_played_name': most_played['name'] if most_played else None,
        'most_played_icon_url': icon_url(most_played),
        'recent': [
            {'name': g['name'], 'icon_url': icon_url(g)}
            for g in recent
        ],
    }


def download(url, dest):
    urllib.request.urlretrieve(url, dest)


STEAM_LOGO = '''<svg width="16" height="16" viewBox="0 0 24 24" style="vertical-align:-3px;margin-right:5px;" fill="#a7a0a7">
<path d="M11.979 0C5.678 0 0.511 4.86.022 11.037l6.432 2.658c.545-.371 1.203-.591 1.912-.591.063 0 .125.004.188.006l2.861-4.142V8.91c0-2.505 2.038-4.543 4.543-4.543 2.505 0 4.543 2.039 4.543 4.545 0 2.506-2.038 4.545-4.543 4.545h-.101l-4.076 2.909c.001.053.003.106.003.159 0 1.9-1.544 3.444-3.444 3.444-1.669 0-3.061-1.19-3.379-2.766l-4.6-1.902C1.547 19.298 6.242 24 11.979 24c6.626 0 11.999-5.373 11.999-12S18.605 0 11.979 0zM7.54 18.21l-1.473-.61c.262.542.714.999 1.314 1.25 1.297.539 2.793-.076 3.332-1.375.263-.63.264-1.319.005-1.949s-.75-1.121-1.377-1.383c-.624-.26-1.29-.249-1.878-.03l1.523.63c.956.4 1.409 1.5 1.009 2.455-.398.957-1.497 1.41-2.454 1.012zm11.415-9.303c0-1.665-1.353-3.017-3.015-3.017-1.665 0-3.015 1.353-3.015 3.017 0 1.665 1.35 3.015 3.015 3.015 1.663 0 3.015-1.35 3.015-3.015zm-5.273-.005c0-1.252 1.013-2.266 2.265-2.266 1.249 0 2.266 1.014 2.266 2.266 0 1.251-1.017 2.265-2.266 2.265-1.253 0-2.265-1.014-2.265-2.265z"/>
</svg>'''

CSS = '''
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap');
body { background:#000; margin:0; padding:20px; font-family:Inter,-apple-system,Segoe UI,Helvetica,Arial,sans-serif; }
.card { width:320px; background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.08); border-radius:18px; padding:18px 20px; }
.row { display:flex; align-items:center; gap:12px; }
.avatar { width:52px; height:52px; border-radius:50%; flex-shrink:0; }
.name { font-weight:700; font-size:21px; color:#fff; line-height:1.15; display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
.level { font-size:10px; font-weight:700; color:#a7a0a7; border:1px solid rgba(255,255,255,0.15); border-radius:999px; padding:2px 7px; }
.meta-row { display:flex; align-items:center; gap:6px; margin-top:2px; }
.games { font-size:12px; color:#a7a0a7; }
.dot { font-size:8px; color:#444; }
.status { font-size:12px; color:#e5e5e5; }
.status-dot { display:inline-block; width:7px; height:7px; border-radius:50%; margin-right:5px; vertical-align:middle; }
.divider { height:1px; background:rgba(255,255,255,0.08); margin:14px 0; }
.hero { display:flex; align-items:baseline; gap:8px; }
.hero-num { font-size:34px; font-weight:800; color:#fff; line-height:1; }
.hero-unit { font-size:16px; color:#a7a0a7; }
.hero-label { font-size:11px; color:#a7a0a7; margin-top:2px; }
.stat-label { font-size:10px; color:#666; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:8px; }
.stat-row { display:flex; align-items:center; gap:10px; }
.stat-row + .stat-row { margin-top:10px; }
.stat-img { width:32px; height:32px; border-radius:6px; flex-shrink:0; }
.stat-name { font-size:13px; color:#e5e5e5; font-weight:600; line-height:1.25; }
.stat-sub { font-size:11px; color:#a7a0a7; margin-top:1px; }
.brand { display:flex; align-items:center; justify-content:flex-end; font-size:11px; color:#a7a0a7; margin-top:14px; }
.brand svg { width:13px; height:13px; }
'''


def build_html(data, avatar_b64, most_icon_b64, recent_icons_b64):
    most_block = ''
    if data['most_played_name']:
        icon_tag = f'<img class="stat-img" src="data:image/jpeg;base64,{most_icon_b64}"/>' if most_icon_b64 else '<div class="stat-img"></div>'
        most_block = f'''
<div class="divider"></div>
<div class="stat-label">most played</div>
<div class="stat-row">
{icon_tag}
<div class="stat-name">{data['most_played_name']}</div>
</div>'''

    recent_block = ''
    if data['recent']:
        rows = []
        for g, icon_b64 in zip(data['recent'], recent_icons_b64):
            icon_tag = f'<img class="stat-img" src="data:image/jpeg;base64,{icon_b64}"/>' if icon_b64 else '<div class="stat-img"></div>'
            rows.append(f'''<div class="stat-row">
{icon_tag}
<div class="stat-name">{g['name']}</div>
</div>''')
        recent_block = f'''
<div class="divider"></div>
<div class="stat-label">recently played</div>
''' + '\n'.join(rows)

    hero_block = ''
    if data['hours_2weeks_total']:
        hero_block = f'''
<div class="divider"></div>
<div class="hero">
<div class="hero-num">{data['hours_2weeks_total']}<span class="hero-unit">h</span></div>
<div class="hero-label">played in the last 2 weeks</div>
</div>'''

    return f'''<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="card">
<div class="row">
<img class="avatar" src="data:image/png;base64,{avatar_b64}"/>
<div>
<div class="name">𝓓` <span class="level">Lv. {data['level']}</span></div>
<div class="meta-row">
<span class="status"><span class="status-dot" style="background:{data['status_color']}"></span>{data['status_text']}</span>
<span class="dot">&bull;</span>
<span class="games">{data['games_count']} games</span>
</div>
</div>
</div>
{hero_block}
{most_block}
{recent_block}
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
        '--force-device-scale-factor=2', '--window-size=400,600',
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

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)

        avatar_path = tmp / 'avatar.png'
        download(data['avatar_url'], avatar_path)
        avatar_b64 = base64.b64encode(avatar_path.read_bytes()).decode()

        def maybe_download(url, name):
            if not url:
                return None
            p = tmp / name
            download(url, p)
            return base64.b64encode(p.read_bytes()).decode()

        most_icon_b64 = maybe_download(data['most_played_icon_url'], 'most.jpg')
        recent_icons_b64 = [
            maybe_download(g['icon_url'], f'recent{i}.jpg')
            for i, g in enumerate(data['recent'])
        ]

        html_path = tmp / 'card.html'
        html_path.write_text(build_html(data, avatar_b64, most_icon_b64, recent_icons_b64), encoding='utf-8')

        out_path = HERE.parent / 'assets' / 'steam_card.png'
        render(html_path, tmp, out_path, find_chrome())
        print('written', out_path)


if __name__ == '__main__':
    main()
