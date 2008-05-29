#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Copyright (C) 2007 Guillermo Gonzalez
#
# The code taken from bzrlib is under: Copyright (C) 2005, 2006, 2007 Canonical Ltd
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


from xmlrpclib import Server, Error
import socket

server = Server("http://localhost:11111")

try:
    import sys
    args = ['bzr']
    [args.append(arg) for arg in sys.argv[1:-1]]
    exit_val, out, err = server.run_bzr(args, sys.argv[-1])
    sys.stdout.write(out)
    sys.stderr.write(str(err))
    sys.exit(exit_val)
except Error, v:
    raise v
    sys.stderr.write(v.__repr__())

