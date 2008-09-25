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
import os
import sys
from bzrlib import osutils

def setup_outf(encoding_type='replace'):
    """Return a file linked to stdout, which has proper encoding."""
    import codecs
    import bzrlib
    if encoding_type == 'exact':
        # force sys.stdout to be binary stream on win32
        if sys.platform == 'win32':
            fileno = getattr(sys.stdout, 'fileno', None)
            if fileno:
                import msvcrt
                msvcrt.setmode(fileno(), os.O_BINARY)
        outf = sys.stdout
        return

    output_encoding = osutils.get_terminal_encoding()

    outf = codecs.getwriter(output_encoding)(sys.stdout,
                    errors=encoding_type)
    outf.encoding = output_encoding
    return outf


def main(argv=[]): 
    server = Server("http://localhost:11111")
    try:
        args = ['bzr']
        [args.append(arg) for arg in argv[1:]]
        exit_val, out, err = server.run_bzr_command(args, os.getcwd())
        outf = setup_outf()
        outf.write(out.data.decode(osutils.get_terminal_encoding(), 'replace'))
        sys.stderr.write(err)
        outf.flush();
        sys.stderr.flush();
        sys.exit(exit_val)
    except Error, exc:
        sys.stderr.write(exc.__repr__())
        raise


if __name__ == '__main__':
    main(sys.argv)