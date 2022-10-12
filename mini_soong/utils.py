from typing import Mapping, Sequence

def mergedefaults(a, b):
    for k, v in b.items():
        if k in a:
            if isinstance(v, Mapping):
                new = v.copy()
                new.update(a[k])
                a[k] = new
            elif isinstance(v, Sequence):
                a[k] = v + a[k]
        else:
            a[k] = v
    return a

def add_dicts(a, b):
    # currently unused
    new = {}
    for k, v in b.items():
        if k in a:
            # the docco isn’t clear on this but it’s better to overwrite strings
            if isinstance(v, str):
                new[k] = b[k]
            elif isinstance(v, Mapping):
                new[k] = add_dicts(a[k], b[k])
            elif isinstance(v, Sequence):
                new[k] = a[k] + b[k]
        else:
            new[k] = v
    return new

def print_vars(target, kv, names):
    for name in names:
        if name in kv:
            print(f"{target}_{name.upper():<8} = {' '.join(kv[name])}")

import re
from functools import lru_cache
from pathlib import Path
from debian.deb822 import Deb822
from debian.changelog import Changelog
from debian.debian_support import Version

@lru_cache(maxsize=None)
def deb_version():
    changelog = Path('debian/changelog')
    if changelog.exists():
        try:
            with changelog.open() as f:
                ch = Changelog(f, max_blocks=1)
                return ch.version
        except:
            pass
    return None


def library_pkgs():
    _, _, lib_pkgs = parse_control()
    return lib_pkgs

def mangle_lib(lib: str) -> str:
    # add a dash if there is a number before .so
    lib = re.sub(r'([0-9])\.so$', r'\1-', lib)
    # drop .so
    lib = re.sub(r'\.so$', '', lib)
    return lib.replace('_', '-').lower()

def match_libs(libs):
    pkg_ver = deb_version()
    if pkg_ver:
        pkg_ver = '.'.join(pkg_ver.upstream_version.split('.')[:3])
    lib_pkgs = sorted(library_pkgs())
    mangled_libs = [(lib, mangle_lib(lib)) for lib in sorted(libs)]
    for lib, mangled_lib in mangled_libs:
        for pkg in lib_pkgs:
            if pkg.startswith(mangled_lib):
                rest = pkg.replace(mangled_lib, '', 1)
                if rest.isdecimal():
                    yield (lib, rest, pkg_ver if pkg_ver.startswith(rest) else rest)
                    break

@lru_cache(maxsize=None)
def parse_control():
    control = Path('debian/control')
    if control.exists():
        try:
            with control.open() as f:
                bin_pkgs = [p['Package'] for p in Deb822.iter_paragraphs(f) if 'Package' in p]
                dev_pkgs = [p for p in bin_pkgs if p.startswith('lib') and p.endswith('-dev')]
                lib_pkgs = [p for p in bin_pkgs if p.startswith('lib') and not p.endswith('-dev')]
                return bin_pkgs, dev_pkgs, lib_pkgs
        except:
            pass
    return [], [], []
