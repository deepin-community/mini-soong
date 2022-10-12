# A debhelper build system class for handling simple soong-based projects.
# It uses mini-soong, a Python re-implementation of a minimal Soong subset.
#
# Copyright: © 2008 Joey Hess
#            © 2008-2009 Modestas Vainius
#            © 2020 Andrej Shadura
#
# SPDX-License-Identifier: GPL-2+
#
# This program is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later
# version.

package Debian::Debhelper::Buildsystem::soong;

use strict;
use Debian::Debhelper::Dh_Lib qw(compat escape_shell clean_jobserver_makeflags gain_root_cmd dpkg_architecture_value);
use base 'Debian::Debhelper::Buildsystem::makefile';

sub DESCRIPTION {
	"mini-Soong"
}

sub clean {
	my $this=shift;
	if (-e $this->get_buildpath("soong.mk")) {
		$this->SUPER::clean(@_);
	}
	$this->doit_in_builddir('rm', '-f', 'soong.mk');
}

sub configure {
	my $this=shift;

	$this->mkdir_builddir();

	my $builddir = $this->get_builddir();

	my @opts;
	if (-e $this->get_buildpath("Android.bp")) {
		push @opts, "-o";
		push @opts, "soong.mk";
	}
	$this->doit_in_builddir("mini-soong", @opts, @_);
}

sub do_make {
	my $this=shift;

	# Avoid possible warnings about unavailable jobserver,
	# and force make to start a new jobserver.
	clean_jobserver_makeflags();

	my @opts;
	push @opts, "-f";
	push @opts, "soong.mk";
	my $prefix = "/usr";
	push @opts, "prefix=${prefix}";
	push @opts, "mandir=${prefix}/share/man";
	push @opts, "infodir=${prefix}/share/info";
	push @opts, "sysconfdir=/etc";
	my $multiarch=dpkg_architecture_value("DEB_HOST_MULTIARCH");
	if (defined $multiarch) {
		push @opts, "libdir=${prefix}/lib/$multiarch";
		push @opts, "libexecdir=${prefix}/lib/$multiarch" if compat(11);
	}
	else {
		push @opts, "libexecdir=${prefix}/lib" if compat(11);
	}

	my @root_cmd;
	if (exists($this->{_run_make_as_root}) and $this->{_run_make_as_root}) {
		@root_cmd = gain_root_cmd();
	}
	$this->doit_in_builddir(@root_cmd, $this->{makecmd}, @opts, @_);
}

sub exists_make_target {
	my $this=shift;
	return $this->SUPER::exists_make_target(@_, "-f", "soong.mk");
}

sub check_auto_buildable {
	my $this=shift;
	my ($step)=@_;

	return 0 unless -e $this->get_sourcepath("Android.bp");
	return 1;
}

sub new {
	my $class=shift;
	my $this=$class->SUPER::new(@_);
	$this->{makecmd} = "make";
	return $this;
}

1
