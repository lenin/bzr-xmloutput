#!/usr/bin/env python
# Copyright (C) 2007-2009 Guillermo Gonzalez
#
# The code taken from bzrlib is under: Copyright (C) 2005-2007 Canonical Ltd
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA
#
# Contributors:
#               Martin Albisetti

"""
This plugin adds an option (--xml) to log and provides an xml version of some builtin commands.

A xmlrpc service it's also provided, in order to keep bzr loaded in memory and
avoid the startup overhead.

(most of this is code was modified from bzrlib.cmd_status,
bzrlib.status, bzrlib.delta.TreeDelta.show and bzrlib.log.LongLogFormatter)
"""
import info
from bzrlib import (
    log,
    )

from bzrlib.commands import plugin_cmds

version_info = info.bzr_plugin_version
plugin_name = info.bzr_plugin_name

for cmd in [
    "xmlstatus",
    "xmlannotate",
    "xmlmissing",
    "xmlinfo",
    "xmlplugins",
    "xmlversion",
    "start_xmlrpc",
    "stop_xmlrpc",
    "xmllog",
    "xmlls"]:
    plugin_cmds.register_lazy(
        "cmd_%s" % cmd, [],
        "bzrlib.plugins.xmloutput.cmds")
log.log_formatter_registry.register_lazy('xml',
    "bzrlib.plugins.xmloutput.logxml", "XMLLogFormatter",
    'Detailed XML log format')


def load_tests(basic_tests, module, loader):
    try:
        testmod_names = [
            'tests',
            ]
        basic_tests.addTest(loader.loadTestsFromModuleNames(
                ["%s.%s" % (__name__, tmn) for tmn in testmod_names]))
        return basic_tests
    except ImportError:
        return None
