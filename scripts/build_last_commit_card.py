"""
Builds assets/last_commit_card.png from Darwin's most recent public GitHub
push: repo, primary language (icon/dot, matching GitHub's own language
colors), commit message (truncated), short SHA, line diff stat, and how
long ago -- coarse-grained (no raw minutes, see format_commit_time) rather
than an absolute clock time, which would avoid the staleness problem
entirely but leak a timezone/schedule pattern across enough commits that
nothing else on this profile does.

Also writes assets/last_commit_url.txt (the target commit's own GitHub
page) -- build_readme.py reads it to link the card, since the URL changes
every run and README.md's own template has no way to reach the API itself.

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

# All 692 of GitHub's own per-language colors (github-linguist/linguist's
# languages.yml, re-extracted whenever it's worth refreshing -- see
# scripts/build_language_colors.py), not a hand-picked subset: a hardcoded
# ~15-language list left anything else falling back to gray, and one entry
# (C#) was even wrong -- linguist has it as #7355dd, not the #178600 that
# was hardcoded here before. Unrecognized/unlisted languages still fall back
# to gray rather than erroring.
LANGUAGE_COLORS = json.loads((HERE / 'language_colors.json').read_text(encoding='utf-8'))
DEFAULT_LANGUAGE_COLOR = '#8b8b8b'

# GitHub language name -> devicon slug, for the ~90 languages devicon has an
# icon for (see scripts/build_language_icons.py). Missing entirely for
# anything unmapped -- that's expected for most of the 692 languages
# (nobody's making a real icon for e.g. "Roff"), and build_html() falls back
# to the plain colored dot in that case rather than erroring.
LANGUAGE_ICON_SLUGS = json.loads((HERE / 'language_icon_slugs.json').read_text(encoding='utf-8'))
DEVICON_URL = 'https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/{slug}/{slug}-original.svg'


def format_commit_time(iso_ts):
    # Back to relative time, not an absolute UTC timestamp -- a fixed clock
    # time never goes stale, but repeated across enough commits it reveals a
    # pattern (roughly what hours someone's usually online) that nothing
    # else on this profile does; everything else here is taste/interests,
    # not a schedule. The actual problem with relative time wasn't the
    # concept, it was showing single MINUTES when the render cadence (hourly
    # cron, instant on a push) can't back up that precision -- "1m ago"
    # sitting there for the next 59 real minutes is what read as a lie.
    # Dropping minutes entirely for a coarse bucket removes that -- but even
    # that bucket used to say "just now", which is its own small lie: GitHub's
    # schedule trigger is best-effort and has sat idle for 10+ hours at a
    # stretch, so this exact bucket can end up on screen far longer than 45
    # real minutes. "recently" doesn't claim a freshness the render cadence
    # can't actually back up.
    then = datetime.strptime(iso_ts, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - then
    minutes = delta.total_seconds() / 60
    if minutes < 45:
        return 'recently'
    hours = minutes / 60
    if hours < 24:
        return f'{round(hours)}h ago'
    days = hours / 24
    if days < 7:
        return f'{round(days)}d ago'
    weeks = days / 7
    if weeks < 4.35:
        return f'{round(weeks)}w ago'
    months = days / 30.44
    if months < 12:
        return f'{round(months)}mo ago'
    years = days / 365.25
    return f'{round(years)}y ago'


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


def fetch_language_icon_b64(language):
    slug = LANGUAGE_ICON_SLUGS.get(language)
    if not slug:
        return None
    try:
        with urllib.request.urlopen(DEVICON_URL.format(slug=slug), timeout=10) as r:
            return base64.b64encode(r.read()).decode()
    except Exception:
        # a CDN hiccup or a slug devicon has since renamed shouldn't break
        # the whole card -- just fall back to the plain colored dot
        return None


def truncate(message, limit):
    first_line = message.split('\n', 1)[0]
    if len(first_line) <= limit:
        return first_line
    return first_line[:limit - 1].rstrip() + '\u2026'


def fetch_data():
    # The public events feed (/users/.../events/public) is what this always
    # used to read from, but it's eventually-consistent -- it can lag a few
    # minutes behind a push that just landed. That's invisible on a schedule
    # trigger (plenty of real time has passed either way), but the whole
    # point of the push trigger is to refresh the instant a commit lands, and
    # the feed sometimes hasn't caught up by the time this script runs a few
    # seconds later -- rendering the *previous* commit as if it were current.
    # This workflow's push trigger only ever fires for a push to this exact
    # repo, so on that trigger GITHUB_SHA/GITHUB_REPOSITORY (auto-injected by
    # Actions) already name the authoritative commit with no lag at all.
    # Schedule/manual runs have no such commit to anchor to -- those still
    # need the events feed, since that's the only way to see a push made to
    # any of Darwin's repos, not just this one.
    if os.environ.get('GITHUB_EVENT_NAME') == 'push':
        repo_name = os.environ['GITHUB_REPOSITORY']
        sha = os.environ['GITHUB_SHA']
    else:
        # GitHub's own docs say this feed is "delivered on a best-effort
        # basis" -- confirmed the hard way: a push from hours ago surfaced
        # ahead of two pushes to the same repo made since, so the first
        # PushEvent in the list isn't reliably the most recent one. Picking
        # by max(created_at) instead of list order is the fix.
        events = github_api(f'/users/{USERNAME}/events/public')
        pushes = [e for e in events if e['type'] == 'PushEvent']
        push = max(pushes, key=lambda e: e['created_at'])
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
        'language_icon_b64': fetch_language_icon_b64(language) if language else None,
        'message': truncate(commit['commit']['message'], MESSAGE_MAX_LEN),
        'sha_short': commit['sha'][:7],
        'additions': stats.get('additions', 0),
        'deletions': stats.get('deletions', 0),
        'committed_at': format_commit_time(commit['commit']['author']['date']),
        'avatar_url': f'https://avatars.githubusercontent.com/{USERNAME}',
        'commit_url': commit['html_url'],
    }


CSS = '''
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,400;0,500;0,600;0,700;1,400&family=JetBrains+Mono:wght@500;700&display=swap');
body { background:#000; margin:0; padding:20px; overflow:hidden; font-family:Inter,-apple-system,Segoe UI,Helvetica,Arial,sans-serif; }
.card { width:380px; background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.08); border-radius:18px; padding:22px 24px; position:relative; overflow:hidden; }
.accent { position:absolute; top:0; left:0; width:100%; height:3px; }
.stat-label { font-size:11px; color:#666; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:12px; }
.repo-row { display:flex; align-items:center; gap:8px; margin-bottom:12px; }
.repo-group { display:flex; align-items:center; gap:8px; }
.gh-icon { width:16px; height:16px; flex-shrink:0; fill:#a7a0a7; }
.repo { font-size:16px; color:#fff; font-weight:700; font-family:"JetBrains Mono",monospace; }
.lang-group { display:flex; align-items:center; gap:6px; margin-left:auto; }
.lang-dot { width:10px; height:10px; border-radius:50%; flex-shrink:0; }
.lang-icon { width:18px; height:18px; flex-shrink:0; }
.lang-name { font-size:12px; color:#a7a0a7; font-family:"JetBrains Mono",monospace; }
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


GITHUB_MARK = '''<svg class="gh-icon" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>'''


def build_html(data, avatar_b64):
    lang_block = f'<span class="lang-name">{data["language"]}</span>' if data['language'] else ''
    # icon when devicon has one for this language (real personality, its own
    # brand colors baked into the svg) -- plain colored dot otherwise, same
    # as before this existed
    if data['language_icon_b64']:
        lang_marker = f'<img class="lang-icon" src="data:image/svg+xml;base64,{data["language_icon_b64"]}"/>'
    else:
        lang_marker = f'<span class="lang-dot" style="background:{data["language_color"]}; box-shadow:0 0 8px {data["language_color"]}aa;"></span>'
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="card">
<div class="accent" style="background:linear-gradient(90deg, {data['language_color']}, transparent);"></div>
<div class="stat-label">latest commit</div>
<div class="repo-row">
<div class="repo-group">{GITHUB_MARK}<span class="repo">{data['repo_name']}</span></div>
<div class="lang-group">{lang_marker}{lang_block}</div>
</div>
<div class="msg">{data['message']}</div>
<div class="meta-row">
<span class="sha-chip">{data['sha_short']}</span>
<span class="diffstat"><span class="add">+{data['additions']}</span><span class="del">-{data['deletions']}</span></span>
<span class="time">{data['committed_at']}</span>
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

        # sidecar file, not baked into the image: build_readme.py reads this
        # to link the card to the actual commit instead of leaving it an
        # unlinked image (which GitHub just opens as the raw file on click).
        # A plain text file, not JSON -- it's a single value, and this way
        # `cat`/opening it directly already shows the answer.
        url_path = HERE.parent / 'assets' / 'last_commit_url.txt'
        url_path.write_text(data['commit_url'], encoding='utf-8')
        print('written', url_path)


if __name__ == '__main__':
    main()
