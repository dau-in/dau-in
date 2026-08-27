"""
Refreshes scripts/language_icon_slugs.json: maps GitHub language names (the
same keys as scripts/language_colors.json) to a devicon slug, wherever
devicon has a matching icon. Devicon (devicons/devicon) is used instead of
Simple Icons because it's built specifically for programming
languages/tools and actually covers ones Simple Icons is missing entirely
-- Java, C#, and PowerShell all have no Simple Icons entry at all, and
those are squarely in what Darwin's repos will show.

Deliberately not exhaustive: only ~90 of GitHub's 692 recognized languages
get a mapped icon here (whatever devicon happens to also cover, matched by
name or explicit override below for known mismatches like "C++" ->
"cplusplus"). That's fine -- build_last_commit_card.py falls back to a
plain colored dot for anything unmapped, so an obscure language never
breaks the render, it just doesn't get a logo. No point pre-cataloging
icons for languages that will probably never show up in a "latest commit"
card anyway.

Re-run this occasionally (same cadence as build_language_colors.py) to
pick up devicon additions.
"""
import json
import re
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
DEVICON_URL = 'https://raw.githubusercontent.com/devicons/devicon/master/devicon.json'

# GitHub language name -> devicon slug, for names that don't normalize-match
# a devicon entry automatically. `None` means "known to have no good devicon
# icon, don't bother trying" (e.g. Batchfile, Assembly, Makefile -- nothing
# in devicon represents these well).
OVERRIDES = {
    'C++': 'cplusplus', 'C#': 'csharp', 'F#': 'fsharp', 'Objective-C': 'objectivec',
    'Objective-C++': 'objectivecpp', 'Shell': 'bash', 'HTML': 'html5', 'CSS': 'css3',
    'Vim Script': 'vim', 'Jupyter Notebook': 'jupyter', 'Dockerfile': 'docker',
    'PowerShell': 'powershell', 'Markdown': 'markdown', 'YAML': 'yaml', 'TeX': 'latex',
    'Vue': 'vuejs', 'Emacs Lisp': 'emacs', 'Common Lisp': 'lisp', 'Batchfile': None,
    'Assembly': None, 'Makefile': None, 'CMake': 'cmake', 'Groovy': 'groovy',
    'Perl': 'perl', 'Scala': 'scala', 'Elixir': 'elixir', 'Erlang': 'erlang',
    'Haskell': 'haskell', 'Clojure': 'clojurescript', 'Dart': 'dart', 'R': 'r',
    'Julia': 'julia', 'MATLAB': 'matlab', 'Nim': 'nim', 'Zig': 'zig', 'Crystal': 'crystal',
    'OCaml': 'ocaml', 'Elm': 'elm', 'Solidity': 'solidity', 'GDScript': 'godot',
}


def normalize(name):
    return re.sub(r'[^a-z0-9]', '', name.lower())


def main():
    with urllib.request.urlopen(DEVICON_URL, timeout=15) as r:
        devicon = json.loads(r.read())

    by_normalized_name = {}
    for entry in devicon:
        by_normalized_name.setdefault(normalize(entry['name']), entry['name'])
        for alt in entry.get('altnames', []):
            by_normalized_name.setdefault(normalize(alt), entry['name'])

    colors_path = HERE / 'language_colors.json'
    github_languages = json.loads(colors_path.read_text(encoding='utf-8'))

    mapping = {}
    for name in github_languages:
        if name in OVERRIDES:
            if OVERRIDES[name]:
                mapping[name] = OVERRIDES[name]
            continue
        slug = by_normalized_name.get(normalize(name))
        if slug:
            mapping[name] = slug

    out_path = HERE / 'language_icon_slugs.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(dict(sorted(mapping.items())), f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write('\n')
    print('written', out_path, '--', len(mapping), 'of', len(github_languages), 'languages mapped')


if __name__ == '__main__':
    main()
