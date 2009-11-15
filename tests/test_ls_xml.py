# Copyright (C) 2006 Canonical Ltd
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

"""Blackbox tests of 'bzr xmlls'"""

import os

from bzrlib import ignores
from bzrlib.tests import TestCaseWithTransport
from bzrlib.trace import mutter
from bzrlib.xml_serializer import elementtree as elementtree
fromstring = elementtree.ElementTree.fromstring


class TestLSXML(TestCaseWithTransport):

    def setUp(self):
        super(TestLSXML, self).setUp()

        # Create a simple branch that can be used in testing
        ignores._set_user_ignores(['user-ignore'])

        self.wt = self.make_branch_and_tree('.')
        self.build_tree_contents([
                                 ('.bzrignore', '*.pyo\n'),
                                 ('a', 'hello\n'),
                                 ])

    def run_xmlls(self, args=None):
        command = 'xmlls'
        if args:
            command += ' ' + args
        out, err = self.run_bzr(command)
        self.assertEqual('', err)
        # parse the output and convert it into more usable structure:
        #   [ { 'kind': 'file, 'path': 'foo', ... }, ... ]
        lst = fromstring(out)
        items = []
        for item_elem in lst.findall('item'):
            item = {}
            for attr in item_elem.getchildren():
                item[attr.tag] = attr.text
            items.append(item)
        return items
        
    #def test_lsxml_null_verbose(self):
    #    # Can't supply both
    #    self.run_bzr_error(['Cannot set both --verbose and --null'],
    #                       'xmlls --verbose --null')

    def test_lsxml_basic(self):
        """Test the abilities of 'bzr xmlls'"""
        expected_items = [{'kind': 'file',
                           'path': '.bzrignore',
                           'status_kind': 'unknown'},
                          {'kind': 'file',
                           'path': 'a',
                           'status_kind': 'unknown'}]
        self.assertEquals(expected_items, self.run_xmlls())
        self.assertEquals(expected_items, self.run_xmlls('--unknown'))
        self.assertEquals([], self.run_xmlls('--ignored'))
        self.assertEquals([], self.run_xmlls('--versioned'))
        self.assertEquals([], self.run_xmlls('-V'))
        self.assertEquals(expected_items,
                          self.run_xmlls('--unknown --ignored --version'))
        self.assertEquals(expected_items,
                          self.run_xmlls('--unknown --ignored -V'))
        self.assertEquals([], self.run_xmlls('--ignored -V'))

    def test_lsxml_added(self):
        self.wt.add(['a'], ['a-id'])
        expected_items = [{'kind': 'file',
                           'path': '.bzrignore',
                           'status_kind': 'unknown'},
                          {'id': 'a-id',
                           'kind': 'file',
                           'path': 'a',
                           'status_kind': 'versioned'}]
        self.assertEquals(expected_items, self.run_xmlls())
        
        self.wt.commit('add')
        self.build_tree(['subdir/'])
        expected_items = [{'kind': 'file',
                           'path': '.bzrignore',
                           'status_kind': 'unknown'},
                          {'id': 'a-id',
                           'kind': 'file',
                           'path': 'a',
                           'status_kind': 'versioned'},
                          {'kind': 'directory',
                           'path': 'subdir',
                           'status_kind': 'unknown'}]
        self.assertEquals(expected_items, self.run_xmlls())
        
        self.build_tree(['subdir/b'])
        self.wt.add(['subdir/', 'subdir/b', '.bzrignore'],
            ['subdir-id', 'subdirb-id', 'bzrignore-id'])
        expected_items = [{'id': 'bzrignore-id',
                           'kind': 'file',
                           'path': '.bzrignore',
                           'status_kind': 'versioned'},
                          {'id': 'a-id',
                           'kind': 'file',
                           'path': 'a',
                           'status_kind': 'versioned'},
                          {'id': 'subdir-id',
                           'kind': 'directory',
                           'path': 'subdir',
                           'status_kind': 'versioned'},
                          {'id': 'subdirb-id',
                           'kind': 'file',
                           'path': 'subdir/b',
                           'status_kind': 'versioned'}]
        self.assertEquals(expected_items, self.run_xmlls())

    def test_lsxml_non_recursive(self):
        self.build_tree(['subdir/', 'subdir/b'])
        self.wt.add(['a', 'subdir/', 'subdir/b', '.bzrignore'],
            ['a-id', 'subdir-id', 'subdirb-id', 'bzrignore-id'])
        expected_items = [{'id': 'bzrignore-id',
                           'kind': 'file',
                           'path': '.bzrignore',
                           'status_kind': 'versioned'},
                          {'id': 'a-id',
                           'kind': 'file',
                           'path': 'a',
                           'status_kind': 'versioned'},
                          {'id': 'subdir-id',
                           'kind': 'directory',
                           'path': 'subdir',
                           'status_kind': 'versioned'}]
        self.assertEquals(expected_items, self.run_xmlls('--non-recursive'))

        # Check what happens in a sub-directory
        os.chdir('subdir')
        expcted_items = [{'id': 'subdirb-id',
                          'kind': 'file',
                          'path': 'b',
                          'status_kind': 'versioned'}]
        self.assertEquals(expcted_items, self.run_xmlls())
        expcted_items = [{'id': 'subdirb-id',
                          'kind': 'file',
                          'path': 'subdir/b',
                          'status_kind': 'versioned'}]
        self.assertEquals(expcted_items, self.run_xmlls('--from-root'))
        expected_items = [{'id': 'subdirb-id',
                           'kind': 'file',
                           'path': 'subdir/b',
                           'status_kind': 'versioned'}]
        self.assertEquals(expected_items,
                          self.run_xmlls('--from-root --non-recursive'))

    def test_lsxml_path(self):
        """If a path is specified, files are listed with that prefix"""
        self.build_tree(['subdir/', 'subdir/b'])
        self.wt.add(['subdir', 'subdir/b'], ['subdir-id', 'subdirb-id'])
        expected_items = [{'id': 'subdir-id',
                           'kind': 'directory',
                           'path': 'subdir',
                           'status_kind': 'versioned'},
                          {'id': 'subdirb-id',
                           'kind': 'file',
                           'path': 'subdir/b',
                           'status_kind': 'versioned'},]
        self.assertEquals(expected_items, self.run_xmlls('subdir'))

        # Check what happens in a sub-directory, referring to parent
        os.chdir('subdir')
        expected_items = [{'kind': 'file',
                           'path': '.bzrignore',
                           'status_kind': 'unknown'},
                          {'kind': 'file',
                           'path': 'a',
                           'status_kind': 'unknown'},
                          {'id': 'subdir-id',
                           'kind': 'directory',
                           'path': 'subdir',
                           'status_kind': 'versioned'},
                          {'id': 'subdirb-id',
                           'kind': 'file',
                           'path': 'subdir/b',
                           'status_kind': 'versioned'}]
        self.assertEquals(expected_items, self.run_xmlls('..'))
        self.run_bzr_error(['cannot specify both --from-root and PATH'],
                           'xmlls --from-root ..')

    def test_lsxml_revision(self):
        self.wt.add(['a'], ['a-id'])
        self.wt.commit('add')

        self.build_tree(['subdir/'])

        # Check what happens when we supply a specific revision
        expected_items = [{'id': 'a-id',
                           'kind': 'file',
                           'path': 'a',
                           'status_kind': 'versioned'}]
        self.assertEquals(expected_items, self.run_xmlls('--revision 1'))

        os.chdir('subdir')
        self.assertEquals([], self.run_xmlls('--revision 1'))

    def test_lsxml_branch(self):
        """If a branch is specified, files are listed from it"""
        self.build_tree(['subdir/', 'subdir/b'])
        self.wt.add(['subdir', 'subdir/b'], ['subdir-id', 'subdirb-id'])
        self.wt.commit('committing')
        branch = self.make_branch('branchdir')
        branch.pull(self.wt.branch)
        expected_items = [{'id': 'subdir-id',
                           'kind': 'directory',
                           'path': 'branchdir/subdir',
                           'status_kind': 'versioned'},
                          {'id': 'subdirb-id',
                           'kind': 'file',
                           'path': 'branchdir/subdir/b',
                           'status_kind': 'versioned'}]
        self.assertEquals(expected_items, self.run_xmlls('branchdir'))
        self.assertEquals(expected_items,
                          self.run_xmlls('branchdir --revision 1'))

    def test_lsxml_ignored(self):
        # Now try to do ignored files.
        self.wt.add(['a', '.bzrignore'], ['a-id', 'bzrignore-id'])
        self.build_tree(['blah.py', 'blah.pyo', 'user-ignore'])
        expected_items = [{'id': 'bzrignore-id',
                           'kind': 'file',
                           'path': '.bzrignore',
                           'status_kind': 'versioned'},
                          {'id': 'a-id',
                           'kind': 'file',
                           'path': 'a',
                           'status_kind': 'versioned'},
                          {'kind': 'file',
                           'path': 'blah.py',
                           'status_kind': 'unknown'},
                          {'kind': 'file',
                           'path': 'blah.pyo',
                           'status_kind': 'ignored'},
                          {'kind': 'file',
                           'path': 'user-ignore',
                           'status_kind': 'ignored'}]
        self.assertEquals(expected_items, self.run_xmlls())
        expected_items = [{'kind': 'file',
                           'path': 'blah.pyo',
                           'pattern': '*.pyo',
                           'status_kind': 'ignored'},
                          {'kind': 'file',
                           'path': 'user-ignore',
                           'pattern': 'user-ignore',
                           'status_kind': 'ignored'}]
        self.assertEquals(expected_items, self.run_xmlls('--ignored'))
        expected_items = [{'kind': 'file',
                           'path': 'blah.py',
                           'status_kind': 'unknown'}]
        self.assertEquals(expected_items, self.run_xmlls('--unknown'))
        expected_items = [{'id': 'bzrignore-id',
                           'kind': 'file',
                           'path': '.bzrignore',
                           'status_kind': 'versioned'},
                          {'id': 'a-id',
                           'kind': 'file',
                           'path': 'a',
                           'status_kind': 'versioned'}]
        self.assertEquals(expected_items, self.run_xmlls('--versioned'))

    def test_lsxml_kinds(self):
        self.build_tree(['subdir/'])
        expected_items = [{'kind': 'file',
                           'path': '.bzrignore',
                           'status_kind': 'unknown'},
                          {'kind': 'file',
                           'path': 'a',
                           'status_kind': 'unknown'}]
        self.assertEquals(expected_items, self.run_xmlls('--kind=file'))
        expected_items = [{'kind': 'directory',
                           'path': 'subdir',
                           'status_kind': 'unknown'}]
        self.assertEquals(expected_items, self.run_xmlls('--kind=directory'))
        self.assertEquals([], self.run_xmlls('--kind=symlink'))
        self.run_bzr_error(['invalid kind specified'], 'xmlls --kind=pile')
