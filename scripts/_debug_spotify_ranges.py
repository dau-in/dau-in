"""
Temporary, one-off diagnostic: prints top tracks for all three Spotify
time_range values side by side, so the actual song lists can be compared
before picking which range build_spotify_card.py should use. Not part of
the regular pipeline -- delete after use, along with the workflow that
runs it.
"""
import base64
import json
import os
import urllib.request

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


def main():
    token = get_access_token()
    for time_range in ('short_term', 'medium_term', 'long_term'):
        data = spotify_get(f'/me/top/tracks?time_range={time_range}&limit=20', token)
        items = data.get('items', [])
        print(f'\n=== {time_range} ({len(items)} tracks) ===')
        for i, t in enumerate(items, start=1):
            artists = ', '.join(a['name'] for a in t['artists'])
            print(f'{i:2d}. {t["name"]} -- {artists}')

        artist_data = spotify_get(f'/me/top/artists?time_range={time_range}&limit=10', token)
        aitems = artist_data.get('items', [])
        print(f'--- top artists ({time_range}) ---')
        for i, a in enumerate(aitems, start=1):
            genres = ', '.join(a.get('genres', [])[:3])
            print(f'{i:2d}. {a["name"]} ({genres})')


if __name__ == '__main__':
    main()
