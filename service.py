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
from bzrlib.lazy_import import lazy_import
lazy_import(globals(), """
import socket, sys
from cStringIO import StringIO 
from bzrlib import commands
from bzrlib.option import Option
from bzrlib.commands import display_command
""")

class BzrXMLRPCServer(SimpleXMLRPCServer):
    
    finished=False

    def __init__(self, args):
        SimpleXMLRPCServer.__init__(self, args)
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


def run_bzr(argv):
    sys.stdout = StringIO()
    sys.stderr = StringIO()
    return_val = (commands.main(argv), sys.stdout.getvalue(), sys.stderr.getvalue())
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    return return_val


class cmd_start_xmlrpc(commands.Command):
    """Start the xmlrpc service."""

    hidden=True
    takes_options = [
            Option('hostname', argname='HOSTNAME', type=str, help='use the specified hostname, defaults to localhost'),
            Option('port', argname='PORT', type=int, help='use the specified port, defaults to 11111')
            ]

    @display_command
    def run(self, port=11111, hostname='localhost'):
        if hostname is None:
            hostname = socket.gethostname()
        print 'http://' + hostname + ':' + str(port)
        self.server = BzrXMLRPCServer((hostname, port))
        self.server.serve_forever()

