#!/usr/bin/env python3
"""Check and build this extension from its pinned public grammar."""
# SPDX-License-Identifier: Apache-2.0
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tomllib

HERE = Path(__file__).resolve().parent


def run(*args, cwd=None, capture=False):
    return subprocess.run([str(a) for a in args], cwd=cwd, check=True,
                          capture_output=capture, text=True)


def tree_sitter():
    """Return a runnable tree-sitter CLI, skipping broken shims on PATH."""
    candidates = [shutil.which('tree-sitter')]
    homebrew = '/opt/homebrew/bin/tree-sitter'
    if sys.platform == 'darwin' and Path(homebrew).is_file():
        candidates.append(homebrew)
    for candidate in candidates:
        if not candidate:
            continue
        try:
            if subprocess.run([candidate, '--version'], capture_output=True).returncode == 0:
                return candidate
        except OSError:
            pass
    raise SystemExit('A runnable tree-sitter CLI is required')


def grammar_source():
    grammar = tomllib.loads((HERE / 'extension.toml').read_text())['grammars']['pooka']
    cached = HERE / '.build/grammar-source'
    if not (cached / '.git').is_dir():
        cached.parent.mkdir(exist_ok=True)
        run('git', 'clone', '--filter=blob:none', grammar['repository'], cached)
    head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=cached, capture_output=True, text=True)
    if head.returncode or head.stdout.strip() != grammar['rev'] or not (cached / 'src/parser.c').is_file():
        run('git', 'fetch', '--depth', '1', 'origin', grammar['rev'], cwd=cached)
    run('git', 'checkout', '--detach', grammar['rev'], cwd=cached)
    if not (cached / 'src' / 'parser.c').is_file():
        raise SystemExit('The pinned grammar checkout has no generated parser')
    return cached


def check(grammar):
    config = tomllib.loads((HERE / 'languages/pooka/config.toml').read_text())
    assert config['grammar'] == 'pooka'
    assert 'pooka' in config['path_suffixes']
    icons = json.loads((HERE / 'icon_themes/pooka.json').read_text())
    for theme in icons['themes']:
        for icon in theme['file_icons'].values():
            if isinstance(icon, dict) and icon.get('path'):
                assert (HERE / icon['path']).is_file(), icon
    sample = HERE / 'tests/sample.spec.pooka'
    cli = tree_sitter()
    parsed = run(cli, 'parse', sample, cwd=grammar, capture=True)
    if 'ERROR' in parsed.stdout or 'MISSING' in parsed.stdout:
        raise SystemExit(parsed.stdout)
    for query in sorted((HERE / 'languages/pooka').glob('*.scm')):
        run(cli, 'query', query, sample, cwd=grammar, capture=True)
    print('Language configuration, icons, sample and all four queries checked.')


def zed_data():
    if sys.platform == 'darwin':
        return Path.home() / 'Library/Application Support/Zed'
    if sys.platform == 'win32':
        return Path(os.environ['LOCALAPPDATA']) / 'Zed'
    return Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share')) / 'zed'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='validate without building WebAssembly')
    args = parser.parse_args()
    grammar = grammar_source()
    check(grammar)
    if args.check:
        return
    sdk = os.environ.get('WASI_SDK_PATH')
    clang = Path(sdk) / 'bin/clang' if sdk else zed_data() / 'extensions/build/wasi-sdk/bin/clang'
    if not clang.is_file():
        raise SystemExit('Set WASI_SDK_PATH to a WASI SDK, or let Zed install its grammar build tools first.')
    stage = HERE / 'dist'
    # Only replace generated build output owned by this script.
    if stage.exists():
        shutil.rmtree(stage)
    (stage / 'grammars').mkdir(parents=True)
    run(clang, '-fPIC', '-shared', '-Os', '-Wl,--export=tree_sitter_pooka',
        '-Wl,--max-memory=4294967296', '-I', grammar / 'src', grammar / 'src/parser.c',
        '-o', stage / 'grammars/pooka.wasm')
    for name in ['languages', 'icon_themes', 'icons']:
        shutil.copytree(HERE / name, stage / name)
    for name in ['extension.toml', 'LICENSE', 'README.md']:
        shutil.copy2(HERE / name, stage / name)
    (HERE / 'grammars').mkdir(exist_ok=True)
    shutil.copy2(stage / 'grammars/pooka.wasm', HERE / 'grammars/pooka.wasm')
    print('Extension ready in dist/. Install this directory as a Zed dev extension.')


if __name__ == '__main__':
    main()
