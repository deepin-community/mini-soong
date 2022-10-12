# Soong to Makefile translator
#
# Copyright 2020 Andrej Shadura
#
# SPDX-License-Identifier: MIT
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from .parser import soong
from .model import defaults, all_targets, all_modules, current_recipe, Module
from .utils import mergedefaults, print_vars
from .builders import flag_defaults, extra_targets
import argparse
import os
from pathlib import Path

def run():
    import sys
    global all_modules, current_recipe

    parser = argparse.ArgumentParser(description='Convert Soong recipes to a Makefile')
    parser.add_argument('bp', metavar='RECIPES', type=str, default='**/Android.bp', nargs='?', help='pattern used to find recipes')
    parser.add_argument('poutput', metavar='OUTPUT', type=str, nargs='?', help='where to write the Makefile (default: stdout)')
    parser.add_argument('--output', '-o', metavar='OUTPUT', type=str, help='where to write the Makefile (default: stdout)')
    args = parser.parse_args()

    bp = args.bp
    output = args.poutput or args.output

    if output:
        sys.stdout = open(output, 'w')

    flag_defaults()
    all_modules.clear()

    # todo: allow chdir
    recipes = sorted([path for path in Path('.').glob(bp) if not path.parts[0].startswith('.')])
    for recipe in recipes:
        parsed = soong.parseString(recipe.read_text())
        all_modules += [r.arguments['name'] for r in parsed if isinstance(r, Module) and 'name' in r.arguments]

        current_recipe.update({
            'name': str(recipe),
            'dir': recipe.parents[0],
            'parsed': parsed
        })
        for r in parsed:
            r.run()

    print(f"build: {' '.join(all_targets)}")
    if all_targets:
        clean_targets = [f"clean-{target}" for target in all_targets]
        print(f"clean: {' '.join(clean_targets)}")
    else:
        print(f"clean:")
    extra_targets()
