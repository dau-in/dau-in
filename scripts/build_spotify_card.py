"""
Builds assets/spotify_card.png from live Spotify data: top artist + genre (last 6
months, time_range=medium_term -- long_term/all-time felt too static since taste
changes), top 5 tracks this month (time_range=short_term, ~4 weeks), and the single
most recently played track with a relative "how long ago".

Requires SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REFRESH_TOKEN in the
environment (see spotify_auth.py for the one-time OAuth setup). The refresh token
must have been issued with scopes: user-top-read user-read-private user-read-recently-played
"""
import base64
import json
import os
import shutil
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def time_ago(iso_ts):
    for fmt in ('%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%SZ'):
        try:
            then = datetime.strptime(iso_ts, fmt).replace(tzinfo=timezone.utc)
            break
        except ValueError:
            continue
    else:
        return ''
    delta = datetime.now(timezone.utc) - then
    minutes = delta.total_seconds() / 60
    if minutes < 60:
        return f'{max(round(minutes), 1)}m ago'
    hours = minutes / 60
    if hours < 24:
        return f'{round(hours)}h ago'
    days = hours / 24
    return f'{round(days)}d ago'

HERE = Path(__file__).parent
CLIENT_ID = os.environ['SPOTIFY_CLIENT_ID']
CLIENT_SECRET = os.environ['SPOTIFY_CLIENT_SECRET']
REFRESH_TOKEN = os.environ['SPOTIFY_REFRESH_TOKEN']


def get_access_token():
    auth = base64.b64encode(f'{CLIENT_ID}:{CLIENT_SECRET}'.encode()).decode()
    req = urllib.request.Request(
        'https://accounts.spotify.com/api/token',
        data=f'grant_type=refresh_token&refresh_token={REFRESH_TOKEN}'.encode(),
        headers={
            'Authorization': f'Basic {auth}',
            'Content-Type': 'application/x-www-form-urlencoded',
        },
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())['access_token']


def spotify_get(endpoint, token):
    req = urllib.request.Request(
        f'https://api.spotify.com/v1{endpoint}',
        headers={'Authorization': f'Bearer {token}'},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def fetch_data():
    token = get_access_token()

    me = spotify_get('/me', token)
    top_artists = spotify_get('/me/top/artists?time_range=medium_term&limit=1', token)
    top_tracks = spotify_get('/me/top/tracks?time_range=short_term&limit=5', token)
    recent = spotify_get('/me/player/recently-played?limit=1', token)

    artist = top_artists['items'][0] if top_artists.get('items') else None
    tracks = top_tracks.get('items', [])
    last_item = recent['items'][0] if recent and recent.get('items') else None
    last = last_item['track'] if last_item else None

    return {
        'display_name': me.get('display_name') or 'me',
        'avatar_url': me['images'][0]['url'] if me.get('images') else None,
        'top_artist_name': artist['name'] if artist else None,
        'top_artist_img': artist['images'][0]['url'] if artist and artist.get('images') else None,
        'genre': artist['genres'][0].title() if artist and artist.get('genres') else None,
        'top_tracks': [
            {
                'name': t['name'],
                'artist': ', '.join(a['name'] for a in t['artists']),
                'img': t['album']['images'][-1]['url'] if t['album'].get('images') else None,
            }
            for t in tracks
        ],
        'last_track_name': last['name'] if last else None,
        'last_track_artist': ', '.join(a['name'] for a in last['artists']) if last else None,
        'last_track_img': last['album']['images'][0]['url'] if last and last['album'].get('images') else None,
        'last_track_ago': time_ago(last_item['played_at']) if last_item else None,
    }


def download(url, dest):
    urllib.request.urlretrieve(url, dest)


SPOTIFY_LOGO = '''<svg width="16" height="16" viewBox="0 0 24 24" style="vertical-align:-3px;margin-right:5px;" fill="#1DB954">
<path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141 4.32-1.32 9.719-.66 13.439 1.621.361.181.54.78.301 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.72 1.621.539.3.719 1.02.42 1.56-.299.421-1.02.599-1.559.3z"/>
</svg>'''

CSS = '''
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap');
body { background:#000; margin:0; padding:20px; overflow:hidden; font-family:Inter,-apple-system,Segoe UI,Helvetica,Arial,sans-serif; }
.card { width:340px; background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.08); border-radius:18px; padding:20px 22px; }
.row { display:flex; align-items:center; gap:12px; }
.avatar { width:56px; height:56px; border-radius:50%; object-fit:cover; background:#222; flex-shrink:0; }
.name { font-weight:700; font-size:22px; color:#fff; line-height:1.15; }
.divider { height:1px; background:rgba(255,255,255,0.08); margin:16px 0; }
.stat-label { font-size:11px; color:#666; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:9px; }
.stat-row { display:flex; align-items:center; gap:11px; }
.stat-row + .stat-row { margin-top:11px; }
.stat-img { width:36px; height:36px; border-radius:6px; object-fit:cover; background:#222; flex-shrink:0; }
.stat-name { font-size:14px; color:#e5e5e5; font-weight:600; line-height:1.25; }
.stat-sub { font-size:12px; color:#a7a0a7; margin-top:2px; }
.rank-row { display:flex; align-items:center; gap:10px; }
.rank-row + .rank-row { margin-top:10px; }
.rank-num { font-size:13px; color:#555; font-weight:700; width:16px; flex-shrink:0; text-align:center; }
.rank-img { width:30px; height:30px; border-radius:5px; object-fit:cover; background:#222; flex-shrink:0; }
.rank-name { font-size:13px; color:#e5e5e5; font-weight:600; line-height:1.2; }
.rank-sub { font-size:11px; color:#777; line-height:1.2; margin-top:1px; }
.brand { display:flex; align-items:center; justify-content:flex-end; font-size:12px; color:#a7a0a7; margin-top:16px; }
.brand svg { width:14px; height:14px; }
'''


def build_html(data, avatar_b64, artist_img_b64, track_imgs_b64, last_img_b64):
    artist_block = ''
    if data['top_artist_name']:
        icon_tag = f'<img class="stat-img" src="data:image/jpeg;base64,{artist_img_b64}"/>' if artist_img_b64 else '<div class="stat-img"></div>'
        sub = f'<div class="stat-sub">{data["genre"]}</div>' if data['genre'] else ''
        artist_block = f'''
<div class="divider"></div>
<div class="stat-label">top artist &middot; 6 months</div>
<div class="stat-row">
{icon_tag}
<div>
<div class="stat-name">{data['top_artist_name']}</div>
{sub}
</div>
</div>'''

    tracks_block = ''
    if data['top_tracks']:
        rows = []
        for i, (t, img_b64) in enumerate(zip(data['top_tracks'], track_imgs_b64), start=1):
            img_tag = f'<img class="rank-img" src="data:image/jpeg;base64,{img_b64}"/>' if img_b64 else '<div class="rank-img"></div>'
            rows.append(f'''<div class="rank-row">
<div class="rank-num">{i}</div>
{img_tag}
<div>
<div class="rank-name">{t['name']}</div>
<div class="rank-sub">{t['artist']}</div>
</div>
</div>''')
        tracks_block = f'''
<div class="divider"></div>
<div class="stat-label">top 5 &middot; this month</div>
''' + '\n'.join(rows)

    last_block = ''
    if data['last_track_name']:
        icon_tag = f'<img class="stat-img" src="data:image/jpeg;base64,{last_img_b64}"/>' if last_img_b64 else '<div class="stat-img"></div>'
        ago = f' &middot; {data["last_track_ago"]}' if data.get('last_track_ago') else ''
        last_block = f'''
<div class="divider"></div>
<div class="stat-label">last played</div>
<div class="stat-row">
{icon_tag}
<div>
<div class="stat-name">{data['last_track_name']}</div>
<div class="stat-sub">{data['last_track_artist']}{ago}</div>
</div>
</div>'''

    return f'''<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="card">
<div class="row">
<img class="avatar" src="data:image/jpeg;base64,{avatar_b64}"/>
<div class="name">𝓓`</div>
</div>
{artist_block}
{tracks_block}
{last_block}
<div class="brand">{SPOTIFY_LOGO}open.spotify.com</div>
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
        '--force-device-scale-factor=2', '--window-size=400,950',
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
    if not data['top_artist_name'] and not data['top_tracks'] and not data['last_track_name']:
        print('No Spotify data available at all -- skipping (card left as-is).')
        return

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)

        def maybe_download(url, name):
            if not url:
                return None
            p = tmp / name
            download(url, p)
            return base64.b64encode(p.read_bytes()).decode()

        avatar_b64 = maybe_download(data['avatar_url'], 'avatar.jpg')
        artist_img_b64 = maybe_download(data['top_artist_img'], 'artist.jpg')
        track_imgs_b64 = [
            maybe_download(t['img'], f'track{i}.jpg')
            for i, t in enumerate(data['top_tracks'])
        ]
        last_img_b64 = maybe_download(data['last_track_img'], 'last.jpg')

        html_path = tmp / 'card.html'
        html_path.write_text(
            build_html(data, avatar_b64, artist_img_b64, track_imgs_b64, last_img_b64),
            encoding='utf-8',
        )

        out_path = HERE.parent / 'assets' / 'spotify_card.png'
        render(html_path, tmp, out_path, find_chrome())
        print('written', out_path)


if __name__ == '__main__':
    main()
