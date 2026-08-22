# -*- coding: utf-8 -*-
import pyfiglet

def box(title, lines):
    width = max([len(l) for l in lines] + [len(title) + 4]) + 2
    top = '┌─ ' + title + ' ' + '─' * (width - len(title) - 4) + '┐'
    bot = '└' + '─' * (width - 2) + '┘'
    body = []
    for l in lines:
        pad = width - 2 - len(l)
        body.append('│ ' + l + ' ' * max(pad - 1, 0) + '│')
    return '\n'.join([top] + body + [bot])

def strip_blank_lines(s):
    lines = s.split('\n')
    while lines and lines[0].strip() == '':
        lines.pop(0)
    while lines and lines[-1].strip() == '':
        lines.pop()
    return '\n'.join(lines)

def sep(width=60):
    dash = (width - 3) // 2
    return '▪' + '─' * (dash - 1) + '[ • ]' + '─' * (dash - 1) + '▪'

name_banner = strip_blank_lines(pyfiglet.figlet_format('DAUIN', font='thin'))

typing_url = ('https://readme-typing-svg.demolab.com?font=Cutive+Mono&pause=1200'
              '&color=8B949E&center=true&vCenter=true&width=380&height=30'
              '&lines=still+typing+this+myself%2C+mostly;'
              'still+figuring+it+out;'
              'still+here%2C+still+terminal-pilled')

# pure ASCII icons -- guaranteed identical width on every monospace font, on every OS.
# no more unicode glyphs in box-drawn content: this is what was breaking alignment on
# Darwin's own machine (different fallback font than the one this was tested against).
whoami_lines = [
 '*  Computer Engineer',
 '>  Into agentic programming — building with AI, not just using it',
 '-  Full-stack + IT support + networking, all in one',
 '^  Eternal student — always hungry for more to learn',
 '=  Hardware enthusiast at heart',
 '+  Available for freelance & remote work',
 '~  I live in the terminal — and in the windows too (CachyOS main, though)',
 '<  Clauding my way forward, step by step.',
 '#  "Everything that lives is designed to end"... meanwhile, I leave proof',
 '   of my existence on my passport ↓',
]
whoami_box = box('whoami.txt', whoami_lines)

readme = f'''<table><tr>
<td><img width="150" src="assets/section1_photos.gif"/></td>
<td valign="top">

<img src="{typing_url}" width="380" alt="typing"/>

```
{name_banner}
```

</td>
</tr></table>

```
{whoami_box}
```

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

<p align="center">∴ interests: games, music, terminal life</p>

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
