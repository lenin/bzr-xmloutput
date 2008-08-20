#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Copyright (C) 2007-2008 Guillermo Gonzalez
#
# The code taken from bzrlib is under: Copyright (C) 2005-2008 Canonical Ltd
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
from xmlrpclib import Fault
from xml_errors import XMLError
import codecs, logging
from bzrlib.lazy_import import lazy_import
lazy_import(globals(), """
import socket, sys, os
from cStringIO import StringIO 
import bzrlib
from bzrlib.option import Option
from bzrlib.commands import display_command
from bzrlib import commands, trace, errors, osutils
""")

bzrlib.user_encoding = 'utf-8'
run_dir = os.getcwdu()

class BzrXMLRPCServer(SimpleXMLRPCServer):
    
    finished=False

    def __init__(self, addr, logRequests=False, to_file=None):
        SimpleXMLRPCServer.__init__(self, addr=addr, logRequests=logRequests)
        self.register_function(self.system_listMethods, 'list_methods')
        self.register_function(self.shutdown, 'quit')
        self.register_function(self.hello)
        self.to_file = to_file
        if to_file is None:
            self.to_file = sys.stdout
         
    
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


class redirect_output(object):

    def __init__(self):
        self.writer_factory = codecs.getwriter('utf8')
        self.remove_logger()
        
    def __call__(self, func):
        def wrapper(*args, **kwargs):
            trace.mutter('%s arguments: %s' % (func.func_name, str(args)))
            sys.stdout = StringIO()
            sys.stderr = StringIO()
            self.set_logger()
            try:
                return func(*args, **kwargs)
            finally:
                self.remove_logger()
                sys.stdout = sys.__stdout__
                sys.stderr = sys.__stderr__
        return wrapper
    
    def set_logger(self):
        """add sys.stderr as a log handler"""
        encoded_stderr = self.writer_factory(sys.stderr, errors='replace')
        stderr_handler = logging.StreamHandler(encoded_stderr)
        stderr_handler.setLevel(logging.INFO)
        logging.getLogger('bzr').addHandler(stderr_handler)
    
    def remove_logger(self):
        """removes extra log handlers, only keeps the .bzr.log hanlder"""
        del trace._bzr_logger.handlers[1:len(trace._bzr_logger.handlers)]


@redirect_output()
def run_bzr(argv, workdir):
    return _run_bzr(argv, workdir, commands.main)


@redirect_output()
def run_bzr_xml(argv, workdir):
    return _run_bzr(argv, workdir, custom_commands_main)


def _run_bzr(argv, workdir, func):
    os.chdir(workdir)
    exitval = func(argv)
    sys.stderr.flush()
    sys.stdout.flush()
    if isinstance(exitval, Fault):
        return_val = exitval
    else: 
        return_val = (exitval, sys.stdout.getvalue(),
                    sys.stderr.getvalue())
    os.chdir(run_dir)
    return return_val


def custom_commands_main(argv):
    import bzrlib.ui
    bzrlib.ui.ui_factory = bzrlib.ui.SilentUIFactory()
    try:
        argv = [a.decode(bzrlib.user_encoding) for a in argv[1:]]
        ret = commands.run_bzr(argv)
        return ret
    except errors.BzrError, e:
        raise Fault(42, str(XMLError(e)))
    except Exception, e:
        raise Fault(32, str(XMLError(e)))


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

        self.server = BzrXMLRPCServer((hostname, port), 
                                     logRequests=verbose, to_file=self.outf)
        register_functions(self.server)
        
        import bzrlib.osutils
        bzrlib.user_encoding = 'UTF-8'
        bzrlib.osutils._cached_user_encoding = bzrlib.user_encoding
        bzrlib.osutils.bzrlib.user_encoding = bzrlib.user_encoding
        
        try:
            self.server.serve_forever()
        finally:
            self.server.shutdown()


def register_functions(server):
    server.register_function(run_bzr, 'run_bzr_command')
    server.register_function(run_bzr_xml, 'run_bzr')
    import search
    if search.is_available:
        server.register_function(search.search, 'search')
