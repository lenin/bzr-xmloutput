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
This plugin provides xml output for status, log, annotate, missing, info,
version and plugins adding a --xml option to each

(most of this is code was modified from bzrlib.cmd_status,
bzrlib.status, bzrlib.delta.TreeDelta.show and bzrlib.log.LongLogFormatter)
"""
import bzrlib
from bzrlib.lazy_import import lazy_import
lazy_import(globals(), """
import sys
from bzrlib import (
    builtins,
    bzrdir,
    commands,
    option,
    log,
    workingtree,
    xml_serializer,
    errors
    )

from bzrlib.option import Option, custom_help
from bzrlib.commands import display_command, register_command
import logxml
import service
import socket
from xml_errors import handle_error_xml
""")


version_info = (0, 8, 5)
plugin_name = 'xmloutput'

null_option = option.Option('null',
                            help='Write an ascii NUL (\\0) as the final char.')


class cmd_xmlstatus(commands.Command):
    """Display status summary.

    This reports on versioned and unknown files, reporting them
    grouped by state.  Possible states are:

    added
        Versioned in the working copy but not in the previous revision.

    removed
        Versioned in the previous revision but removed or deleted
        in the working copy.

    renamed
        Path of this file changed from the previous revision;
        the text may also have changed.  This includes files whose
        parent directory was renamed.

    modified
        Text has changed since the previous revision.

    kind changed
        File kind has been changed (e.g. from file to directory).

    unknown
        Not versioned and not matching an ignore pattern.

    To see ignored files use 'bzr ignored'.  For details on the
    changes to file texts, use 'bzr diff'.

    Note that --short or -S gives status flags for each item, similar
    to Subversion's status command. To get output similar to svn -q,
    use bzr -SV.

    If no arguments are specified, the status of the entire working
    directory is shown.  Otherwise, only the status of the specified
    files or directories is reported.  If a directory is given, status
    is reported for everything inside that directory.

    If a revision argument is given, the status is calculated against
    that revision, or between two revisions if two are provided.
    """
    hidden = True
    takes_args = ['file*']
    takes_options = ['show-ids', 'revision', 'change',
                     Option('versioned', help='Only show versioned files.',
                            short_name='V'),
                     null_option
                     ]
    encoding_type = 'replace'

    @display_command
    @handle_error_xml
    def run(self, file_list=None, revision=None, versioned=False, null=False):
        from statusxml import show_tree_status_xml
        tree, file_list = builtins.tree_files(file_list)
        to_file = self.outf
        if to_file is None:
            to_file = sys.stdout
        show_tree_status_xml(tree, show_ids=True,
            specific_files=file_list, revision=revision,
            to_file=to_file, versioned=versioned)
        if null:
            to_file.write('\0')
        self.outf.write('\n')


class cmd_xmlannotate(commands.Command):
    """Show the origin of each line in a file.

    This prints out the given file with an annotation on the left side
    indicating which revision, author and date introduced the change.

    If the origin is the same for a run of consecutive lines, it is
    shown only at the top, unless the --all option is given.
    """
    hidden = True
    takes_args = ['filename']
    takes_options = ['revision', 'show-ids', null_option]

    encoding_type = 'exact'

    @display_command
    @handle_error_xml
    def run(self, filename, revision=None, show_ids=False, null=False):
        from annotatexml import annotate_file_xml
        wt, branch, relpath = \
            bzrdir.BzrDir.open_containing_tree_or_branch(filename)
        if wt is not None:
            wt.lock_read()
        else:
            branch.lock_read()
        wt_root_path = wt.id2abspath(wt.get_root_id())
        try:
            if revision is None:
                revision_id = branch.last_revision()
            elif len(revision) != 1:
                raise bzrlib.errors.BzrCommandError(
                    'xmlannotate --revision takes exactly 1 argument')
            else:
                revision_id = revision[0].in_history(branch).rev_id
            tree = branch.repository.revision_tree(revision_id)
            if wt is not None:
                file_id = wt.path2id(relpath)
            else:
                file_id = tree.path2id(relpath)
            if file_id is None:
                raise bzrlib.errors.NotVersionedError(filename)

            file_version = tree.inventory[file_id].revision
            # always run with --all and --long options
            # to get the author of each line
            annotate_file_xml(branch=branch, rev_id=file_version,
                    file_id=file_id, to_file=self.outf, show_ids=show_ids,
                    wt_root_path=wt_root_path, file_path=relpath)
            if null:
                self.outf.write('\0')
            self.outf.write('\n')
        finally:
            if wt is not None:
                wt.unlock()
            else:
                branch.unlock()


class cmd_xmlmissing(commands.Command):
    """Show unmerged/unpulled revisions between two branches.

    OTHER_BRANCH may be local or remote.
    """
    hidden = True
    takes_args = ['other_branch?']
    takes_options = [
            Option('reverse', 'Reverse the order of revisions.'),
            Option('mine-only',
                   'Display changes in the local branch only.'),
            Option('this' , 'Same as --mine-only.'),
            Option('theirs-only',
                   'Display changes in the remote branch only.'),
            Option('other', 'Same as --theirs-only.'),
            'show-ids',
            'verbose',
            null_option
            ]
    encoding_type = 'replace'

    @display_command
    @handle_error_xml
    def run(self, *args, **kwargs):
        from missingxml import show_missing_xml

        if self.outf is None:
            self.outf = sys.stdout

        show_missing_xml(self, log_format=logxml.XMLLogFormatter,
                         *args, **kwargs)
        if getattr(kwargs, 'null', False):
            self.outf.write('\0')
        self.outf.write('\n')


class cmd_xmlinfo(commands.Command):
    """Show information about a working tree, branch or repository.

    This command will show all known locations and formats associated to the
    tree, branch or repository.  Statistical information is included with
    each report.

    Branches and working trees will also report any missing revisions.
    """
    hidden = True
    takes_args = ['location?']
    takes_options = ['verbose', null_option]
    encoding_type = 'replace'

    @display_command
    @handle_error_xml
    def run(self, *args, **kwargs):
        location = None
        if kwargs.has_key('location'):
            location = kwargs['location']
        if kwargs.has_key('verbose') and kwargs['verbose']:
            noise_level = 2
        else:
            noise_level = 0
        from infoxml import show_bzrdir_info_xml
        if location != None:
            from bzrlib.urlutils import normalize_url
            location = normalize_url(location)
        show_bzrdir_info_xml(bzrdir.BzrDir.open_containing(location)[0],
                             verbose=noise_level, outfile=self.outf)
        if getattr(kwargs, 'null', False):
            self.outf.write('\0')
        self.outf.write('\n')


class cmd_xmlplugins(commands.Command):
    """List the installed plugins.

    This command displays the list of installed plugins including
    version of plugin and a short description of each.

    """
    hidden = True
    takes_options = ['verbose', null_option]

    @display_command
    @handle_error_xml
    def run(self, *args, **kwargs):
        import bzrlib.plugin
        from inspect import getdoc
        if self.outf is None:
            self.outf = sys.stdout

        self.outf.write('<?xml version="1.0" encoding="%s"?>' % \
                bzrlib.user_encoding)
        self.outf.write('<plugins>')
        from bzrlib.xml_serializer import _escape_cdata
        for name, plugin in bzrlib.plugin.plugins().items():
            self.outf.write('<plugin>')
            self.outf.write('<name>%s</name>' % name)
            self.outf.write('<version>%s</version>' % plugin.__version__)
            self.outf.write('<path>%s</path>' % plugin.path())
            d = getdoc(plugin.module)
            if d:
                self.outf.write('<doc>%s</doc>' % _escape_cdata(d))
            self.outf.write('</plugin>')
        self.outf.write('</plugins>')
        if getattr(kwargs, 'null', False):
            self.outf.write('\0')
        self.outf.write('\n')


class cmd_xmlversion(commands.Command):
    """Show version of bzr."""
    hidden = True
    encoding_type = 'replace'
    takes_options = [Option("short", help="Only print the version number."),
                    null_option]

    @display_command
    @handle_error_xml
    def run(self, short=False, null=False):
        from versionxml import show_version_xml
        to_file = self.outf
        if to_file is None:
            to_file = sys.stdout
        if short:
            to_file.write("<version><bazaar><version>" + \
            bzrlib.version_string + \
            "</version></bazaar></version>")
        else:
            show_version_xml(to_file=to_file)
        if null:
            to_file.write('\0')
        to_file.write('\n')


def xmllog_options():
    # Take a copy of the log options before modifying it
    opts = builtins.cmd_log.takes_options[:]
    opts.append(null_option)
    # Remove log_format since we requires our own
    opts.remove('log-format')
    return opts


class cmd_xmllog(builtins.cmd_log):
    """Show log of a branch, file, or directory as XML."""
    hidden = True

    takes_options = xmllog_options()

    @display_command
    @handle_error_xml
    def run(self, *args, **kwargs):
        # Force our specific formatter
        kwargs['log_format'] = logxml.XMLLogFormatter
        # Filter out our specific option
        try:
            null = kwargs.pop('null')
        except KeyError:
            null = False
        exit_val =  builtins.cmd_log.run(self, *args, **kwargs)
        if null:
            self.outf.write('\0')
        self.outf.write('\n')
        return exit_val


class cmd_xmlls(builtins.cmd_ls):
    """XML representation of the list of files in a tree.
    """

    hidden = True
    _see_also = ['xmlstatus']
    takes_args = ['path?']
    # TODO: Take a revision or remote path and list that tree instead.
    takes_options = [
            'verbose',
            'revision',
            Option('non-recursive',
                   help='Don\'t recurse into subdirectories.'),
            Option('from-root',
                   help='Print paths relative to the root of the branch.'),
            Option('unknown', help='Print unknown files.'),
            Option('versioned', help='Print versioned files.',
                   short_name='V'),
            Option('ignored', help='Print ignored files.'),
            Option('kind',
                   help='List entries of a particular kind: file, ' + \
                   'directory, symlink.',
                   type=unicode),
            null_option
            ]
    encoding_type = 'replace'


    @display_command
    @handle_error_xml
    def run(self, *args, **kwargs):
        import lsxml
        self.outf.write('<?xml version="1.0" encoding="%s"?>' % \
                bzrlib.user_encoding)
        lsxml.show_ls_xml(self.outf, *args, **kwargs)
        if getattr(kwargs, 'null', False):
            self.outf.write('\0')
        self.outf.write('\n')

class cmd_start_xmlrpc(commands.Command):
    """Start the xmlrpc service."""

    hidden = True
    takes_options = [
            Option('hostname', argname='HOSTNAME', type=str,
                help='Use the specified hostname, defaults to localhost.'),
            Option('port', argname='PORT', type=int,
                help='Use the specified port, defaults to 11111.'),
            'verbose',
            ]

    @display_command
    def run(self, port=11111, hostname='localhost', verbose=False):
        if hostname is None:
            hostname = socket.gethostname()

        if verbose:
            self.outf.write('Listening on http://'+hostname+':'+str(port)+'\n')
            self.outf.flush()

        self.server = service.BzrXMLRPCServer((hostname, port),
                                     logRequests=verbose, to_file=self.outf)

        try:
            self.server.serve_forever()
        finally:
            self.server.shutdown()


class cmd_stop_xmlrpc(commands.Command):
    """Stops a xmlrpc service."""

    hidden = True
    takes_options = [
            Option('hostname', argname='HOSTNAME', type=str,
                help='Use the specified hostname, defaults to localhost.'),
            Option('port', argname='PORT', type=int,
                help='Use the specified port, defaults to 11111.'),
            'verbose',
            ]

    @display_command
    def run(self, port=11111, hostname='localhost', verbose=False):
        url = "http://"+hostname+":"+str(port)
        if verbose:
            self.outf.write('Stopping xmlrpc service on ' + url + '\n')
            self.outf.flush()
        from xmlrpclib import Server
        server = Server(url)
        server.quit()

register_command(cmd_xmlstatus, decorate=True)
register_command(cmd_xmlannotate, decorate=True)
register_command(cmd_xmlmissing, decorate=True)
register_command(cmd_xmlinfo, decorate=True)
register_command(cmd_xmlplugins, decorate=True)
register_command(cmd_xmlversion, decorate=True)
register_command(cmd_start_xmlrpc, decorate=True)
register_command(cmd_stop_xmlrpc, decorate=True)
register_command(cmd_xmllog, decorate=True)
register_command(cmd_xmlls, decorate=True)
log.log_formatter_registry.register('xml', logxml.XMLLogFormatter,
                              'Detailed XML log format')


def load_tests(basic_tests, module, loader):
    testmod_names = [
        'tests',
        ]
    basic_tests.addTest(loader.loadTestsFromModuleNames(
            ["%s.%s" % (__name__, tmn) for tmn in testmod_names]))
    return basic_tests
