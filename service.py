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



from SimpleXMLRPCServer import SimpleXMLRPCServer
from xml_errors import XMLError
from bzrlib.lazy_import import lazy_import
lazy_import(globals(), """
import socket, sys
from cStringIO import StringIO 
import bzrlib
from bzrlib import commands
from bzrlib.option import Option
from bzrlib.commands import display_command
from bzrlib import trace
from bzrlib import errors
import os
""")

run_dir = os.getcwdu()

class BzrXMLRPCServer(SimpleXMLRPCServer):
    
    finished=False

    def __init__(self, addr, logRequests=False):
        SimpleXMLRPCServer.__init__(self, addr=addr, logRequests=logRequests)
        self.register_function(run_bzr, 'run_bzr')
        self.register_function(self.shutdown, 'quit')
        self.register_function(self.hello)
    
    def register_signal(self, signum):
        signal.signal(signum, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        print "Caught signal", signum
        self.shutdown()
        
    def shutdown(self):
        self.finished=True
        self.server_close()
        return 1

    def serve_forever(self):
        while not self.finished:
            self.handle_request()

    def hello(self):
        return 'world!'


def redirect_output(func):
    def wrapper(*args, **kwargs):
        sys.stdout = StringIO()
        sys.stderr = StringIO()
        try:
            return func(*args, **kwargs)
        finally:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
    return wrapper


@redirect_output
def run_bzr(argv, workdir):
    os.chdir(workdir)
    exitval = custom_commands_main(argv)
    return_val = (exitval, sys.stdout.getvalue(), sys.stderr.getvalue())
    os.chdir(run_dir)
    return return_val


def custom_commands_main(argv):
    import bzrlib.ui
    from bzrlib.ui.text import TextUIFactory
    bzrlib.ui.ui_factory = TextUIFactory()
    try:
        argv = [a.decode(bzrlib.user_encoding) for a in argv[1:]]
        ret = commands.run_bzr(argv)
        return ret
    except errors.BzrError, e:
        sys.stderr.write(str(XMLError(e)))
        return errors.EXIT_ERROR
    except Exception, e:
        sys.stderr.write(str(e))
        return errors.EXIT_ERROR
    finally:
        sys.stderr.flush();
        sys.stdout.flush();


class cmd_start_xmlrpc(commands.Command):
    """Start the xmlrpc service."""

    hidden=True
    takes_options = [
            Option('hostname', argname='HOSTNAME', type=str, 
                help='use the specified hostname, defaults to localhost'),
            Option('port', argname='PORT', type=int, 
                help='use the specified port, defaults to 11111'),
            'verbose',
            ]

    @display_command
    def run(self, port=11111, hostname='localhost', verbose=False):
        if hostname is None:
            hostname = socket.gethostname()

        if verbose:
            self.outf.write('Listening on http://' + hostname + ':' + str(port))
            self.outf.flush()

        self.server = BzrXMLRPCServer((hostname, port), logRequests=verbose)
        self.server.serve_forever()


