#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Copyright (C) 2008-2009 Guillermo Gonzalez
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
""" xmlrpc service module """

from bzrlib.lazy_import import lazy_import
lazy_import(globals(), """
import bzrlib
from bzrlib import (
    commands,
    trace,
    errors,
    osutils
    )
import sys
import os
import codecs
import logging
import traceback
from cStringIO import StringIO
""")

from xml_errors import XMLError
from xmlrpclib import Fault, Binary
from SimpleXMLRPCServer import SimpleXMLRPCServer

run_dir = os.getcwdu()


class BzrXMLRPCServer(SimpleXMLRPCServer):
    """ Very simple xmlrpc server to handle bzr commands and search"""

    finished = False

    def __init__(self, addr, logRequests=False, to_file=None):
        SimpleXMLRPCServer.__init__(self, addr=addr,
            logRequests=logRequests)
        self.register_function(self.system_listMethods, 'list_methods')
        self.register_function(self.shutdown, 'quit')
        self.register_function(self.hello)
        register_functions(self)
        self.to_file = to_file
        if to_file is None:
            self.to_file = sys.stdout

    def register_signal(self, signum):
        """register a signal using self.signal_handler"""
        signal.signal(signum, self.signal_handler)

    def signal_handler(self, signum, frame):
        """signal handler, shutdown by default"""
        print "Caught signal", signum
        self.shutdown()

    def shutdown(self):
        """ stop serving and return 1 """
        self.finished = True
        self.server_close()
        return 1

    def serve_forever(self):
        """Start serving, and block"""
        import bzrlib.osutils
        default_encoding = 'UTF-8'
        if hasattr(bzrlib, 'user_encoding'):
            bzrlib.user_encoding = default_encoding
            bzrlib.osutils.bzrlib.user_encoding = default_encoding
        bzrlib.osutils._cached_user_encoding = default_encoding
        self.encoding = default_encoding
        # support new super lazy commands (bzr-1.17)
        if getattr(commands, 'install_bzr_command_hooks'):
            commands.install_bzr_command_hooks()
        while not self.finished:
            self.handle_request()

    def hello(self):
        """ simple reply to hello request, 'world!'"""
        return 'world!'


class redirect_output(object):
    """decorator to redirect stdout/err to a StringIO"""

    def __init__(self, func):
        self.writer_factory = codecs.getwriter('utf8')
        self.func = func
        self.logger_removed = False

    def __call__(self, *args, **kwargs):
        if self.logger_removed:
            self.remove_logger()
        trace.mutter('%s arguments: %s' % (self.func.func_name, str(args)))
        sys.stdout = StringIO()
        sys.stderr = StringIO()
        self.set_logger()
        try:
            return self.func(*args, **kwargs)
        finally:
            self.remove_logger()
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__

    def set_logger(self):
        """add sys.stderr as a log handler"""
        encoded_stderr = self.writer_factory(sys.stderr, errors='replace')
        stderr_handler = logging.StreamHandler(encoded_stderr)
        stderr_handler.setLevel(logging.INFO)
        logging.getLogger('bzr').addHandler(stderr_handler)

    def remove_logger(self):
        """removes extra log handlers, only keeps the .bzr.log handler"""
        self.logger_removed = True
        del trace._bzr_logger.handlers[1:len(trace._bzr_logger.handlers)]


@redirect_output
def run_bzr(argv, workdir):
    """run a regular bzr command"""
    return _run_bzr(argv, workdir, commands.main)


@redirect_output
def run_bzr_xml(argv, workdir):
    """run a bzr command, but handle errors using XMLError"""
    return _run_bzr(argv, workdir, custom_commands_main)


def _run_bzr(argv, workdir, func):
    """Actually executes the command and build the response."""
    try:
        os.chdir(workdir)
        exitval = func(argv)
        sys.stderr.flush()
        sys.stdout.flush()
        if isinstance(exitval, Fault):
            return_val = exitval
        else:
            # use a Binary object to wrap the output to avoid NULL and other
            # non xmlrpc (or client xml parsers) friendly chars
            out = Binary(data=sys.stdout.getvalue())
            return_val = (exitval, out, sys.stderr.getvalue())
            os.chdir(run_dir)
        return return_val
    except:
        import traceback
        traceback.print_exc(file=sys.__stderr__)
        raise


def custom_commands_main(argv):
    """custom commands.main that handle errors using XMLError"""
    import bzrlib.ui
    bzrlib.ui.ui_factory = bzrlib.ui.SilentUIFactory()
    try:
        _argv = []
        for a in argv[1:]:
            if isinstance(a, str):
                a = a.decode(bzrlib.osutils.get_user_encoding())
            _argv.append(a)
        argv = _argv
        ret = commands.run_bzr(argv)
        return ret
    except errors.BzrError, e:
        raise Fault(42, str(XMLError(e)))
    except Exception, e:
        traceback.print_exc(file=sys.__stderr__)
        raise Fault(32, str(XMLError(e)))


def register_functions(server):
    """register functions exposed via xmlrpc."""
    server.register_function(run_bzr, 'run_bzr_command')
    server.register_function(run_bzr_xml, 'run_bzr')
    import search
    if search.is_available:
        server.register_function(search.search, 'search')

