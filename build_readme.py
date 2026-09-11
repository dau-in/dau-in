# -*- coding: utf-8 -*-
import os
import time
from pathlib import Path

import pyfiglet

# raw.githubusercontent.com (what a relative <img src> in a README actually
# resolves to) caches by URL -- the asset's bytes on disk can be fully
# updated and viewers still get a stale copy for a while, because the path
# never changes between renders. A query string that changes every run
# forces a fresh fetch instead of a cache hit. GITHUB_RUN_ID (auto-injected
# by Actions), not GITHUB_SHA -- most refreshes are the cards' own data
# changing (WakaTime, last commit) with no new commit to this repo at all,
# so the SHA would stay identical run to run and never bust anything for
# the case that matters most. update-widgets.yml only re-runs this script
# when a card actually changed, so this still doesn't churn on no-op runs.
CACHE_BUST = os.environ.get('GITHUB_RUN_ID', str(int(time.time())))

def build_terminal_box(command, lines, prompt='[dauin@cachyos ~]$ '):
    # Plain ASCII border (+/-/|), not the Unicode box-drawing block (was
    # ┌─│└┘) -- confirmed on the GitHub mobile app: that block falls back to
    # a different, poorly-hinted font there, and the vertical bar renders as
    # a dashed line instead of solid once the box is scrolled horizontally
    # (screenshots from the user). Same reasoning as the ASCII-only content
    # below: a glyph outside plain ASCII has no guaranteed consistent shape
    # across monospace fonts.
    header = f'+- {prompt}'
    body_lines = [f'$ {command}', ''] + lines + ['', f'{prompt}_']

    max_len = max(len(l) for l in body_lines)
    width = max_len + 6

    top = header + '-' * (width - len(header) - 1) + '+'
    bot = '+' + '-' * (width - 2) + '+'

    body = []
    for l in body_lines:
        pad = width - 4 - len(l)
        body.append('| ' + l + ' ' * max(pad, 0) + ' |')

    return '\n'.join([top] + body + [bot])

def strip_blank_lines(s):
    lines = s.split('\n')
    while lines and lines[0].strip() == '':
        lines.pop(0)
    while lines and lines[-1].strip() == '':
        lines.pop()
    return '\n'.join(lines)

def sep():
    # a real <hr> is always 100% of the container width -- unlike a fixed-length
    # dash string it can't overflow/wrap on narrow viewports, and unlike a marker
    # between two <hr>s it can't look unfinished/disconnected. plain and boring on purpose.
    return '<hr>'

name_banner = strip_blank_lines(pyfiglet.figlet_format('DAUIN', font='thin'))

# pure ASCII icons and standard single-column box drawing to guarantee
# identical width on every monospace font and mobile OS without wrapping breaks.
whoami_cpp_lines = [
    'namespace dauin {',
    '    constexpr auto role     = "Computer Engineer.";',
    '    constexpr auto ai       = "\\"Why is AI so addictive?\\" "',
    '                              "-- because architecting autonomy is fun.";',
    '    constexpr auto stack    = { "full-stack dev", "IT support", "network" };',
    '    constexpr auto mindset  = "Perpetual student with endless curiosity "',
    '                              "for how things tick.";',
    '    constexpr auto hardware = "Hardware lover at the core.";',
    '    constexpr auto vibe     = "Just for fun, I guess...";',
    '    constexpr auto habitat  = "Living in the terminal (CachyOS enjoyer), "',
    '                              "but Windows is my cozy fallback.";',
    '    constexpr auto loop     = "Clauding my way forward, step by step.";',
    '}',
    '',
    '// -- [ Memory Log ] ----------------------------------------------------',
    '// "Everything that lives is designed to end"...',
    '// meanwhile, I leave proof of my existence on my passport ↓',
]
whoami_box = build_terminal_box('cat whoami.cpp', whoami_cpp_lines)

# Active choice: process-monitor style ($ ps) -- one line per project,
# columns aligned (PID/STAT/PROJECT/DETAILS). The tree ~/projects version
# tried before this read worse: two uneven lines per project (a short
# name+tag line, then a long indented description line) zigzags instead of
# lining up, where this is a clean table.
projects_ps_lines = [
    'PID  STAT  PROJECT     DETAILS',
    '001  RUN   channel-3   NES emulator (WebGL CRT)',
    '002  DEV   kintsugi    Go TUI / Windows DISM',
]

# Saved in case you want to switch back to it later:
projects_tree_lines = [
    '|-- channel-3 [live]',
    '|   `-- WebGL NES emulator, CRT shaders, netplay',
    '`-- kintsugi  [wip]',
    '    `-- Go TUI for Windows DISM and ISO tooling',
]

projects_box = build_terminal_box('ps -o pid,stat,command -C projects', projects_ps_lines)
# To switch back to the tree version, simply change to:
# projects_box = build_terminal_box('tree ~/projects', projects_tree_lines)

# GitHub injects style="max-width:100%" into every <img> it renders, which
# makes an image contribute *zero* min-content width to the table column it
# sits in -- the column only ever gets whatever width is left over after its
# siblings. Measured on the live rendered profile at a 375px viewport: the
# projects row's code-block column demands 406px inside a 293px container,
# so auto table layout hands it everything and the photo column collapses to
# 27px (td padding alone). The photo then renders at 0x0 -- present in the
# DOM, invisible on screen. That's the whole bug ("the second photo doesn't
# show up in the GitHub mobile app"), and it's why the same row survives up
# top: that table's code block is only ~196px wide, so leftovers remain.
# A 1x1 spacer *image* does not fix it -- zero min-content for exactly the
# same reason, verified. Non-breaking spaces are real text, so they do claim
# min-content and hold the column open: 40 of them measure ~153px, close to
# the photo's own 160px and still under the <td width="170"> the desktop
# layout already uses, so desktop rendering is untouched (170px -> 173px).
# The <br> is load-bearing: without it the run shares the image's line, the
# column's *max*-content becomes 160+153, and desktop widens to match.
#
# Sized to 69px (18 of them), which is what the *top* photo renders at, not
# to the 160px the image would like. The top one is deliberately left with
# no spacer at all: its column takes whatever the name banner leaves over,
# which is exactly why that row still fits a phone screen with nothing to
# scroll. Pinning it wider was tried and reverted -- it pushed the row to
# 376px, so the name needed a sideways drag, and the spacer's own line adds
# ~24px under the image, which showed up as a gap on desktop because
# nothing else in that row is tall enough to absorb it. Down here the ps
# box is ~190px tall, so the same line costs nothing.
# Both <img> carry width=180 -- the GIFs' own native size, so desktop draws
# them 1:1 with no scaling at all -- and the <td> here is 207 (180 + the
# 27px GitHub puts on every cell) so this column actually hands over those
# 180. On the web
# that attribute is ignored for a GIF anyway (GitHub wraps animated images
# in <animated-image> and forces the inner img to width:100%, so the column
# decides), but the mobile app has no such wrapper and goes by the
# attribute. The two can only match exactly at one container width, since
# the top one is elastic and this one is pinned -- 69px matches what
# GitHub's mobile web gives the top photo in its 293px article column.
_SPACER_LINE = '&nbsp;' * 18
# One run above the image and one below, not just below: a single run leaves
# the image sitting high in its cell (measured 7px of air above it against
# 33px below, since valign centers image+run as one block). Two runs cost a
# second line of height but put the image back on the cell's centre line.
# Both runs are the same width, so the column's min-content is unchanged.
PHOTO_COL_SPACER_TOP = _SPACER_LINE + '<br>'
PHOTO_COL_SPACER_BOTTOM = '<br>' + _SPACER_LINE

# Rendered width of the last-commit / wakatime cards, in px. Measured, not
# guessed: the table above renders at photo column 207 + projects box 406 +
# 1px of border = 614, and a card's own table comes out at CARD_WIDTH + 28,
# so 586 puts the two tables at exactly the same width and the section reads
# as one block. Re-measure both whenever either column changes.
# max-width:100% still shrinks the cards to fit a phone.
CARD_WIDTH = 586

discord_url = ('https://lanyard.cnrad.dev/api/780932598922084384'
               '?theme=dark&bg=000000&borderRadius=18px&animated=true'
               '&idleMessage=bored%2C+for+now&showDisplayName=true')

# written by scripts/build_last_commit_card.py alongside the card itself --
# the actual commit URL changes every run, and this template has no way to
# reach the GitHub API on its own to look it up. Falls back to the profile
# page itself on a fresh checkout that hasn't run the card script yet.
last_commit_url_path = Path('assets/last_commit_url.txt')
last_commit_url = (
    last_commit_url_path.read_text(encoding='utf-8').strip()
    if last_commit_url_path.exists() else 'https://github.com/dau-in'
)


# typing_dark/light.png are self-built animated APNGs (scripts/build_typing_png.py),
# not the old readme-typing-svg widget -- that service only accepts Google
# Fonts, and Departure Mono (the pixel font here) isn't on Google Fonts. Two
# variants (near-white text / near-black text, no drop shadow on either)
# because one color can't read well on both GitHub themes. The #gh-*-mode-only
# swap only works through markdown ![]() image syntax, not raw <img> tags --
# confirmed by fetching the rendered page, a plain <img src="...#gh-dark-mode-only">
# just shows both, unhidden -- so this needs blank lines to drop out of the
# surrounding HTML block and be parsed as markdown, and can't take a width=
# (the files are already baked out at their intended display size instead).
# <div align="center">, not <p align="center"> -- a <p> auto-closes the moment
# the blank line lets markdown open its own new <p> for the image, so the two
# end up as unrelated siblings and "center" never reaches the image (that's
# why it rendered left-aligned). text-align inherits into a <div>'s children
# the same way, but a <div> can legally contain a <p> instead of closing early.
readme = f'''<div align="center">

![name](assets/typing_dark.png#gh-dark-mode-only)
![name](assets/typing_light.png#gh-light-mode-only)

</div>

<table align="center"><tr>
<td><img width="180" src="assets/section1_photos.gif"/></td>
<td align="center" valign="middle">

```

{name_banner}

```

</td>
</tr></table>

<!-- table+td, not <div align="center"> -- on real mobile (GitHub app and
     Chrome mobile both) this box was rendering broken: overflow-x:auto is
     set on the <pre> same as everywhere else, but nothing above it in a bare
     <div> ancestor chain forces a definite (viewport-bound) width, so the
     unwrappable (white-space:pre) 846px-wide content just expands its own
     box instead of scrolling inside a contained one. A <td> is the one
     wrapper already proven (by the rest of this file) to hold its content
     to a definite width without GitHub stripping/ignoring it. -->
<table align="center"><tr><td align="center">

```
{whoami_box}
```

</td></tr></table>

{sep()}

<!-- photo + projects box only. The last-commit and wakatime cards used to
     be colspan rows of this same table, so both halves would read as one
     block; they were split into the table below once that turned out to
     drag the cards' own width along with this row's (see the note there).
     Matching widths and align="center" on both keep them reading as one
     section anyway. -->
<table align="center">
<tr>
<td width="207" align="center" valign="middle">{PHOTO_COL_SPACER_TOP}<img src="assets/section2_photos_v2.gif" width="180"/>{PHOTO_COL_SPACER_BOTTOM}</td>
<td width="360" valign="middle">

```
{projects_box}
```

</td>
</tr>
</table>

<!-- the two cards sit in their OWN table, not as colspan rows of the one
     above. They used to live there so both halves read as one block, but a
     colspan cell is as wide as its table, and that table is as wide as the
     photo column plus the (unwrappable, 406px) projects box -- 587px, which
     on a phone means the cards themselves had to be scrolled sideways to be
     seen whole, unlike every other card on the page. Split out, this table
     has nothing forcing it wide, so it shrinks to the viewport and the cards
     land complete. They still line up with the box above on desktop: 559 +
     28px of td padding is exactly the 587 that table renders at. width= here
     is a pixel count, NOT width="100%" -- a percentage resolves against a
     table that is itself sizing to its contents, which collapses the whole
     thing to 28px (measured). Re-measure CARD_WIDTH if the projects box ever
     changes width. -->
<table align="center">
<tr><td align="center"><a href="{last_commit_url}"><img src="assets/last_commit_card.png?v={CACHE_BUST}" width="{CARD_WIDTH}"/></a></td></tr>
<tr><td align="center"><img src="assets/wakatime_card.png?v={CACHE_BUST}" width="{CARD_WIDTH}"/></td></tr>
</table>

<!-- wakatime_card.png has no <a> wrapper -- unlike every other linked card
     here, there's nowhere real to send a click: this WakaTime account's
     profile is private (no public username set either), so a link would
     either 404 or point at a page that shows nothing. Rebuilt alongside the
     other cards by update-widgets.yml (scripts/build_wakatime_card.py). -->
<!-- TODO: add real repo link once Kintsugi has a demoable run -->

{sep()}

<p align="center">∴ off the clock: games, music, and a terminal that never quite closes — full taste below ↓</p>

<!-- back to one unified table (colspan for passport/discord) -- three
     separate tables let each widget size independently, but on the native
     GitHub mobile app a <table> gets forced to width:100% regardless of
     what's inside it, which broke align="center" once the image was much
     narrower than that forced width (dead space that should've centered
     just... didn't, in the app specifically -- fine on web and Chrome
     mobile). Small standalone tables made that visible; one wide table
     doesn't leave enough dead space for it to be noticeable. width="100%"
     on the passport/discord cells fills whatever the row actually renders
     as; pinning width= on the steam/spotify <td>s (their own natural size,
     +27 for GitHub's fixed td padding/border) keeps that column from being
     inflated by the wider colspan cells. -->
<table align="center">
<tr><td colspan="2" align="center"><a href="https://passportdex.com/dauin"><img src="assets/passport_card.png" width="100%"/></a></td></tr>
<tr>
<td width="247" align="center"><a href="https://steamcommunity.com/id/dauin"><img src="assets/steam_card.png?v={CACHE_BUST}" width="220"/></a></td>
<td width="247" align="center"><a href="https://open.spotify.com/user/31aluwrafhtrzpee4pqzyodbvusm"><img src="assets/spotify_card.png?v={CACHE_BUST}" width="220"/></a></td>
</tr>
<tr><td colspan="2" align="center"><a href="https://discord.com/users/780932598922084384"><img src="{discord_url}" width="100%" alt="discord"/></a></td></tr>
</table>

<!-- steam_card.png, spotify_card.png, and wakatime_card.png are rebuilt
     every 30 min and on every push by .github/workflows/update-widgets.yml
     (scripts/build_steam_card.py, build_spotify_card.py, build_wakatime_card.py)
     -- never hand-edited. -->

{sep()}

<p align="center"><sub>◇ art by <a href="https://x.com/inoitoh">@inoitoh</a> on twt</sub></p>

<!-- TODO: replace static passport card with a live embed once passportdex offers one -->
'''

with open('README.md', 'w', encoding='utf-8') as f:
    f.write(readme)
print('written, whoami box width:', len(whoami_box.split(chr(10))[0]))
