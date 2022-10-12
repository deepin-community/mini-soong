Mini-Soong
==========

Mini-Soong is a minimalist and incomplete reimplementation of Soong, the
Android build system. It is intended to simplify the packaging of parts
of Android for Debian. It is not intended to be a complete replacement
for Soong.

What is Soong?
==============

The Soong build system was introduced in Android 7.0 to replace Make
which at Android's scale became slow, error prone, unscalable, and
difficult to test. It leverages the Kati GNU Make clone tool and Ninja
build system component to speed up builds of Android.

To learn more about Soong, see <https://source.android.com/setup/build>.

What does Mini-Soong support?
=============================

At the moment, Mini-Soong accepts almost any Soong Blueprint file,
but only supports a minimal set of features Soong provides.  The only
feature of the Blueprint format not supported is the addition of maps.

Feature-wise, only flat Soong files for projects in C, C++ and assembler
work. No recursive builds, other programming languages, YACC support,
rule generation or any of the advanced features.

Mini-Soong generates a Makefile with three targets: `clean`, `build`,
`install`. The `install` target only installs binaries and shared
libraries. Static libraries and headers are *not* installed. `DESTDIR`,
`prefix` and `libdir` are taken into account. When ran on a Debian system
with `dpkg-dev` installed, the system build flags are automatically
picked up.
