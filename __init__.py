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
    xml_serializer,
    errors
    )

from bzrlib.workingtree import WorkingTree
""")

from bzrlib.option import Option
from bzrlib.commands import display_command, register_command
from bzrlib.log import log_formatter_registry 
import logxml
from logxml import XMLLogFormatter 

version_info = (0, 4, 0)
plugin_name = 'xmloutput'

class cmd_status(builtins.cmd_status):
    builtins.cmd_status.takes_options.append(Option('xml', help='Show status in xml format'))
    __doc__ = builtins.cmd_status.__doc__
    encoding_type = 'replace'

    @display_command
    def run(self, show_ids=False, file_list=None, revision=None, short=False,
            versioned=False, xml=False):
        if xml:
            from statusxml import show_tree_status_xml
            tree, file_list = builtins.tree_files(file_list)
            to_file = self.outf
            if to_file is None:
                to_file = sys.stdout
            show_tree_status_xml(tree, show_ids=show_ids,
                    specific_files=file_list, revision=revision,
                    to_file=to_file, versioned=versioned)
        else:
            status_class.run(self, show_ids=show_ids, file_list=file_list, 
                    revision=revision, short=short, versioned=versioned)

class cmd_annotate(builtins.cmd_annotate):
    builtins.cmd_annotate.takes_options.append(Option('xml', help='Show annotations in xml format'))
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
                if file_id is None:
                    raise errors.NotVersionedError(filename)
                tree = branch.repository.revision_tree(revision_id)
                file_version = tree.inventory[file_id].revision
                # always run with --all and --long option (to get the author of each line)
                to_file = self.outf
                if to_file is None:
                    to_file = sys.stdout
                annotate_file_xml(branch=branch, rev_id=file_version, 
                        file_id=file_id, to_file=to_file,
                        show_ids=show_ids, wt_root_path=wt_root_path, file_path=relpath)
            finally:
                branch.unlock()
        else:
            annotate_class.run(self, filename=filename, all=all, long=long, revision=revision,
            show_ids=show_ids)

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
        
        if log_format is XMLLogFormatter:
            show_missing_xml(self, other_branch=other_branch, reverse=reverse, mine_only=mine_only,
                        theirs_only=theirs_only, log_format=log_format, long=long, short=short, line=line, 
                        show_ids=show_ids, verbose=verbose, this=this, other=other)
        else:
            missing_class.run(self, other_branch=other_branch, reverse=reverse, mine_only=mine_only,
                        theirs_only=theirs_only, log_format=log_format, long=long, short=short, line=line, 
                        show_ids=show_ids, verbose=verbose, this=this, other=other)

class cmd_info(builtins.cmd_info):
    builtins.cmd_info.takes_options.append(Option('xml', help='Show info in xml format'))
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
    builtins.cmd_plugins.takes_options.append(Option('xml', help='Show plugins list in xml format'))
    __doc__ = builtins.cmd_info.__doc__

    @display_command
    def run(self, xml=False):
        if xml:
            import bzrlib.plugin
            from inspect import getdoc
            if self.outf is None:
                self.outf = sys.stdout

            self.outf.write('<?xml version="1.0" encoding="%s"?>' % \
                    bzrlib.user_encoding)
            self.outf.write('<plugins>')
            for name, plugin in bzrlib.plugin.plugins().items():
                self.outf.write('<plugin>')
                self.outf.write('<name>%s</name>' % name)
                self.outf.write('<version>%s</version>' % plugin.__version__)
                self.outf.write('<path>%s</path>' % plugin.path())
                d = getdoc(plugin.module)
                if d:
                    self.outf.write('<doc>%s</doc>' % d)
                self.outf.write('</plugin>')
            self.outf.write('</plugins>')
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
            to_file = self.outf
            if to_file is None:
                to_file = sys.stdout
            show_version_xml(to_file=to_file)
        else:
            version_class.run(self)
            
status_class = register_command(cmd_status, decorate=True)
annotate_class = register_command(cmd_annotate, decorate=True)
missing_class = register_command(cmd_missing, decorate=True)
info_class = register_command(cmd_info, decorate=True)
plugins_class = register_command(cmd_plugins, decorate=True)
version_class = register_command(cmd_version, decorate=True)
log_formatter_registry.register('xml', XMLLogFormatter,
                              'Detailed XML log format')

def test_suite():
    import tests
    return tests.test_suite()
