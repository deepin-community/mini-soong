#!/usr/bin/python3
# Soong parsed model
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

from dataclasses import dataclass

all_modules = list()
all_targets = list()

defaults = dict()

current_recipe = dict()

@dataclass
class Assignment:
    # NOT currently used
    variable: str
    value: object

    def __init__(self, tokens):
        self.variable = tokens[0][0]
        self.value = tokens[0][1]

    def run(self):
        global variables
        variables[self.variable] = self.value

@dataclass
class Module:
    name: str
    arguments: dict

    def __init__(self, tokens):
        self.name = tokens[0][0]
        self.arguments = tokens[0][1].asDict()

    def run(self):
        from . import builders
        if self.name in builders.methods:
            builders.methods[self.name](**self.arguments)
        else:
            import sys
            print(f"WARNING: {self.name} not yet supported", file=sys.stderr)
