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

typing_url = ('https://readme-typing-svg.demolab.com?font=Cutive+Mono&pause=1200'
              '&color=8B949E&center=true&vCenter=true&width=380&height=30'
              '&lines=still+typing+this+myself%2C+mostly;'
              'still+figuring+it+out;'
              'still+here%2C+still+terminal-pilled')

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
  '+  Available for freelance & remote work',
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

# Lanyard's widget has no logo/brand mark of its own (unlike the steam/spotify
# cards, which are ours and show their own in-card branding) -- add one below it,
# same small-muted-caption style, so it's identifiable as Discord at a glance.
discord_logo = ('<svg width="13" height="13" viewBox="0 0 24 24" '
                 'style="vertical-align:-2px;margin-right:5px;" fill="#a7a0a7">'
                 '<path d="M20.317 4.3698a19.7913 19.7913 0 00-4.8851-1.5152.0741.0741 0 00-.0785.0371c-.211.3753-.4447.8648-.6083 1.2495-1.8447-.2762-3.68-.2762-5.4868 0-.1636-.3933-.4058-.8742-.6177-1.2495a.077.077 0 00-.0785-.037 19.7363 19.7363 0 00-4.8852 1.515.0699.0699 0 00-.0321.0277C.5334 9.0458-.319 13.5799.0992 18.0578a.0824.0824 0 00.0312.0561c2.0528 1.5076 4.0413 2.4228 5.9929 3.0294a.0777.0777 0 00.0842-.0276c.4616-.6304.8731-1.2952 1.226-1.9942a.076.076 0 00-.0416-.1057c-.6528-.2476-1.2743-.5495-1.8722-.8923a.077.077 0 01-.0076-.1277c.1258-.0943.2517-.1923.3718-.2914a.0743.0743 0 01.0776-.0105c3.9278 1.7933 8.18 1.7933 12.0614 0a.0739.0739 0 01.0785.0095c.1202.099.246.1981.3728.2924a.077.077 0 01-.0066.1276 12.2986 12.2986 0 01-1.873.8914.0766.0766 0 00-.0407.1067c.3604.698.7719 1.3628 1.225 1.9932a.076.076 0 00.0842.0286c1.961-.6067 3.9495-1.5219 6.0023-3.0293a.077.077 0 00.0313-.0552c.5004-5.177-.8382-9.6739-3.5485-13.6604a.061.061 0 00-.0312-.0286zM8.02 15.3312c-1.1825 0-2.1569-1.0857-2.1569-2.419 0-1.3332.9555-2.4189 2.157-2.4189 1.2108 0 2.1757 1.0952 2.1568 2.419 0 1.3332-.9555 2.4189-2.1569 2.4189zm7.9748 0c-1.1825 0-2.1569-1.0857-2.1569-2.419 0-1.3332.9554-2.4189 2.1569-2.4189 1.2108 0 2.1757 1.0952 2.1568 2.419 0 1.3332-.946 2.4189-2.1568 2.4189Z"/>'
                 '</svg>')

readme = f'''<p align="center"><img src="{typing_url}" width="380" alt="typing"/></p>

<table align="center"><tr>
<td><img width="150" src="assets/section1_photos.gif"/></td>
<td align="center" valign="middle">

```

{name_banner}

```

</td>
</tr></table>

<div align="center">

```
{whoami_box}
```

</div>

{sep()}

<table align="center"><tr>
<td><img src="assets/section2_photos_v2.gif" width="150"/></td>
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

<!-- single flat table, no nesting -- a table-within-a-table is what broke images
     on the GitHub mobile app before (see commit 8325169); colspan avoids that
     entirely while still mixing full-width rows with a 2-column row. -->
<table align="center">

<tr><td colspan="2" align="center">

<p align="center"><a href="https://passportdex.com/dauin"><img src="assets/passport_card.png" width="380"/></a></p>

</td></tr>

<tr>
<td align="center"><a href="https://steamcommunity.com/id/dauin"><img src="assets/steam_card.png" width="300"/></a></td>
<td align="center"><a href="https://open.spotify.com/user/31aluwrafhtrzpee4pqzyodbvusm"><img src="assets/spotify_card.png" width="300"/></a></td>
</tr>

<tr><td colspan="2" align="center">

<p align="center"><a href="https://discord.com/users/780932598922084384"><img src="{discord_url}" width="380" alt="discord"/></a></p>
<p align="center"><sub>{discord_logo}discord.com/users/780932598922084384</sub></p>

</td></tr>

</table>

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
