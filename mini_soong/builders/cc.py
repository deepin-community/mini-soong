# Builders for C and C++
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


__all__ = [
    'cc_defaults',
    'cc_binary',
    'cc_binary_host',
    'cc_library',
    'cc_library_shared',
    'cc_library_host_shared',
    'cc_library_static',
    'cc_library_host_static',
    'cc_test',
    'cc_test_host',
    'cc_benchmark',
    'cc_benchmark_host',
]

from ..utils import mergedefaults, print_vars, match_libs
from ..model import defaults, all_targets, all_modules, current_recipe
from functools import lru_cache
from pathlib import Path
import os
import sh

dpkg_architecture = sh.Command('dpkg-architecture')

targets_binary = list()
targets_shlib = list()

flag_blacklist = ['-Werror', '-U_FORTIFY_SOURCE', '-m32', '-m64', '-Wno-#pragma-messages']

@lru_cache(maxsize=None)
def detect_arch():
    if 'DEB_HOST_ARCH' in os.environ:
        return os.environ['DEB_HOST_ARCH']
    else:
        return dpkg_architecture('-q', 'DEB_HOST_ARCH').rstrip()

def map_arch():
    arch = detect_arch()
    if arch == 'amd64':
        return 'x86_64'
    elif arch == 'i386':
        return 'x86'
    elif arch == 'arm64':
        return 'arm64'
    elif arch.startswith('arm'):
        return 'arm'
    elif arch.startswith('mips64'):
        return 'mips64'
    elif arch.startswith('mips'):
        return 'mips'
    return arch

def multilib():
    if map_arch().endswith('64'):
        return 'lib64'
    else:
        return 'lib32'

@lru_cache(maxsize=None)
def detect_multiarch():
    if 'DEB_HOST_MULTIARCH' in os.environ:
        return os.environ['DEB_HOST_MULTIARCH']
    else:
        return dpkg_architecture('-q', 'DEB_HOST_MULTIARCH').rstrip()

def collect_defaults(args):
    global defaults
    def_cxxflags = []
    def_cflags = []
    def_ldflags = []
    def_ldlibs = []
    def_srcs = []
    for default in args.get('defaults', []):
        if default in defaults:
            def_cxxflags += [f"$({default}_CXXFLAGS)"]
            def_cflags += [f"$({default}_CFLAGS)"]
            def_ldflags += [f"$({default}_LDFLAGS)"]
            def_ldlibs += [f"$({default}_LDLIBS)"]
            def_srcs += [f"$({default}_SRCS)"]
    arch_specific = args.get('arch', {}).get(map_arch(), {})
    mergedefaults(args, arch_specific)
    target_specific = args.get('target', {}).get('linux_glibc', {})
    mergedefaults(args, target_specific)
    multilib_specific = args.get('multilib', {}).get(multilib(), {})
    mergedefaults(args, multilib_specific)
    return def_cxxflags, def_cflags, def_ldflags, def_ldlibs, def_srcs

def filter_flags(flags):
    return [flag for flag in flags if flag not in flag_blacklist]

def relative_to(path: Path, fname: str) -> Path:
    if fname.startswith('/'):
        return Path(fname)
    else:
        return path / fname

def rel(fname: str) -> Path:
    return relative_to(current_recipe['dir'], fname)

def cc_defaults(**args):
    def_cxxflags, def_cflags, def_ldflags, def_ldlibs, def_srcs = collect_defaults(args)
    defaults[args['name']] = {k: v for k, v in args.items() if k != 'name'}
    local_include_dirs = args.get('local_include_dirs', [])
    cxxflags = filter_flags(def_cxxflags + args.get('cppflags', []) + [f"-I{inc}" for inc in local_include_dirs])
    cflags = filter_flags(def_cflags + args.get('cflags', []) + [f"-I{rel(inc)}" for inc in local_include_dirs])
    ldflags = filter_flags(def_ldflags + args.get('ldflags', []))
    ldlibs = def_ldlibs + [f"-l{lib[3:]}" for lib in args.get('shared_libs', [])]
    srcs = [(f"{rel(path)}" if not path.startswith('$') else path) for path in def_srcs + args.get('srcs', [])]
    print_vars(args['name'], locals(), ['cxxflags', 'cflags', 'ldflags', 'ldlibs', 'srcs'])
    print()

def cc_compile_link(args, binary: bool = True, shared: bool = False, variables: bool = True):
    print(f"# link {args['name']} {'shared' if shared else 'static'} library")

    def_cxxflags, def_cflags, def_ldflags, def_ldlibs, def_srcs = collect_defaults(args)
    local_include_dirs = args.get('local_include_dirs', [])
    if not binary:
        export_include_dirs = args.get('export_include_dirs', [])
        export_system_include_dirs = args.get('export_system_include_dirs', [])
        includes = [f"-I{rel(inc)}" for inc in export_include_dirs]
        system_includes = [f"-isystem {rel(inc)}" for inc in export_system_include_dirs]
    cxxflags = filter_flags(def_cxxflags + args.get('cppflags', []) + [f"-I{rel(inc)}" for inc in local_include_dirs])
    cflags = filter_flags(def_cflags + args.get('cflags', []) + [f"-I{rel(inc)}" for inc in local_include_dirs])

    if not binary:
        cxxflags += [f"$({args['name']}_INCLUDES)", f"$({args['name']}_SYSTEM_INCLUDES)"]
        cflags += [f"$({args['name']}_INCLUDES)", f"$({args['name']}_SYSTEM_INCLUDES)"]
    ldflags = filter_flags(def_ldflags + args.get('ldflags', []))
    shared_libs = args.get('shared_libs', [])
    if not binary:
        if shared and 'shared' in args:
            mergedefaults(args, args['shared'])
        elif not shared and 'static' in args:
            mergedefaults(args, args['static'])
    shared_libs += [lib for lib in args.get('static_libs', []) if lib not in all_modules]
    shared_libs += [lib for lib in args.get('whole_static_libs', []) if lib not in all_modules]
    ldlibs = def_ldlibs + [f"-l{lib[3:]}" for lib in shared_libs]
    shlibdeps = []

    multiarch_libdir = Path(f"/usr/lib/{detect_multiarch()}")
    multiarch_android_libdir = multiarch_libdir / "android"

    external_android_shlibs = [lib for lib in shared_libs if (lib not in all_modules) and (multiarch_android_libdir / f"{lib}.so").exists()]
    if external_android_shlibs:
        ldflags += [f"-L{multiarch_android_libdir}"]
    external_shlibs = external_android_shlibs + [lib for lib in shared_libs if (lib not in all_modules) and (multiarch_libdir / f"{lib}.so").exists()]

    for lib in shared_libs:
        cxxflags += [f"$({lib}_INCLUDES)", f"$({lib}_SYSTEM_INCLUDES)"]
        cflags += [f"$({lib}_INCLUDES)", f"$({lib}_SYSTEM_INCLUDES)"]
        if lib not in external_shlibs:
            shlibdeps += [f"{lib}.so"]

    if any(lib for lib in shared_libs if lib in all_modules):
        ldflags += ["-L."]

    static_libs = [f"{lib}.a" for lib in args.get('static_libs', []) if lib in all_modules]
    if 'whole_static_libs' in args:
        static_libs += ["-Wl,--whole-archive"]
        static_libs += [f"{lib}.a" for lib in args.get('whole_static_libs', []) if lib in all_modules]
        static_libs += ["-Wl,--no-whole-archive"]
    srcs = [(f"{rel(path)}" if not path.startswith('$') else path) for path in def_srcs + args.get('srcs', [])]
    if variables:
        print(f"{args['name']}_DIR        = {current_recipe['dir']}")
        if shared:
            matches = {lib: (major, ver) for lib, major, ver in match_libs([args['name']])}
            if args['name'] in matches:
                somajor, soversion = matches[args['name']]
                print(f"{args['name']}_soversion ?= {soversion}")
                print(f"{args['name']}_somajor    = $(basename $(basename $({args['name']}_soversion)))")
            else:
                print(f"{args['name']}_soversion ?= 0.0.0")
                print(f"{args['name']}_somajor    = $(basename $(basename $({args['name']}_soversion)))")
        print_vars(args['name'], locals(), ['cxxflags', 'cflags', 'ldflags', 'ldlibs', 'srcs'] + ['includes', 'system_includes'] if not binary else [])
        print()
    if not binary:
        suffix = f".so.$({args['name']}_soversion)" if shared else ".a"
        soname = f"{args['name']}{suffix}"
        target = soname
        shared_flag = f"-shared -Wl,-soname,{args['name']}.so.$({args['name']}_somajor)" if shared else ""
    else:
        target = args['name']
        shared_flag = ""
    if shared:
        print(f"{args['name']}.so: {target}")
    print(f"{target}: $({args['name']}_SRCS) {' '.join(shlibdeps)}")
    print("\t" + ' '.join([
        f"$(CC) $({args['name']}_SRCS) -o $@" if shared or binary else f"$(CC) $({args['name']}_SRCS) -c",
        ' '.join(static_libs),
        f"$(CPPFLAGS)",
        f"$(CFLAGS) $({args['name']}_CFLAGS)",
        f"$(CXXFLAGS) $({args['name']}_CXXFLAGS)" if have_cxx(srcs) else "",
        f"$(LDFLAGS) $({args['name']}_LDFLAGS) {shared_flag}" if shared or binary else "",
        "-lstdc++" if have_cxx(srcs) else "",
        f"$(LDLIBS) $({args['name']}_LDLIBS)" if shared or binary else "",
    ]))
    if shared:
        print(f"\tln -sf $@ $(@:.$({args['name']}_soversion)=.$({args['name']}_somajor))")
        print(f"\tln -sf $(@:.$({args['name']}_soversion)=.$({args['name']}_somajor)) $(@:.$({args['name']}_soversion)=)")
    if not shared and not binary:
        print(f"\tar rcs {soname} $(patsubst %,%.o,$(notdir $(basename $({args['name']}_SRCS))))")
        print(f"\trm $(patsubst %,%.o,$(notdir $(basename $({args['name']}_SRCS))))")
    all_targets.append(target)
    print()
    print(f"clean-{target}:")
    print(f"\trm -f {target}")
    if shared:
        print(f"\trm -f {args['name']}.so {args['name']}.so.$({args['name']}_somajor)")
        print()
        print(f"install-{target}: {target} install-{args['name']}-headers")
        print(f"\tinstall -m644 -D -t $(DESTDIR)$(libdir) $<")
        print(f"\tln -s $< $(DESTDIR)$(libdir)/$(<:.$({args['name']}_soversion)=.$({args['name']}_somajor))")
        print(f"\tln -s $(<:.$({args['name']}_soversion)=.$({args['name']}_somajor)) $(DESTDIR)$(libdir)/$(<:.$({args['name']}_soversion)=)")
        targets_shlib.append(target)
    elif binary:
        print()
        print(f"install-{target}: {target}")
        print(f"\tinstall -m755 -D -t $(DESTDIR)$(prefix)/bin $<")
        targets_binary.append(target)
    if shared and (export_include_dirs or export_system_include_dirs):
        print()
        print(f"install-{args['name']}-headers:")
        print(f"\tmkdir -p $(DESTDIR)$(prefix)/include/{args['name']}")
        for inc_dir in export_include_dirs + export_system_include_dirs:
            print(f"\tcp -R -t $(DESTDIR)$(prefix)/include/{args['name']} {inc_dir}/*")
    print()

def cc_binary(**args):
    cc_compile_link(args, binary = True, shared = False)

def cc_binary_host(**args):
    cc_compile_link(args, binary = True, shared = False)

def cc_library(**args):
    cc_compile_link(args, binary = False, shared = True)
    cc_compile_link(args, binary = False, shared = False, variables = False)

def cc_library_shared(**args):
    cc_compile_link(args, binary = False, shared = True)

def cc_library_host_shared(**args):
    cc_compile_link(args, binary = False, shared = True)

def cc_library_static(**args):
    cc_compile_link(args, binary = False, shared = False)

def cc_library_host_static(**args):
    cc_compile_link(args, binary = False, shared = False)

def cc_test(**args):
    pass

def cc_test_host(**args):
    pass

def cc_benchmark(**args):
    pass

def cc_benchmark_host(**args):
    pass

def have_cxx(files):
    return any(is_cxx(f) for f in files)

def is_cxx(filename):
    return (filename.endswith('.cc') or
            filename.endswith('.cxx') or
            filename.endswith('.cpp') or
            filename.endswith('.CPP') or
            filename.endswith('.c++') or
            filename.endswith('.cp') or
            filename.endswith('.C'))

def flag_defaults():
    print("DPKG_EXPORT_BUILDFLAGS = 1")
    print("-include /usr/share/dpkg/buildflags.mk\n")
    print("CXXFLAGS += " + ' '.join([
        "-D__STDC_FORMAT_MACROS",
        "-D__STDC_CONSTANT_MACROS",
        "-std=c++11",
    ]))
    print("CFLAGS += " + ' '.join([
        "-D_FILE_OFFSET_BITS=64",
        "-D_LARGEFILE_SOURCE=1",
        "-Wa,--noexecstack",
        "-fPIC",
        "-fcommon",
    ]))
    print("LDFLAGS += " + ' '.join([
        "-Wl,-z,noexecstack",
        "-Wl,--no-undefined-version",
        "-Wl,--as-needed",
    ]))
    print("LDLIBS += " + ' '.join([
        f'-l{lib}' for lib in [
            "c",
            "dl",
            "gcc",
            #"gcc_s",
            "m",
            #"ncurses",
            "pthread",
            #"resolv",
            "rt",
            "util",
        ]
    ]))
    print()

def extra_targets():
    targets = []
    if targets_binary:
        print(f"install-binaries: install-{' install-'.join(targets_binary)}")
        targets.append('install-binaries')

    if targets_shlib:
        print(f"install-shlibs: install-{' install-'.join(targets_shlib)}")
        targets.append('install-shlibs')

    return targets
