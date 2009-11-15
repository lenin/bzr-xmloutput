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
        # parse the output and convert it into a list structure:
        #   [ [ kind, path, status_kind ], ... ]
        lst = fromstring(out)
        items = lst.findall('item')
        return [[i.find('kind').text,
                 i.find('path').text,
                 i.find('status_kind').text] for i in items]
        
    #def test_lsxml_null_verbose(self):
    #    # Can't supply both
    #    self.run_bzr_error(['Cannot set both --verbose and --null'],
    #                       'xmlls --verbose --null')

    def test_lsxml_basic(self):
        """Test the abilities of 'bzr xmlls'"""
        expected_files = [['file', '.bzrignore', 'unknown'],
            ['file', 'a', 'unknown']]
        self.assertEquals(expected_files, self.run_xmlls())
        self.assertEquals(expected_files, self.run_xmlls('--unknown'))
        self.assertEquals([], self.run_xmlls('--ignored'))
        self.assertEquals([], self.run_xmlls('--versioned'))
        self.assertEquals([], self.run_xmlls('-V'))
        self.assertEquals(expected_files,
                          self.run_xmlls('--unknown --ignored --version'))
        self.assertEquals(expected_files,
                          self.run_xmlls('--unknown --ignored -V'))
        self.assertEquals([], self.run_xmlls('--ignored -V'))

    def test_lsxml_added(self):
        self.wt.add(['a'])
        expected_files = [['file', '.bzrignore', 'unknown'],
            ['file', 'a', 'versioned']]
        self.assertEquals(expected_files, self.run_xmlls())
        
        self.wt.commit('add')
        self.build_tree(['subdir/'])
        expected_files = [['file', '.bzrignore', 'unknown'],
            ['file', 'a', 'versioned'],
            ['directory', 'subdir', 'unknown']]
        self.assertEquals(expected_files, self.run_xmlls())
        
        self.build_tree(['subdir/b'])
        self.wt.add(['subdir/', 'subdir/b', '.bzrignore'])
        expected_files = [['file', '.bzrignore', 'versioned'],
            ['file', 'a', 'versioned'],
            ['directory', 'subdir', 'versioned'],
            ['file', 'subdir/b', 'versioned']]
        self.assertEquals(expected_files, self.run_xmlls())
