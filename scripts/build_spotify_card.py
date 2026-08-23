"""
Builds assets/spotify_card.png from live Spotify data (currently playing, falling
back to the most recently played track).

Requires three env vars, all from your own Spotify Developer app + a one-time OAuth
consent (see spotify_auth.py): SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET,
SPOTIFY_REFRESH_TOKEN. Never commit these -- env vars / GitHub Actions secrets only.
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
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            if r.status == 204:
                return None
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code == 204:
            return None
        raise


def fetch_data():
    token = get_access_token()

    now = spotify_get('/me/player/currently-playing', token)
    if now and now.get('item') and now.get('is_playing'):
        track = now['item']
        status = 'listening now'
    else:
        recent = spotify_get('/me/player/recently-played?limit=1', token)
        track = recent['items'][0]['track'] if recent and recent.get('items') else None
        status = 'last played'

    if not track:
        return None

    return {
        'status': status,
        'track_name': track['name'],
        'artist': ', '.join(a['name'] for a in track['artists']),
        'art_url': track['album']['images'][0]['url'] if track['album']['images'] else None,
        'track_url': track['external_urls']['spotify'],
    }


def download(url, dest):
    urllib.request.urlretrieve(url, dest)


SPOTIFY_LOGO = '''<svg width="16" height="16" viewBox="0 0 24 24" style="vertical-align:-3px;margin-right:5px;" fill="#1DB954">
<path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141 4.32-1.32 9.719-.66 13.439 1.621.361.181.54.78.301 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.72 1.621.539.3.719 1.02.42 1.56-.299.421-1.02.599-1.559.3z"/>
</svg>'''

CSS = '''
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,400;0,500;0,700;1,400&display=swap');
body { background:#000; margin:0; padding:20px; font-family:Inter,-apple-system,Segoe UI,Helvetica,Arial,sans-serif; }
.card { width:420px; background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.08); border-radius:18px; padding:18px 20px; }
.row { display:flex; align-items:center; gap:14px; }
.art { width:56px; height:56px; border-radius:6px; object-fit:cover; }
.label { font-size:11px; color:#666; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:6px; }
.track { font-weight:700; font-size:16px; color:#fff; line-height:1.3; }
.artist { font-size:13px; color:#a7a0a7; margin-top:2px; }
.brand { display:flex; align-items:center; justify-content:flex-end; font-size:12px; color:#a7a0a7; margin-top:16px; }
'''


def build_html(data, art_b64):
    art_tag = f'<img class="art" src="data:image/jpeg;base64,{art_b64}"/>' if art_b64 else ''
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="card">
<div class="label">{data['status']}</div>
<div class="row">
{art_tag}
<div>
<div class="track">{data['track_name']}</div>
<div class="artist">{data['artist']}</div>
</div>
</div>
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
        '--force-device-scale-factor=2', '--window-size=560,260',
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
    if not data:
        print('No listening history available at all -- skipping (card left as-is).')
        return

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)

        art_b64 = None
        if data['art_url']:
            art_path = tmp / 'art.jpg'
            download(data['art_url'], art_path)
            art_b64 = base64.b64encode(art_path.read_bytes()).decode()

        html_path = tmp / 'card.html'
        html_path.write_text(build_html(data, art_b64), encoding='utf-8')

        out_path = HERE.parent / 'assets' / 'spotify_card.png'
        render(html_path, tmp, out_path, find_chrome())
        print('written', out_path)


if __name__ == '__main__':
    main()
