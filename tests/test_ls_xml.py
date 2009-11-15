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
