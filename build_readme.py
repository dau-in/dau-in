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
    # real <hr> elements are always 100% of the container width -- unlike a
    # fixed-length dash string, they can't overflow/wrap on narrow (mobile) viewports.
    return '<hr>\n\n<p align="center">[ * ]</p>\n\n<hr>'

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
<td><img src="assets/section2_photos.gif" width="150"/></td>
<td>

| project | description | status |
|---|---|---|
| **channel-3** | NES emulator, browser-based — WebGL CRT, netplay | soon |
| **kintsugi** | Go TUI — Windows LTSB/LTSC/Legacy ISOs, DISM internals | wip |

</td>
</tr></table>

<!-- TODO: swap in real repo link + final name once Channel 3 is published -->
<!-- TODO: add real repo link once Kintsugi has a demoable run -->

{sep()}

<p align="center">∴ off the clock: games, music, and a terminal that never quite closes — full taste below ↓</p>

<p align="center">
<a href="https://passportdex.com/dauin"><img src="assets/passport_card.png" width="380"/></a>
</p>

{sep()}

<p align="center"><sub>◇ art by <a href="https://x.com/inoitoh">@inoitoh</a> on twt</sub></p>

<!-- TODO: replace static passport card with a live embed once passportdex offers one -->
<!-- TODO: Discord/Spotify/Steam widgets, once decided how -->
<!-- TODO: stats section (WakaTime / github-readme-stats), once decided -->
'''

with open('README.md', 'w', encoding='utf-8') as f:
    f.write(readme)
print('written, whoami box width:', len(whoami_box.split(chr(10))[0]))
