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

banner = pyfiglet.figlet_format('DAUIN', font='digital').rstrip('\n')

whoami_lines = [
 '▸ Computer Engineer',
 '→ Into agentic programming — building with AI, not just using it',
 '▪ Full-stack + IT support + networking, all in one',
 '▴ Eternal student — always hungry for more to learn',
 '≡ Hardware enthusiast at heart',
 '► Available for freelance & remote work',
 '○ I live in the terminal — and in the windows too (CachyOS main, though)',
 '» Clauding my way forward, step by step.',
 '● "Everything that lives is designed to end"... meanwhile, I leave proof',
 '   of my existence on my passport ↓',
]
whoami_box = box('whoami.txt', whoami_lines)

projects_lines = [
 'channel-3/   NES emulator, browser-based — WebGL CRT, netplay.  [soon]',
 'kintsugi/    Go TUI, Windows LTS ISOs — DISM internals.         [wip]',
]
projects_box = box('projects.log', projects_lines)

contact_lines = ['Best way to reach me →']
contact_box = box('contact.txt', contact_lines)

readme = f'''<p align="center">

```
{banner}
```

</p>

```
$ chafa avatar.jpg
```

<p align="center">
<img src="assets/profile_pic_circular.png" width="180" />
</p>

```
$ ls
whoami.txt  projects.log  contact.txt

$ cat whoami.txt
{whoami_box}
```

<table align="center"><tr><td align="center">
<a href="https://passportdex.com/dauin"><b>→ full passport here</b></a>
</td></tr></table>

```
$ cat projects.log
{projects_box}
```

<!-- TODO: swap in real repo link + final name once Channel 3 is published -->
<!-- TODO: add real repo link once Kintsugi has a demoable run -->

```
$ cat contact.txt
{contact_box}
```

<table align="center"><tr><td align="center">
<a href="https://github.com/dau-in"><b>→ github.com/dau-in</b></a>
</td></tr></table>

<p align="center"><sub>○ art by <a href="https://twitter.com/inoitoh">@inoitoh</a> on twt</sub></p>

<!-- TODO: stats section (WakaTime / github-readme-stats), once decided -->
'''

with open('README.md', 'w', encoding='utf-8') as f:
    f.write(readme)
print('written, whoami box width:', len(whoami_box.split(chr(10))[0]))
