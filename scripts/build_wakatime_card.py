"""
Builds assets/wakatime_card.png from WakaTime's Stats API (coding time, top
languages, peak day) plus real lines-shipped totals pulled straight from
GitHub's commit diffs (see fetch_lines_shipped) instead of WakaTime's own
line counter, which turned out to be unreliable for this account.

Reads the API key from WAKATIME_API_KEY in the environment first (that's how
GitHub Actions passes it as a secret -- there's no ~/.wakatime.cfg on a
runner), falling back to ~/.wakatime.cfg's [settings] api_key (that's where
every local plugin -- the Claude Code plugin, the Antigravity plugin, any
IDE extension -- already keeps it, so local runs of this script don't need
their own separate copy of the same key). Never commit the key itself
either way, same as every other card here.

No "top projects" section -- repo names are already shown (with cover art)
in the projects table right above this card in the README, and again via
GitHub's own pinned repos. Repeating them here was pure redundancy, not a
second data point.

"Other" is dropped from the language breakdown: it's WakaTime's bucket for
heartbeats with no language at all (the Claude Code / Antigravity plugins
send one per prompt/tool-use, not per file), not an actual language worth
showing next to Python/JS/etc. The remaining languages are renormalized to
sum to 100% -- "of the time actually attributable to a language" is an
honest framing this account's heartbeat mix can back up; showing Python at
its raw ~15%-of-everything share would just look sparse for no real reason.

TODO once there's real weeks/months of history (not worth it on a couple
days of data): an hour-of-day / day-of-week section like waka-readme-stats'
"I'm an Early bird" / "Most productive on X" blocks. Darwin doesn't touch
the IDE every single day, so raw daily totals would read oddly -- do this as
an average/rate over active days, not a flat day count, and match
whoami.txt's voice (see build_readme.py's whoami_groups) rather than a dry
stats label.
"""
import base64
import configparser
import json
import os
import shutil
import subprocess
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).parent
RANGE = 'last_7_days'
GH_USERNAME = 'dau-in'

# Same GitHub-linguist-derived colors + devicon icons as build_last_commit_card.py.
LANGUAGE_COLORS = json.loads((HERE / 'language_colors.json').read_text(encoding='utf-8'))
DEFAULT_LANGUAGE_COLOR = '#8b8b8b'
LANGUAGE_ICON_SLUGS = json.loads((HERE / 'language_icon_slugs.json').read_text(encoding='utf-8'))
DEVICON_URL = 'https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/{slug}/{slug}-original.svg'
VSCODE_ICON_URL = 'https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/vscode/vscode-original.svg'

# A subtle pink+peach duo instead of a single flat tone -- used for the top
# accent bar, the peak-day flame, and the stat-label tint, so the whole
# card's warmth reads as one deliberate combo rather than one plain color.
PINK = '#f472a0'
PEACH = '#ffab91'
ACCENT_COLOR = PEACH  # kept for anything still expecting a single accent

# devicon has no WakaTime icon -- their real mark is a waveform/heartbeat
# line, redrawn here as a simple bars glyph rather than attempting an exact
# logo trace (same spirit as the hand-drawn star in build_passport_own.py).
WAKATIME_MARK = '''<svg class="brand-icon" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
<rect x="1" y="6" width="2.4" height="4" rx="1.2" fill="currentColor"/>
<rect x="5.1" y="2.5" width="2.4" height="11" rx="1.2" fill="currentColor"/>
<rect x="9.2" y="5" width="2.4" height="6" rx="1.2" fill="currentColor"/>
<rect x="13.3" y="7" width="2.4" height="2" rx="1" fill="currentColor"/>
</svg>'''

# Mountain peak for "peak day" -- literal reading of "peak", and its
# triangular silhouette naturally bleeds edge-to-edge in a 16x16 box (unlike
# the flame, which stayed narrow no matter how it was rescaled, or turned
# squashed-looking when forced wider to compensate). Two overlapping peaks
# in the pink/peach pair, plus a small white snow-cap for detail at this size.
PEAK_ICON = f'''<svg class="peak-icon" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
<g transform="translate(0,-2.4) scale(1,1.3)">
<path d="M1 13 6 4l2 3.2L10.5 3 15 13z" fill="{PINK}"/>
<path d="M9 8.5 10.5 6 15 13H10z" fill="{PEACH}"/>
<path d="M5 8l1.5 2.5L8 8l1 1.5-1 1H5.5z" fill="#fff" opacity="0.85"/>
</g>
</svg>'''

# Small inline glyphs for the two lines under the hero number -- a clock for
# the daily average, a code-bracket for lines shipped. Muted/neutral (not
# pink/peach) so they read as quiet supporting icons, not competing for
# attention with the stat-label bullets.
CLOCK_ICON = '''<svg class="inline-icon" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
<circle cx="8" cy="8" r="6.5" stroke="#8a8a8a" stroke-width="1.3"/>
<path d="M8 4.5V8l2.5 1.5" stroke="#8a8a8a" stroke-width="1.3" stroke-linecap="round"/>
</svg>'''
CODE_ICON = '''<svg class="inline-icon" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M5.5 3.5 1.5 8l4 4.5M10.5 3.5l4 4.5-4 4.5" stroke="#8a8a8a" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
</svg>'''


def lighten(hex_color, amount=0.4):
    hex_color = hex_color.lstrip('#')
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    r, g, b = (round(c + (255 - c) * amount) for c in (r, g, b))
    return f'#{r:02x}{g:02x}{b:02x}'


WEEKDAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


def load_api_key():
    key = os.environ.get('WAKATIME_API_KEY')
    if key:
        return key
    cfg_path = Path.home() / '.wakatime.cfg'
    if cfg_path.exists():
        cfg = configparser.ConfigParser()
        cfg.read(cfg_path, encoding='utf-8')
        key = cfg.get('settings', 'api_key', fallback=None)
        if key:
            return key
    sys.exit('No WakaTime API key found -- set WAKATIME_API_KEY or add it to ~/.wakatime.cfg')


API_KEY = load_api_key()


def wakatime_api(path):
    auth = base64.b64encode(API_KEY.encode()).decode()
    req = urllib.request.Request(
        f'https://wakatime.com/api/v1{path}',
        headers={'Authorization': f'Basic {auth}'},
    )
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
        return None


def fetch_vscode_icon_b64():
    try:
        with urllib.request.urlopen(VSCODE_ICON_URL, timeout=10) as r:
            return base64.b64encode(r.read()).decode()
    except Exception:
        return None


def github_api(path):
    headers = {'User-Agent': GH_USERNAME, 'Accept': 'application/vnd.github+json'}
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        headers['Authorization'] = f'Bearer {token}'
    req = urllib.request.Request(f'https://api.github.com{path}', headers=headers)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def fetch_lines_shipped(days=7):
    # WakaTime's own ai_additions used to back this -- dropped after
    # checking it against real commits (see the note in fetch_data). This
    # sums real per-push diffs from GitHub's compare API instead: verifiable
    # against what's actually on GitHub, not a plugin's internal diffing.
    # Uses before/head compare rather than the push event's own commit list
    # -- the public events API doesn't include per-commit data (checked: the
    # payload only has before/head shas, no `commits` array), and comparing
    # the full before...head range also correctly covers multi-commit pushes
    # in one call instead of missing everything but the head commit.
    # The events endpoint defaults to 30 per page -- with enough same-day
    # activity, that single page can cover barely 3-4 days instead of 7,
    # silently dropping older-but-still-in-range pushes (caught this
    # directly: a busy day pushed the page's oldest event forward and the
    # weekly total quietly fell from ~4,455 to 134). Paginate with
    # per_page=100 and keep going until a page's oldest event falls before
    # the window, or GitHub's own ~300-event cap on this endpoint is hit.
    since = datetime.now(timezone.utc) - timedelta(days=days)
    seen_pushes = set()
    total_additions = 0
    for page in range(1, 11):
        events = github_api(f'/users/{GH_USERNAME}/events/public?per_page=100&page={page}')
        if not events:
            break
        for event in events:
            if event['type'] != 'PushEvent':
                continue
            created_at = datetime.strptime(event['created_at'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
            if created_at < since:
                continue
            repo = event['repo']['name']
            before, head = event['payload']['before'], event['payload']['head']
            key = (repo, before, head)
            if key in seen_pushes or set(before) == {'0'}:
                continue
            seen_pushes.add(key)
            try:
                compare = github_api(f'/repos/{repo}/compare/{before}...{head}')
                total_additions += sum(f.get('additions', 0) for f in compare.get('files') or [])
            except Exception:
                continue
        oldest_on_page = datetime.strptime(events[-1]['created_at'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
        if oldest_on_page < since:
            break
    return total_additions


def format_duration(total_seconds):
    total_seconds = int(total_seconds)
    hours, minutes = total_seconds // 3600, (total_seconds % 3600) // 60
    if hours and minutes:
        return f'{hours} hr{"s" if hours != 1 else ""} {minutes} min{"s" if minutes != 1 else ""}'
    if hours:
        return f'{hours} hr{"s" if hours != 1 else ""}'
    if minutes:
        return f'{minutes} min{"s" if minutes != 1 else ""}'
    return f'{total_seconds} secs'


def fetch_data():
    # /stats/last_7_days is cached server-side and didn't recompute after
    # raising the account's keystroke timeout -- caught it showing a 7-day
    # total (1h39m) SMALLER than its own best_day figure for a day inside
    # that same range (8h39m), which can't be right if both came from the
    # same heartbeats. /summaries is never cached (computed fresh per
    # request), so this builds every number here from summing 7 days of
    # that instead -- self-consistent by construction, no stale-total risk.
    # ai_additions/ai_model_line_changes used to back the "N lines shipped"
    # line directly from WakaTime -- dropped after checking it against real
    # commits. WakaTime's own community has open reports of this exact
    # plugin's line counter being "completely incorrect"; confirmed it
    # firsthand against channel-3's actual commit stats this week (~12,900
    # real additions vs. ~700 reported here, 18x off). fetch_lines_shipped()
    # replaces it with GitHub's own verifiable diff stats instead.
    summaries = wakatime_api(f'/users/current/summaries?range={RANGE}')['data']

    total_seconds = sum(day['grand_total']['total_seconds'] for day in summaries)
    if total_seconds == 0:
        # A week with no heartbeats at all -- Darwin's projects don't get
        # touched daily, so this isn't an error state, just a real "nothing
        # to report" week. Skip the rest of the fetch (languages/peak
        # day/lines shipped would all be empty or misleading anyway) and let
        # build_html render its own dedicated quiet-week layout instead of
        # a normal card full of zeroes.
        return {'is_empty': True, 'vscode_icon_b64': fetch_vscode_icon_b64()}

    active_days = sum(1 for day in summaries if day['grand_total']['total_seconds'] > 0) or 1

    lang_seconds = {}
    for day in summaries:
        for lang in day.get('languages', []):
            if lang['name'] == 'Other':
                continue
            lang_seconds[lang['name']] = lang_seconds.get(lang['name'], 0) + lang['total_seconds']
    named_total = sum(lang_seconds.values()) or 1
    languages = [
        {
            'name': name,
            'percent': seconds / named_total * 100,
            'color': LANGUAGE_COLORS.get(name, DEFAULT_LANGUAGE_COLOR),
            'icon_b64': fetch_language_icon_b64(name),
        }
        for name, seconds in sorted(lang_seconds.items(), key=lambda kv: -kv[1])[:5]
    ]

    best_day = max(summaries, key=lambda day: day['grand_total']['total_seconds'], default=None)
    peak_day = None
    if best_day and best_day['grand_total']['total_seconds'] > 0:
        weekday = datetime.strptime(best_day['range']['date'], '%Y-%m-%d').weekday()
        peak_day = {'weekday': WEEKDAY_NAMES[weekday], 'duration': best_day['grand_total']['text']}

    vscode_icon_b64 = fetch_vscode_icon_b64()
    lines_shipped = fetch_lines_shipped()

    return {
        'is_empty': False,
        'human_readable_total': format_duration(total_seconds),
        # Divided by days actually worked, not all 7 calendar days -- Darwin
        # doesn't touch the IDE daily, he does full blocks (a whole morning,
        # a whole night) on the days he does. Dividing by 7 regardless
        # waters a real multi-hour day down into a misleadingly small
        # "average", which is the opposite of what this number should show.
        'daily_average': format_duration(total_seconds / active_days),
        'languages': languages,
        'peak_day': peak_day,
        'vscode_icon_b64': vscode_icon_b64,
        'lines_shipped': lines_shipped,
    }


CSS = '''
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,400;0,500;0,600;0,700;1,400&family=JetBrains+Mono:wght@500;700&display=swap');
body { background:#000; margin:0; padding:20px; overflow:hidden; font-family:Inter,-apple-system,Segoe UI,Helvetica,Arial,sans-serif; }
.card { width:340px; background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.08); border-radius:18px; padding:22px 24px; position:relative; overflow:hidden; }
.accent { position:absolute; top:0; left:0; width:100%; height:3px; }
.stat-label { font-size:11px; color:#ffab91cc; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:6px; font-weight:700; }
.stat-label::before { content:'\\2022\\a0'; color:#f472a0; }
.hero { display:flex; align-items:baseline; gap:9px; }
.hero-num { font-family:"JetBrains Mono",monospace; font-size:36px; font-weight:700; color:#fff; line-height:1; }
.hero-sub, .tagline { display:flex; align-items:center; gap:7px; font-size:12.5px; color:#a7a0a7; margin-top:7px; }
.inline-icon { width:14px; height:14px; flex-shrink:0; opacity:0.8; }
.mono-num { font-family:"JetBrains Mono",monospace; font-weight:700; color:#d8d8d8; }
.empty-note { font-size:14px; color:#a7a0a7; margin-top:14px; line-height:1.5; }
.divider { height:1px; background:rgba(255,255,255,0.08); margin:16px 0; }
.bar-row { display:flex; align-items:center; gap:10px; }
.bar-row + .bar-row { margin-top:12px; }
.bar-icon, .peak-icon, .brand-icon { width:16px; height:16px; flex-shrink:0; }
.peak-icon { width:19px; height:19px; }
.bar-dot { width:9px; height:9px; border-radius:50%; flex-shrink:0; }
.bar-name { font-size:14px; color:#e5e5e5; font-weight:600; width:96px; flex-shrink:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.bar-track { flex:1; height:8px; background:rgba(255,255,255,0.06); border-radius:999px; overflow:hidden; }
.bar-fill { display:block; height:100%; border-radius:999px; }
.bar-pct { font-family:"JetBrains Mono",monospace; font-size:12px; font-weight:700; color:#e5e5e5; width:38px; text-align:right; flex-shrink:0; }
.peak-row { display:flex; align-items:center; gap:10px; }
.peak-day { font-size:14px; color:#e5e5e5; font-weight:600; width:96px; flex-shrink:0; }
.peak-dur { font-family:"JetBrains Mono",monospace; font-size:13px; font-weight:700; color:#e5e5e5; flex:1; text-align:right; }
.brand { display:flex; align-items:center; justify-content:space-between; font-size:13px; color:#a7a0a7; margin-top:18px; }
.brand-side { display:flex; align-items:center; gap:8px; }
.vscode-dim { filter:grayscale(1) opacity(0.45); }
.zzz { font-family:"JetBrains Mono",monospace; font-weight:700; color:#8a8a8a; line-height:1; letter-spacing:0.02em; }
.zzz span:nth-child(1) { font-size:44px; }
.zzz span:nth-child(2) { font-size:32px; opacity:0.75; }
.zzz span:nth-child(3) { font-size:22px; opacity:0.5; }
'''


def bar_rows(items, name_key='name'):
    rows = []
    for item in items:
        if item.get('icon_b64'):
            marker = f'<img class="bar-icon" src="data:image/svg+xml;base64,{item["icon_b64"]}"/>'
        else:
            marker = f'<span class="bar-dot" style="background:{item["color"]}; box-shadow:0 0 8px {item["color"]}aa;"></span>'
        fill_light = lighten(item['color'])
        rows.append(f'''<div class="bar-row">
{marker}
<span class="bar-name">{item[name_key]}</span>
<span class="bar-track"><span class="bar-fill" style="width:{item['percent']}%; background:linear-gradient(90deg, {item['color']}, {fill_light}); box-shadow:0 0 10px {item['color']}99;"></span></span>
<span class="bar-pct">{item['percent']:.0f}%</span>
</div>''')
    return '\n'.join(rows)


ACCENT_GRADIENT = f'linear-gradient(90deg, {PINK}, {PEACH} 55%, transparent)'


EMPTY_NOTE = 'No heartbeats this week. Asleep, or just away from it.'


def build_html(data):
    if data['vscode_icon_b64']:
        vscode_marker = f'<img class="brand-icon" src="data:image/svg+xml;base64,{data["vscode_icon_b64"]}"/>'
    else:
        vscode_marker = ''

    if data['is_empty']:
        dim_vscode = f'<img class="brand-icon vscode-dim" src="data:image/svg+xml;base64,{data["vscode_icon_b64"]}"/>' if data['vscode_icon_b64'] else ''
        return f'''<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="card">
<div class="accent" style="background:{ACCENT_GRADIENT}; opacity:0.4;"></div>
<div class="stat-label">coding time &middot; last week</div>
<div class="zzz"><span>Z</span><span>z</span><span>z</span></div>
<div class="empty-note">{EMPTY_NOTE}</div>
<div class="divider"></div>
<div class="brand">
<span class="brand-side">{dim_vscode}VS Code</span>
<span class="brand-side">{WAKATIME_MARK}wakatime.com</span>
</div>
</div>
</body></html>'''

    lang_rows = bar_rows(data['languages'])

    peak_block = ''
    if data['peak_day']:
        peak_block = f'''<div class="divider"></div>
<div class="stat-label">peak day</div>
<div class="peak-row">
{PEAK_ICON}
<span class="peak-day">{data['peak_day']['weekday']}</span>
<span class="peak-dur">{data['peak_day']['duration']}</span>
</div>'''

    return f'''<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="card">
<div class="accent" style="background:{ACCENT_GRADIENT};"></div>
<div class="stat-label">coding time &middot; last week</div>
<div class="hero"><div class="hero-num">{data['human_readable_total']}</div></div>
<div class="hero-sub">{CLOCK_ICON}<span><span class="mono-num">{data['daily_average']}</span> avg on active days</span></div>
<div class="tagline">{CODE_ICON}<span><span class="mono-num">{data['lines_shipped']:,}</span> lines shipped this week</span></div>
<div class="divider"></div>
<div class="stat-label">top languages</div>
{lang_rows}
{peak_block}
<div class="brand">
<span class="brand-side">{vscode_marker}VS Code</span>
<span class="brand-side">{WAKATIME_MARK}wakatime.com</span>
</div>
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
        '--force-device-scale-factor=2', '--window-size=460,700',
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
    if data['is_empty']:
        debug_data = {k: v for k, v in data.items() if k != 'vscode_icon_b64'}
    else:
        debug_data = {k: v for k, v in data.items() if k not in ('languages', 'vscode_icon_b64')}
        debug_data['languages'] = [{kk: vv for kk, vv in l.items() if kk != 'icon_b64'} for l in data['languages']]
    print(json.dumps(debug_data, indent=2, ensure_ascii=False))  # sanity-check the shape before trusting the render

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        html_path = tmp / 'card.html'
        html_path.write_text(build_html(data), encoding='utf-8')

        out_path = HERE.parent / 'assets' / 'wakatime_card.png'
        render(html_path, tmp, out_path, find_chrome())
        print('written', out_path)


if __name__ == '__main__':
    main()
