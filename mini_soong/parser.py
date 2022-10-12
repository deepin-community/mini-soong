#!/usr/bin/python3
# Soong parser
#
# Based on an implementation of a simple JSON parser shipped with pyparsing
#
# Copyright 2006, 2007, 2016 Paul McGuire
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

import pyparsing as pp
from pyparsing import pyparsing_common as ppc
from typing import Mapping, Sequence
from .model import Assignment, Module

def make_keyword(kwd_str, kwd_value):
    return pp.Keyword(kwd_str).setParseAction(pp.replaceWith(kwd_value))

TRUE = make_keyword("true", True)
FALSE = make_keyword("false", False)
NULL = make_keyword("null", None)

LBRACK, RBRACK, LBRACE, RBRACE, COLON, EQUALS, COMMA, PLUS = map(pp.Suppress, "[]{}:=,+")

quotedString = pp.quotedString().setParseAction(pp.removeQuotes)
number = ppc.integer()

def add_things(tokens):
    return [tokens[0] + tokens[1]]

numberExp = (number + PLUS + number).setParseAction(add_things)

bracedMap = pp.Forward().setName("dictionary")
singleValue = pp.Forward()
listElements = pp.delimitedList(quotedString) + pp.Optional(COMMA)
stringList = pp.Group(LBRACK + pp.Optional(listElements, []) + RBRACK)

variables = dict()

def set_variable(tokens):
    global variables
    variable, value = tokens[0]
    variables[variable] = value
    return []

def resolve_var(tokens):
    global variables
    variable, = tokens[0]
    return [variables[variable]]

def add_vars(tokens):
    global variables
    left, right = tokens[0]
    return [variables[left] + variables[right]]

variableReference = pp.Group(ppc.identifier).setParseAction(resolve_var)

variableExp = pp.Group(ppc.identifier + PLUS + ppc.identifier).setParseAction(add_vars)

stringListExp = (stringList + PLUS + stringList).setParseAction(add_things)

singleValue << (
    quotedString | numberExp | number | pp.Group(bracedMap) | TRUE | FALSE | NULL | variableExp | variableReference | stringListExp | stringList
)
singleValue.setName("value")


memberDef = pp.Group((quotedString | ppc.identifier) + COLON + singleValue)
mapMembers = pp.delimitedList(memberDef) + pp.Optional(COMMA)
mapMembers.setName("dictionary members")
bracedMap << pp.Dict(LBRACE + pp.Optional(mapMembers) + RBRACE)

comment = pp.cppStyleComment

soongAssignment = pp.Group(ppc.identifier + EQUALS + singleValue)
soongAssignment.setParseAction(set_variable)
soongModule = pp.Group(ppc.identifier + pp.Group(bracedMap)).setParseAction(Module)
soongStatement = soongAssignment | soongModule
soong = soongStatement[...]
soong.ignore(comment)
