"""
Builds assets/wakatime_card.png from WakaTime's Stats API (coding time, top
languages, and a bar per day of the window) plus real lines-shipped
totals pulled straight
from GitHub's commit diffs (see fetch_lines_shipped) instead of WakaTime's
own line counter, which turned out to be unreliable for this account.

Every figure on the card comes from /summaries, computed fresh per request,
so nothing here can disagree with anything else on it. Two things this card
used to get wrong: it claimed "VS Code" as the editor (see the note above
EDITOR -- nothing here has ever reported VS Code), and the header said
"last week" for what is a rolling 7 days ending today.

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
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
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
RANGE = 'last_7_days'
GH_USERNAME = 'dau-in'

# Same GitHub-linguist-derived colors + devicon icons as build_last_commit_card.py.
LANGUAGE_COLORS = json.loads((HERE / 'language_colors.json').read_text(encoding='utf-8'))
DEFAULT_LANGUAGE_COLOR = '#8b8b8b'
LANGUAGE_ICON_SLUGS = json.loads((HERE / 'language_icon_slugs.json').read_text(encoding='utf-8'))
DEVICON_URL = 'https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/{slug}/{slug}-original.svg'

# WakaTime names a few things differently from GitHub linguist, which both
# tables above are keyed by. "Git" is its bucket for commit messages and
# rebase todo files; linguist splits those into Git Commit, Git Config and so
# on, so a lookup on "Git" found nothing and the row got a plain grey dot.
# Git Config carries the git icon and git's orange.
LINGUIST_NAME = {'Git': 'Git Config'}

# EDITOR: no editor/IDE breakdown on this card, deliberately. WakaTime only sees
# what has its plugin installed, and here that's the Claude Code and
# Antigravity harnesses -- not VS Code, which is where the actual editing
# happens but has no WakaTime extension on this machine. So the API's
# "editors" field names harnesses, and any section built on it would be
# telling people the wrong thing about how this profile's owner works. The
# card used to paper over that with a hardcoded "VS Code" chip, which was
# worse: a flat claim the data never supported. Showing nothing is the
# honest option until the IDE itself reports.

# No accent colour any more. The pink+peach duo that used to tint the top bar,
# the peak day and the labels went with the ambient skin (card_skin.py): the
# interface is black/white/grey on every card, and colour only comes from
# content -- here, the language icons. The peak day and the top language are
# picked out in white instead.

# devicon has no WakaTime icon -- their real mark is a waveform/heartbeat
# line, redrawn here as a simple bars glyph rather than attempting an exact
# logo trace (same spirit as the hand-drawn star in build_passport_own.py).
WAKATIME_MARK = '''<svg class="brand-icon" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
<rect x="1" y="6" width="2.4" height="4" rx="1.2" fill="currentColor"/>
<rect x="5.1" y="2.5" width="2.4" height="11" rx="1.2" fill="currentColor"/>
<rect x="9.2" y="5" width="2.4" height="6" rx="1.2" fill="currentColor"/>
<rect x="13.3" y="7" width="2.4" height="2" rx="1" fill="currentColor"/>
</svg>'''

# Small inline glyphs for the two lines under the hero number -- a clock for
# the daily average, a code-bracket for lines shipped. Muted grey so they
# read as quiet supporting icons, not competing with the figures they sit by.
CLOCK_ICON = '''<svg class="inline-icon" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
<circle cx="8" cy="8" r="6.5" stroke="#8a8a8a" stroke-width="1.3"/>
<path d="M8 4.5V8l2.5 1.5" stroke="#8a8a8a" stroke-width="1.3" stroke-linecap="round"/>
</svg>'''
CODE_ICON = '''<svg class="inline-icon" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M5.5 3.5 1.5 8l4 4.5M10.5 3.5l4 4.5-4 4.5" stroke="#8a8a8a" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
</svg>'''


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
    return json.loads(urlopen_retry(req))


def fetch_language_icon(language):
    slug = LANGUAGE_ICON_SLUGS.get(LINGUIST_NAME.get(language, language))
    if not slug:
        return None
    try:
        svg = urlopen_retry(DEVICON_URL.format(slug=slug), timeout=10)
        return {'b64': base64.b64encode(svg).decode(), 'dark': card_skin.is_dark_icon(svg)}
    except Exception:
        return None


def github_api(path):
    headers = {'User-Agent': GH_USERNAME, 'Accept': 'application/vnd.github+json'}
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        headers['Authorization'] = f'Bearer {token}'
    req = urllib.request.Request(f'https://api.github.com{path}', headers=headers)
    return json.loads(urlopen_retry(req))


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
        return {'is_empty': True}

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
            'color': LANGUAGE_COLORS.get(LINGUIST_NAME.get(name, name), DEFAULT_LANGUAGE_COLOR),
            'icon': fetch_language_icon(name),
        }
        for name, seconds in sorted(lang_seconds.items(), key=lambda kv: -kv[1])[:5]
    ]

    # One entry per day in the window, in order, for the bar chart. The peak
    # used to be a sentence ("14 hrs 56 mins on Friday, the peak of the
    # week"); the tallest bar says that by itself, and the other six days --
    # which that sentence threw away -- come along for free. It also makes
    # the rolling window legible: the initials start on whatever day is six
    # back from today, so they visibly shift along by one every day instead
    # of looking like a Monday-to-Sunday week that never resets.
    peak_seconds = max((day['grand_total']['total_seconds'] for day in summaries), default=0)
    day_bars = []
    for day in summaries:
        seconds = day['grand_total']['total_seconds']
        weekday = datetime.strptime(day['range']['date'], '%Y-%m-%d').weekday()
        day_bars.append({
            'initial': WEEKDAY_NAMES[weekday][0],
            'date': day['range']['date'],
            'seconds': seconds,
            'is_peak': seconds > 0 and seconds == peak_seconds,
            'label': f'{round(seconds / 3600)}h' if seconds >= 1800 else '',
        })

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
        'day_bars': day_bars,
        'lines_shipped': lines_shipped,
    }


CSS = '''
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap');
body { margin:0; padding:20px; overflow:hidden; font-family:"Space Grotesk",-apple-system,Segoe UI,Helvetica,Arial,sans-serif; }
.card { width:340px; border:1px solid rgba(255,255,255,0.08); border-radius:18px; padding:22px 24px; }
.label-row { display:flex; align-items:baseline; justify-content:space-between; margin-bottom:8px; }
.hero { display:flex; align-items:baseline; gap:9px; }
.hero-num { font-family:"Space Mono",monospace; font-size:36px; font-weight:700; color:#fff; line-height:1; }
.hero-sub, .tagline { display:flex; align-items:center; gap:7px; font-size:12.5px; color:#a7a0a7; margin-top:7px; }
.inline-icon { width:14px; height:14px; flex-shrink:0; opacity:0.8; }
.mono-num { font-family:"Space Mono",monospace; font-weight:700; color:#d8d8d8; }
.empty-note { font-size:14px; color:#a7a0a7; margin-top:14px; line-height:1.5; }
.divider { height:1px; margin:16px 0; }
.days { display:flex; align-items:flex-end; gap:10px; margin-top:18px; }
.day { flex:1; display:flex; flex-direction:column; align-items:center; gap:6px; }
.day-bar { width:13px; border-radius:7px; background:rgba(255,255,255,0.14); }
.day-bar.peak { background:#f2f2f2; box-shadow:0 0 12px rgba(255,255,255,0.25); }
.day-name { font-family:"Space Mono",monospace; font-size:10px; font-weight:700; color:#5f5a5f; }
.day.is-peak .day-name { color:#f2f2f2; }
.day-hours { font-family:"Space Mono",monospace; font-size:10px; font-weight:700; color:#5f5a5f; height:13px; }
.day.is-peak .day-hours { color:#f2f2f2; }
.bar-row { display:flex; align-items:center; gap:10px; }
.bar-row + .bar-row { margin-top:12px; }
.bar-icon, .brand-icon { width:16px; height:16px; flex-shrink:0; }
.bar-dot { width:9px; height:9px; border-radius:50%; flex-shrink:0; margin:0 3.5px; }
.bar-name { font-size:14px; color:#e5e5e5; font-weight:600; width:110px; flex-shrink:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.bar-track { flex:1; height:8px; background:rgba(255,255,255,0.06); border-radius:999px; overflow:hidden; }
.bar-fill { display:block; height:100%; border-radius:999px; }
.bar-pct { font-family:"Space Mono",monospace; font-size:12px; font-weight:700; color:#e5e5e5; width:38px; text-align:right; flex-shrink:0; }
.source { display:flex; align-items:center; justify-content:flex-end; gap:8px; font-size:12.5px; color:#6f6a6f; margin-top:18px; }
.zzz { font-family:"Space Mono",monospace; font-weight:700; color:#8a8a8a; line-height:1; letter-spacing:0.02em; }
.zzz span:nth-child(1) { font-size:44px; }
.zzz span:nth-child(2) { font-size:32px; opacity:0.75; }
.zzz span:nth-child(3) { font-size:22px; opacity:0.5; }
'''


def bar_rows(items, name_key='name'):
    rows = []
    for i, item in enumerate(items):
        if item.get('icon'):
            dark = ' dark-icon' if item['icon']['dark'] else ''
            marker = f'<img class="bar-icon{dark}" src="data:image/svg+xml;base64,{item["icon"]["b64"]}"/>'
        else:
            marker = f'<span class="bar-dot" style="background:{item["color"]}; box-shadow:0 0 8px {item["color"]}aa;"></span>'
        fill = '#e8e8e8' if i == 0 else '#7a7a7a'
        rows.append(f'''<div class="bar-row">
{marker}
<span class="bar-name">{item[name_key]}</span>
<span class="bar-track"><span class="bar-fill" style="width:{item['percent']}%; background:{fill};"></span></span>
<span class="bar-pct">{item['percent']:.0f}%</span>
</div>''')
    return '\n'.join(rows)


NEWLINE = chr(10)

EMPTY_NOTE = 'No heartbeats in seven days. Asleep, or just away from it.'


def label_row(text, tag=''):
    # Section labels used to carry a bullet glyph and the header read
    # "coding time . last week" with a middot between the two halves. Both
    # are gone: no dot separators anywhere on this card. The range now sits
    # as its own right-aligned tag, which says the same thing with layout
    # instead of punctuation -- and says it more accurately, since the range
    # is a rolling 7 days that includes today, not "last week".
    tag_html = f'<span class="range-tag">{tag}</span>' if tag else ''
    return f'<div class="label-row"><span class="stat-label">{text}</span>{tag_html}</div>'


def build_html(data, avatar=None):
    if data['is_empty']:
        return f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}{card_skin.CSS}</style></head><body>
<div class="card">{card_skin.ambient(avatar)}
{label_row(card_skin.label('wakatime', 'coding-time'), '--7d')}
<div class="zzz"><span>Z</span><span>z</span><span>z</span></div>
<div class="empty-note">{EMPTY_NOTE}</div>
<div class="divider"></div>
<div class="source">{WAKATIME_MARK}wakatime.com</div>
</div>
</body></html>"""

    # Peak day is a supporting fact about the same total, so it reads as one
    # of the lines under the hero number rather than its own titled section
    # at the bottom. That was the inconsistency down there: a stat section, a
    # (wrong) editor chip and a source credit all sharing one visual footing
    # with nothing saying which was data and which was attribution.
    # Heights are relative to the week's own peak, not to a fixed hour
    # scale: the shape of the week is the point, and a fixed scale would
    # flatten every bar to nothing on a quiet week. Days with no heartbeats
    # keep a 4px stub so the row still reads as seven days rather than a
    # chart with holes in it.
    peak_seconds = max((d['seconds'] for d in data['day_bars']), default=0) or 1
    bars = []
    for day in data['day_bars']:
        height = max(round(day['seconds'] / peak_seconds * 74), 4)
        peak_class = ' peak' if day['is_peak'] else ''
        bars.append(
            f'<div class="day{" is-peak" if day["is_peak"] else ""}">'
            f'<span class="day-hours">{day["label"]}</span>'
            f'<span class="day-bar{peak_class}" style="height:{height}px"></span>'
            f'<span class="day-name">{day["initial"]}</span></div>'
        )
    day_chart = '<div class="days">' + ''.join(bars) + '</div>'

    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}{card_skin.CSS}</style></head><body>
<div class="card">{card_skin.ambient(avatar)}
{label_row(card_skin.label('wakatime', 'coding-time'), '--7d')}
<div class="hero"><div class="hero-num">{data['human_readable_total']}</div></div>
<div class="hero-sub">{CLOCK_ICON}<span><span class="mono-num">{data['daily_average']}</span> avg on active days</span></div>
{day_chart}
<div class="tagline">{CODE_ICON}<span><span class="mono-num">{data['lines_shipped']:,}</span> lines shipped this week</span></div>
<div class="divider"></div>
{label_row(card_skin.label('wakatime', 'languages'))}
{bar_rows(data['languages'])}
<div class="source">{WAKATIME_MARK}wakatime.com</div>
</div>
</body></html>"""


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
    card_skin.render(chrome, html_path, out_path, '460,700')


def main():
    import tempfile

    data = fetch_data()
    if data['is_empty']:
        debug_data = dict(data)
    else:
        debug_data = {k: v for k, v in data.items() if k != 'languages'}
        debug_data['languages'] = [{kk: vv for kk, vv in l.items() if kk != 'icon'} for l in data['languages']]
    print(json.dumps(debug_data, indent=2, ensure_ascii=False))  # sanity-check the shape before trusting the render

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        html_path = tmp / 'card.html'
        # No avatar of its own on this card, so the ambient background is the
        # GitHub one -- it's the coding card, same as last-commit.
        html_path.write_text(build_html(data, card_skin.github_avatar(GH_USERNAME)), encoding='utf-8')

        out_path = HERE.parent / 'assets' / 'wakatime_card.png'
        render(html_path, tmp, out_path, find_chrome())
        print('written', out_path)


if __name__ == '__main__':
    main()
