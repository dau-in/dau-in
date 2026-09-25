"""
Builds assets/discord_card.png (and _light) from the Lanyard API.

Until 2026-09-25 the README embedded a third-party widget
(lanyard.cnrad.dev) for this. That service draws its own card, so it could
only be tuned through its query parameters and could never share the other
cards' look (card_skin.py). This builds the same card ourselves.

Lanyard (api.lanyard.rest) mirrors a Discord user's public presence for
anyone who has joined its Discord server -- this account already had, which
is what the old widget needed too. No key, no secret.

The one thing given up: the old widget was fetched live on every view; this
card refreshes with the others, every 30 minutes, so the status dot can be up
to half an hour behind. It reads "offline" most of the time anyway.

Discord's CDN answers 403 to requests without a browser User-Agent, hence
the header on every image fetch.
"""
import base64
import json
import os
import shutil
import sys
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
USER_ID = '780932598922084384'
# The line the old widget showed when nothing else was going on (its
# idleMessage parameter). A custom status set in Discord takes its place.
IDLE_MESSAGE = 'bored, for now'
CDN = 'https://cdn.discordapp.com'

STATUS = {
    'online': ('online', '#23a55a'),
    'idle': ('idle', '#f0b232'),
    'dnd': ('do not disturb', '#f23f43'),
    'offline': ('offline', '#80848e'),
}
# Activity types worth a section of their own. Listening (2) is left out on
# purpose: that's Spotify, which already has its own card right above.
ACTIVITY_VERBS = {0: 'playing', 1: 'streaming', 3: 'watching'}

DISCORD_LOGO = '''<svg width="15" height="15" viewBox="0 0 24 24" fill="#a7a0a7" style="vertical-align:-2px"><path d="M20.317 4.37a19.79 19.79 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.865-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.74 19.74 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028c.462-.63.874-1.295 1.226-1.994a.076.076 0 0 0-.041-.106 13.1 13.1 0 0 1-1.872-.892.077.077 0 0 1-.008-.128c.126-.094.252-.192.372-.291a.074.074 0 0 1 .078-.01c3.927 1.793 8.18 1.793 12.061 0a.074.074 0 0 1 .079.009c.12.099.246.198.373.292a.077.077 0 0 1-.007.128 12.3 12.3 0 0 1-1.873.891.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.029 19.84 19.84 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.086-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.095 2.157 2.42 0 1.332-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.086-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.095 2.157 2.42 0 1.332-.946 2.418-2.157 2.418z"/></svg>'''


def fetch_image(url):
    """An image as base64, or None -- the decoration, guild badge and activity
    art are extras, and a failed one shouldn't take the card down with it."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        return base64.b64encode(urlopen_retry(req, timeout=20)).decode()
    except Exception:
        return None


def activity_image_url(activity):
    large = (activity.get('assets') or {}).get('large_image')
    if not large:
        return None
    if large.startswith('mp:'):
        return f'https://media.discordapp.net/{large[3:]}'
    if activity.get('application_id'):
        return f"{CDN}/app-assets/{activity['application_id']}/{large}.png"
    return None


def fetch_data():
    resp = json.loads(urlopen_retry(f'https://api.lanyard.rest/v1/users/{USER_ID}'))
    if not resp.get('success'):
        sys.exit(f'Lanyard said no: {resp}')
    presence = resp['data']
    user = presence['discord_user']

    if user.get('avatar'):
        avatar_url = f"{CDN}/avatars/{user['id']}/{user['avatar']}.png?size=256"
    else:
        avatar_url = f"{CDN}/embed/avatars/{(int(user['id']) >> 22) % 6}.png"
    avatar_b64 = fetch_image(avatar_url)
    if not avatar_b64:
        sys.exit(f'Could not fetch the avatar at {avatar_url}')

    deco = (user.get('avatar_decoration_data') or {}).get('asset')
    guild = user.get('primary_guild') or {}
    has_tag = guild.get('identity_enabled') and guild.get('tag')

    custom = next((a for a in presence.get('activities', []) if a.get('type') == 4 and a.get('state')), None)
    activity = next((a for a in presence.get('activities', []) if a.get('type') in ACTIVITY_VERBS), None)

    return {
        'name': user.get('global_name') or user['username'],
        'username': user['username'],
        'status': presence.get('discord_status', 'offline'),
        'avatar_b64': avatar_b64,
        'decoration_b64': fetch_image(f'{CDN}/avatar-decoration-presets/{deco}.png?size=240&passthrough=false') if deco else None,
        'guild_tag': guild['tag'] if has_tag else None,
        'guild_badge_b64': (fetch_image(f"{CDN}/guild-tag-badges/{guild['identity_guild_id']}/{guild['badge']}.png?size=32")
                            if has_tag and guild.get('badge') else None),
        'status_line': custom['state'] if custom else IDLE_MESSAGE,
        'activity': {
            'verb': ACTIVITY_VERBS[activity['type']],
            'name': activity.get('name', ''),
            'details': activity.get('details') or activity.get('state') or '',
            'image_b64': fetch_image(activity_image_url(activity)) if activity_image_url(activity) else None,
        } if activity else None,
    }


CSS = '''
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&family=Fraunces:ital@1&display=swap');
body { margin:0; padding:20px; overflow:hidden; font-family:"Space Grotesk",-apple-system,Segoe UI,Helvetica,Arial,sans-serif; }
.card { width:420px; border:1px solid rgba(255,255,255,0.08); border-radius:18px; padding:20px 22px; }
.row { display:flex; align-items:center; gap:16px; }
.av { position:relative; width:72px; height:72px; flex-shrink:0; }
.av .avatar { width:72px; height:72px; border-radius:50%; display:block; }
.av .deco { position:absolute; left:-9px; top:-9px; width:90px; height:90px; }
.name { font-weight:700; font-size:22px; color:#fff; line-height:1.15; display:flex; align-items:center; gap:9px; }
.gtag { display:inline-flex; align-items:center; gap:4px; font-size:12px; font-weight:700; color:#d6d6d6;
  background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.12); border-radius:6px; padding:2px 6px; }
.gtag img { width:14px; height:14px; }
.status { font-size:14px; color:#e5e5e5; margin-top:5px; }
.status-dot { display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:6px; vertical-align:1px; }
.divider { height:1px; margin:16px 0; }
.stat-label { margin-bottom:9px; }
.quote { font-family:'Fraunces', Georgia, serif; font-style:italic; font-size:16px; color:#e5e5e5; }
.act { display:flex; align-items:center; gap:12px; }
.act img { width:50px; height:50px; border-radius:8px; flex-shrink:0; }
.act .t { font-size:15px; font-weight:600; color:#e5e5e5; }
.act .s { font-size:13px; color:#a7a0a7; margin-top:2px; }
.brand { display:flex; align-items:center; justify-content:flex-end; gap:7px; font-size:12px; color:#a7a0a7; margin-top:16px; }
'''


def build_html(data):
    status_text, status_color = STATUS.get(data['status'], STATUS['offline'])
    deco = (f'<img class="deco" src="data:image/png;base64,{data["decoration_b64"]}"/>'
            if data['decoration_b64'] else '')
    tag = ''
    if data['guild_tag']:
        badge = (f'<img src="data:image/png;base64,{data["guild_badge_b64"]}"/>'
                 if data['guild_badge_b64'] else '')
        tag = f'<span class="gtag">{badge}{data["guild_tag"]}</span>'

    act = data['activity']
    if act:
        art = f'<img src="data:image/png;base64,{act["image_b64"]}"/>' if act['image_b64'] else ''
        section = f'''<div class="stat-label">{card_skin.label('discord', act['verb'])}</div>
<div class="act">{art}<div><div class="t">{act['name']}</div><div class="s">{act['details']}</div></div></div>'''
    else:
        section = f'''<div class="stat-label">{card_skin.label('discord', 'status')}</div>
<div class="quote">"{data['status_line']}"</div>'''

    # The @username sits at the foot, where every other card puts its link;
    # the old discord.com/users/<id> link read as noise. The whole card still
    # links to that profile from the README.
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>{CSS}{card_skin.CSS}</style></head><body>
<div class="card">{card_skin.ambient(card_skin.data_url(data['avatar_b64']))}
<div class="row">
<div class="av"><img class="avatar" src="data:image/png;base64,{data['avatar_b64']}"/>{deco}</div>
<div>
<div class="name">{data['name']} {tag}</div>
<div class="status"><span class="status-dot" style="background:{status_color}"></span>{status_text}</div>
</div>
</div>
<div class="divider"></div>
{section}
<div class="brand">{DISCORD_LOGO}@{data['username']}</div>
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


def main():
    import tempfile

    data = fetch_data()
    print(json.dumps({k: v for k, v in data.items() if not k.endswith('_b64') and k != 'activity'},
                     indent=2, ensure_ascii=False))

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        html_path = tmp / 'card.html'
        html_path.write_text(build_html(data), encoding='utf-8')

        out_path = HERE.parent / 'assets' / 'discord_card.png'
        card_skin.render(find_chrome(), html_path, out_path, '520,500')
        print('written', out_path)


if __name__ == '__main__':
    main()
