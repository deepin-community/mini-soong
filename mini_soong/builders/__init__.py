import importlib
import pkgutil

builders = []
methods = {}

for _, name, _ in pkgutil.walk_packages(__path__):
    mod = importlib.import_module(f"{__name__}.{name}")
    builders.append(mod)
    for fn in mod.__dict__.get('__all__', []):
        methods[fn] = mod.__dict__[fn]

def flag_defaults():
    print(".PHONY: build install\n")
    print(".DEFAULT_GOAL := build\n")
    print("DESTDIR ?=")
    print("prefix ?= /usr")
    print("libdir ?= ${prefix}/lib\n")

    for builder in builders:
        if 'flag_defaults' in builder.__dict__:
            builder.flag_defaults()

def extra_targets():
    install_targets = []
    for builder in builders:
        if 'extra_targets' in builder.__dict__:
            install_targets += builder.extra_targets()

    print(f"install: {' '.join(install_targets)}")

