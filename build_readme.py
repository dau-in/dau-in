# -*- coding: utf-8 -*-
import pyfiglet

def box(title, groups):
    lines = [l for g in groups for l in g]
    width = max([len(l) for l in lines] + [len(title) + 4]) + 6
    # top line was 1 char longer than every other line ('┌─ title ─┐' == width+1,
    # while body/bottom lines == width) -- that's why '┐' never lined up with the
    # '│' column below it, even though '┘' (computed the same way as the body) did.
    top = '┌─ ' + title + ' ' + '─' * (width - len(title) - 5) + '┐'
    bot = '└' + '─' * (width - 2) + '┘'
    mid = '├' + '─' * (width - 2) + '┤'

    def row(l):
        pad = width - 2 - len(l)
        return '│ ' + l + ' ' * max(pad - 1, 0) + '│'

    body = []
    for i, g in enumerate(groups):
        if i > 0:
            body.append(mid)
        body.extend(row(l) for l in g)
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

# pure ASCII icons -- guaranteed identical width on every monospace font, on every OS.
# no more unicode glyphs in box-drawn content: this is what was breaking alignment on
# Darwin's own machine (different fallback font than the one this was tested against).
whoami_groups = [
 [
  '*  Computer Engineer',
  '>  Into agentic programming — building with AI, not just using it',
  '-  Full-stack + IT support + networking, all in one',
  '^  Eternal student — always hungry for more to learn',
  '=  Hardware enthusiast at heart',
  '+  Here purely for the love of it — not exactly job hunting',
 ],
 [
  '~  I live in the terminal — and in the windows too (CachyOS main, though)',
  '<  Clauding my way forward, step by step.',
  '#  "Everything that lives is designed to end"... meanwhile, I leave proof',
  '   of my existence on my passport ↓',
 ],
]
whoami_box = box('whoami.txt', whoami_groups)

discord_url = ('https://lanyard.cnrad.dev/api/780932598922084384'
               '?theme=dark&bg=000000&borderRadius=18px&animated=true'
               '&idleMessage=bored%2C+for+now&showDisplayName=true')


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

![typing](assets/typing_dark.png#gh-dark-mode-only)
![typing](assets/typing_light.png#gh-light-mode-only)

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

<table align="center"><tr>
<td><img src="assets/section2_photos_v2.gif" width="180"/></td>
<td valign="top">

**channel-3** &nbsp; <code>soon</code><br>
NES emulator, browser-based — WebGL CRT, netplay

**kintsugi** &nbsp; <code>wip</code><br>
Go TUI — Windows LTSB/LTSC/Legacy ISOs, DISM internals

</td>
</tr></table>

<!-- TODO: swap in real repo link + final name once Channel 3 is published -->
<!-- TODO: add real repo link once Kintsugi has a demoable run -->

{sep()}

<p align="center">∴ off the clock: games, music, and a terminal that never quite closes — full taste below ↓</p>

<!-- three separate tables, not one colspan'd table -- a colspan cell can
     never render narrower than the columns beneath it, so as long as
     passport/discord shared a table with steam+spotify they were stuck at
     >= steam+spotify's combined width (554px) no matter what width= they
     were given. Splitting them out lets each size to its own content, no
     colspan involved anywhere, so still no dead space for GitHub to border. -->
<table align="center"><tr><td align="center"><a href="https://passportdex.com/dauin"><img src="assets/passport_card.png" width="260"/></a></td></tr></table>

<table align="center"><tr>
<td align="center"><a href="https://steamcommunity.com/id/dauin"><img src="assets/steam_card.png" width="250"/></a></td>
<td align="center"><a href="https://open.spotify.com/user/31aluwrafhtrzpee4pqzyodbvusm"><img src="assets/spotify_card.png" width="250"/></a></td>
</tr></table>

<table align="center"><tr><td align="center"><a href="https://discord.com/users/780932598922084384"><img src="{discord_url}" width="260" alt="discord"/></a></td></tr></table>

<!-- steam_card.png and spotify_card.png are rebuilt every few hours by
     .github/workflows/update-widgets.yml (scripts/build_steam_card.py and
     scripts/build_spotify_card.py) -- never hand-edited. -->

{sep()}

<p align="center"><sub>◇ art by <a href="https://x.com/inoitoh">@inoitoh</a> on twt</sub></p>

<!-- TODO: replace static passport card with a live embed once passportdex offers one -->
<!-- TODO: stats section (WakaTime / github-readme-stats), once decided -->
'''

with open('README.md', 'w', encoding='utf-8') as f:
    f.write(readme)
print('written, whoami box width:', len(whoami_box.split(chr(10))[0]))
