"""
Refreshes scripts/language_colors.json from GitHub linguist's own
languages.yml -- the canonical source GitHub itself uses for the language
color dots/bars shown on repo pages. Re-run this occasionally to pick up
newly-added languages or corrected colors; not on any schedule, since
this data changes rarely.

No YAML library dependency: linguist's languages.yml has a flat structure
(unindented "LanguageName:" keys, each followed by indented fields) simple
enough to pull `color: "#hex"` out of with a plain regex instead of adding
pyyaml just for this one script.
"""
import json
import re
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
SOURCE_URL = 'https://raw.githubusercontent.com/github-linguist/linguist/main/lib/linguist/languages.yml'


def main():
    with urllib.request.urlopen(SOURCE_URL, timeout=15) as r:
        text = r.read().decode('utf-8')

    colors = {}
    current_name = None
    for line in text.split('\n'):
        if line and not line[0].isspace() and not line.startswith('#') and line.rstrip().endswith(':'):
            current_name = line.rstrip()[:-1].strip('"')
        elif current_name:
            m = re.match(r'^\s+color:\s*"?(#[0-9a-fA-F]{6})"?', line)
            if m:
                colors[current_name] = m.group(1)

    out_path = HERE / 'language_colors.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(dict(sorted(colors.items())), f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write('\n')
    print('written', out_path, '--', len(colors), 'languages')


if __name__ == '__main__':
    main()
