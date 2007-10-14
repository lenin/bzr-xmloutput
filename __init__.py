#!/usr/bin/env python
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
# Contributors: 
#               Martin Albisetti

"""
This plugin provides xml output for status, log, annotate, missing, info, version and plugins
adding a --xml option to each
"""
"""
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
    xml_serializer
    )

from bzrlib.workingtree import WorkingTree
from bzrlib.xml_serializer import _escape_cdata
""")

from bzrlib.option import Option
from bzrlib.commands import display_command, register_command
from bzrlib.log import LogFormatter, log_formatter_registry, LogRevision
import os

version_info = (0, 1, 0)

class cmd_status(builtins.cmd_status):
    builtins.cmd_status.takes_options.append(Option('xml', help='show status in xml format'))
    __doc__ = builtins.cmd_status.__doc__
    encoding_type = 'replace'

    @display_command
    def run(self, show_ids=False, file_list=None, revision=None, short=False,
            versioned=False, xml=False):
        if xml:
            from statusxml import show_tree_status_xml
            tree, file_list = builtins.tree_files(file_list)
            show_tree_status_xml(tree, show_ids=show_ids,
                    specific_files=file_list, revision=revision,
                    to_file=self.outf, versioned=False)
        else:
            status_class.run(self, show_ids=show_ids, file_list=file_list, 
                    revision=revision, short=short, versioned=versioned)

class cmd_annotate(builtins.cmd_annotate):
    builtins.cmd_annotate.takes_options.append(Option('xml', help='show annotations in xml format'))
    __doc__ = builtins.cmd_annotate.__doc__
    encoding_type = 'exact'

    @display_command
    def run(self, filename, all=False, long=False, revision=None,
            show_ids=False, xml=False):
        if xml:
            from annotatexml import annotate_file_xml
            tree, relpath = WorkingTree.open_containing(filename)
            wt_root_path = tree.id2abspath(tree.get_root_id())
            branch = tree.branch
            branch.lock_read()
            try:
                if revision is None:
                    revision_id = branch.last_revision()
                elif len(revision) != 1:
                    raise errors.BzrCommandError('bzr annotate --revision takes exactly 1 argument')
                else:
                    revision_id = revision[0].in_history(branch).rev_id
                file_id = tree.path2id(relpath)
                tree = branch.repository.revision_tree(revision_id)
                file_version = tree.inventory[file_id].revision
                # always run with --all and --long option (to get the author of each line)
                annotate_file_xml(branch=branch, rev_id=file_version, 
                        file_id=file_id, to_file=self.outf,
                        show_ids=show_ids, wt_root_path=wt_root_path, file_path=relpath)
            finally:
                branch.unlock()
        else:
            annotate_class.run(self, filename=filename, all=all, long=long, revision=revision,
            show_ids=show_ids)

class cmd_log(builtins.cmd_log):
    __doc__ = builtins.cmd_log.__doc__
    encoding_type = 'replace'

    @display_command
    def run(self, location=None, timezone='original',
            verbose=False,
            show_ids=False,
            forward=False,
            revision=None,
            log_format=None,
            message=None,
            limit=None):

        if log_format is XMLLogFormatter:
            if self.outf is None:
                self.outf = sys.stdout
            print >>self.outf, '<?xml version="1.0"?>'
            print >>self.outf, '<logs>'
            log_class.run(self, location=location, timezone=timezone, 
                    verbose=verbose, show_ids=show_ids, forward=forward, 
                    revision=revision, log_format=log_format, message=message, limit=limit)
            #workaround #2
            if XMLLogFormatter.last_log_was_merge:
                print >>self.outf, '</merge>'
            # workaround
            if XMLLogFormatter.log_count > 0:
                print >>self.outf, '</log>'
            print >>self.outf, '</logs>'
        else:
            log_class.run(self, location=location, timezone=timezone, 
                    verbose=verbose, show_ids=show_ids, forward=forward, 
                    revision=revision, log_format=log_format, message=message, limit=limit)

class cmd_missing(builtins.cmd_missing):
    __doc__ = builtins.cmd_missing.__doc__
    encoding_type = 'replace'

    @display_command
    def run(self, other_branch=None, reverse=False, mine_only=False,
                        theirs_only=False, log_format=None, long=False, short=False, line=False, 
                        show_ids=False, verbose=False, this=False, other=False):
        from missingxml import show_missing_xml
        
        
        if self.outf is None:
            self.outf = sys.stdout

        print >>self.outf, '<?xml version="1.0"?>'
        
        if log_format is XMLLogFormatter:
            
            if XMLLogFormatter.log_count > 0:
                print >>self.outf, '<logs>'
                print >>self.outf, '<log>'
            
            show_missing_xml(self, other_branch=other_branch, reverse=reverse, mine_only=mine_only,
                        theirs_only=theirs_only, log_format=log_format, long=long, short=short, line=line, 
                        show_ids=show_ids, verbose=verbose, this=this, other=other)
            # workaround
            if XMLLogFormatter.log_count > 0:
                print >>self.outf, '</log>'
                print >>self.outf, '</logs>'

        else:
            missing_class.run(self, other_branch=other_branch, reverse=reverse, mine_only=mine_only,
                        theirs_only=theirs_only, log_format=log_format, long=long, short=short, line=line, 
                        show_ids=show_ids, verbose=verbose, this=this, other=other)

class cmd_info(builtins.cmd_info):
    builtins.cmd_info.takes_options.append(Option('xml', help='show info in xml format'))
    __doc__ = builtins.cmd_info.__doc__
    
    @display_command
    def run(self, location=None, verbose=False, xml=False):
        if verbose:
            noise_level = 2
        else:
            noise_level = 0
        if xml:
            from infoxml import show_bzrdir_info_xml
            show_bzrdir_info_xml(bzrdir.BzrDir.open_containing(location)[0],
                             verbose=noise_level)
        else:
            from bzrlib.info import show_bzrdir_info
            show_bzrdir_info(bzrdir.BzrDir.open_containing(location)[0],
                             verbose=noise_level)

class cmd_plugins(builtins.cmd_plugins):
    builtins.cmd_plugins.takes_options.append(Option('xml', help='show plugins list in xml format'))
    __doc__ = builtins.cmd_info.__doc__

    @display_command
    def run(self, xml=False):
        if xml:
            import bzrlib.plugin
            from inspect import getdoc
            print '<plugins>'
            for name, plugin in bzrlib.plugin.plugins().items():
                print '<plugin>'
                print '<name>%s</name>' % name
                print '<version>%s</version>' % plugin.__version__
                print '<path>%s</path>' % plugin.path()
                d = getdoc(plugin.module)
                if d:
                    print '<doc>%s</doc>' % d
                print '</plugin>'
            print '</plugins>'
        else:
            super(cmd_plugins, self).run()

class cmd_version(builtins.cmd_version):
    builtins.cmd_version.takes_options.append(Option('xml', help='generates output in xml format'))
    __doc__ = builtins.cmd_version.__doc__
    encoding_type = 'replace'

    @display_command
    def run(self, xml=False):
        if(xml):
            from versionxml import show_version_xml
            show_version_xml(to_file=self.outf)
        else:
            version_class.run(self)
            
class XMLLogFormatter(LogFormatter):
    """ add a --xml format to 'bzr log'"""

    supports_merge_revisions = True
    supports_delta = True
    supports_tags = True
    log_count = 0
    last_log_was_merge = False

    def __init__(self, to_file, show_ids=False, show_timezone='original'):
        super(XMLLogFormatter, self).__init__(to_file=to_file, 
                               show_ids=show_ids, show_timezone=show_timezone)
        self.is_merge = False
        self.is_first = True
        self.first_log_is_merged = False
        XMLLogFormatter.last_log_was_merge = False
        log_count = 0
        
    def show(self, revno, rev, delta, tags=None):
        lr = LogRevision(rev, revno, 0, delta, tags)
        return self.log_revision(lr)

    def show_merge_revno(self, rev, merge_depth, revno):
        """a call to self._show_helper, XML don't care about formatting """
        lr = LogRevision(rev, merge_depth=merge_depth, revno=revno)
        return self.log_revision(lr)

    def log_revision(self, revision):
        """Log a revision, either merged or not."""
        from bzrlib.osutils import format_date
        to_file = self.to_file
        # to handle merge revision as childs
        if revision.merge_depth > 0:
            if not self.is_merge:
                ## to handle a first log with merge_depth > 0
                if not self.is_first and not self.first_log_is_merged:
                    print >>to_file,  '<merge>',
                else: 
                    self.first_log_is_merged = True
                self.is_merge = True
            print >>to_file,  '<log>',
            self.__log_revision(revision)
            print >>to_file,  '</log>',
            XMLLogFormatter.last_log_was_merge = True
        else:
            if self.first_log_is_merged:
                self.first_log_is_merged = False
                self.is_merge = False
            else:
                if self.is_merge or XMLLogFormatter.last_log_was_merge:
                    print >>to_file,  '</merge>',
                    self.is_merge = False
                if not self.is_first:
                    print >>to_file,  '</log>',
            print >>to_file,  '<log>',
            self.__log_revision(revision)
            XMLLogFormatter.last_log_was_merge = False
        if self.is_first:
            self.is_first = False
        XMLLogFormatter.log_count = XMLLogFormatter.log_count + 1

    def __log_revision(self, revision):
        from bzrlib.osutils import format_date
        import StringIO
        to_file = self.to_file
        if revision.revno is not None:
            print >>to_file,  '<revno>%s</revno>' % revision.revno,
        if revision.tags:
            print >>to_file,  '<tags>'
            for tag in revision.tags:
                print >>to_file, '<tag>%s</tag>' % tag
            print >>to_file,  '</tags>'
        if self.show_ids:
            print >>to_file,  '<revisionid>%s</revisionid>' % revision.rev.revision_id,
            if len(revision.rev.parent_ids) > 0:
                print >>to_file, '<parents>',
            for parent_id in revision.rev.parent_ids:
                print >>to_file, '<parent>%s</parent>' % parent_id,
            if len(revision.rev.parent_ids) > 0:
                print >>to_file, '</parents>',

        print >>to_file,  '<committer>%s</committer>' % \
                        _escape_cdata(revision.rev.committer),

        try:
            print >>to_file, '<branch-nick>%s</branch-nick>' % \
                _escape_cdata(revision.rev.properties['branch-nick']),
        except KeyError:
            pass
        date_str = format_date(revision.rev.timestamp,
                               revision.rev.timezone or 0,
                               self.show_timezone)
        print >>to_file,  '<timestamp>%s</timestamp>' % date_str,

        print >>to_file,  '<message>',
        if not revision.rev.message:
            print >>to_file, '(no message)'
        else:
            message = revision.rev.message.rstrip('\r\n')
            print >>to_file, os.linesep.join(_escape_cdata(message).splitlines()),
        print >>to_file,  '</message>',
        if revision.delta is not None:
            from statusxml import show_tree_xml
            print >>to_file,  '<affected-files>',
            show_tree_xml(revision.delta, to_file, self.show_ids)
            print >>to_file,  '</affected-files>',

status_class = register_command(cmd_status, decorate=True)
annotate_class = register_command(cmd_annotate, decorate=True)
missing_class = register_command(cmd_missing, decorate=True)
log_class = register_command(cmd_log, decorate=True)
info_class = register_command(cmd_info, decorate=True)
plugins_class = register_command(cmd_plugins, decorate=True)
version_class = register_command(cmd_version, decorate=True)
log_formatter_registry.register('xml', XMLLogFormatter,
                              'Detailed (not well formed?) XML log format')

