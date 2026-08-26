"""
Builds assets/last_commit_card.png from Darwin's most recent public GitHub
push: repo, primary language (colored dot, matching GitHub's own language
colors), commit message (truncated), short SHA, line diff stat, and how long
ago.

No secrets needed -- GitHub's public events/commits/repo endpoints work
unauthenticated for public data. Optionally uses GITHUB_TOKEN if set (GitHub
Actions injects one automatically for every run, not something to create or
manage) to raise the rate limit from 60/hr to 5000/hr, since Actions runners
share IPs with a lot of other unauthenticated traffic. This can only ever
reflect what's actually been pushed to GitHub; it has no way to see
local/uncommitted work or anything outside git entirely -- that's what the
Discord "now playing" widget already covers instead.
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

HERE = Path(__file__).parent
USERNAME = 'dau-in'
MESSAGE_MAX_LEN = 90

# GitHub's own per-language colors (github-linguist/linguist), just the
# subset actually likely to show up here -- unlisted languages fall back to
# a neutral gray dot rather than erroring.
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


def time_ago(iso_ts):
    then = datetime.strptime(iso_ts, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - then
    minutes = delta.total_seconds() / 60
    if minutes < 60:
        return f'{max(round(minutes), 1)}m ago'
    hours = minutes / 60
    if hours < 24:
        return f'{round(hours)}h ago'
    days = hours / 24
    return f'{round(days)}d ago'


def github_api(path):
    headers = {'User-Agent': USERNAME, 'Accept': 'application/vnd.github+json'}
    # optional: GitHub Actions injects its own short-lived GITHUB_TOKEN for
    # every run automatically (not a secret Darwin has to create or manage)
    # -- using it if present just raises the rate limit from 60/hr to
    # 5000/hr, since this is a scheduled job sharing runner IPs with a lot
    # of other Actions traffic. Works fine unauthenticated too.
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        headers['Authorization'] = f'Bearer {token}'
    req = urllib.request.Request(f'https://api.github.com{path}', headers=headers)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def truncate(message, limit):
    first_line = message.split('\n', 1)[0]
    if len(first_line) <= limit:
        return first_line
    return first_line[:limit - 1].rstrip() + '\u2026'


def fetch_data():
    events = github_api(f'/users/{USERNAME}/events/public')
    push = next(e for e in events if e['type'] == 'PushEvent')
    repo_name = push['repo']['name']
    sha = push['payload']['head']

    commit = github_api(f'/repos/{repo_name}/commits/{sha}')
    repo = github_api(f'/repos/{repo_name}')

    stats = commit.get('stats', {})
    language = repo.get('language')

    return {
        'repo_name': repo_name,
        'language': language,
        'language_color': LANGUAGE_COLORS.get(language, DEFAULT_LANGUAGE_COLOR),
        'message': truncate(commit['commit']['message'], MESSAGE_MAX_LEN),
        'sha_short': commit['sha'][:7],
        'additions': stats.get('additions', 0),
        'deletions': stats.get('deletions', 0),
        'time_ago': time_ago(commit['commit']['author']['date']),
        'avatar_url': f'https://avatars.githubusercontent.com/u/{push["actor"]["id"]}',
    }


CSS = '''
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,400;0,500;0,600;0,700;1,400&family=JetBrains+Mono:wght@500;700&display=swap');
body { background:#000; margin:0; padding:20px; overflow:hidden; font-family:Inter,-apple-system,Segoe UI,Helvetica,Arial,sans-serif; }
.card { width:380px; background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.08); border-radius:18px; padding:22px 24px; position:relative; overflow:hidden; }
.accent { position:absolute; top:0; left:0; width:100%; height:3px; }
.stat-label { font-size:11px; color:#666; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:12px; }
.repo-row { display:flex; align-items:center; gap:8px; margin-bottom:12px; }
.lang-dot { width:10px; height:10px; border-radius:50%; flex-shrink:0; }
.repo { font-size:16px; color:#fff; font-weight:700; font-family:"JetBrains Mono",monospace; }
.lang-name { font-size:12px; color:#a7a0a7; margin-left:auto; font-family:"JetBrains Mono",monospace; }
.msg { font-size:14.5px; color:#e5e5e5; line-height:1.5; margin-bottom:16px; padding-left:14px; border-left:2px solid rgba(255,255,255,0.12); }
.meta-row { display:flex; align-items:center; gap:10px; }
.sha-chip { font-family:"JetBrains Mono",monospace; font-size:11px; font-weight:700; color:#e5e5e5; background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.1); border-radius:999px; padding:3px 10px; }
.diffstat { font-family:"JetBrains Mono",monospace; font-size:12px; }
.add { color:#3fb950; }
.del { color:#f85149; margin-left:4px; }
.time { font-size:12px; color:#777; margin-left:auto; }
.brand { display:flex; align-items:center; justify-content:flex-end; gap:7px; font-size:12px; color:#a7a0a7; margin-top:18px; }
.brand img { width:16px; height:16px; border-radius:50%; }
'''


def build_html(data, avatar_b64):
    lang_block = f'<span class="lang-name">{data["language"]}</span>' if data['language'] else ''
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="card">
<div class="accent" style="background:linear-gradient(90deg, {data['language_color']}, transparent);"></div>
<div class="stat-label">latest commit</div>
<div class="repo-row">
<span class="lang-dot" style="background:{data['language_color']}; box-shadow:0 0 8px {data['language_color']}aa;"></span>
<span class="repo">{data['repo_name']}</span>
{lang_block}
</div>
<div class="msg">{data['message']}</div>
<div class="meta-row">
<span class="sha-chip">{data['sha_short']}</span>
<span class="diffstat"><span class="add">+{data['additions']}</span><span class="del">-{data['deletions']}</span></span>
<span class="time">{data['time_ago']}</span>
</div>
<div class="brand"><img src="data:image/png;base64,{avatar_b64}"/>github.com/{USERNAME}</div>
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
        '--force-device-scale-factor=2', '--window-size=460,400',
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
        urllib.request.urlretrieve(data['avatar_url'], avatar_path)
        avatar_b64 = base64.b64encode(avatar_path.read_bytes()).decode()

        html_path = tmp / 'card.html'
        html_path.write_text(build_html(data, avatar_b64), encoding='utf-8')

        out_path = HERE.parent / 'assets' / 'last_commit_card.png'
        render(html_path, tmp, out_path, find_chrome())
        print('written', out_path)


if __name__ == '__main__':
    main()
