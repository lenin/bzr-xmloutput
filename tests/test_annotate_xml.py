# Copyright (C) 2005 Canonical Ltd
# -*- coding: utf-8 -*-
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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


"""Black-box tests for bzr.

These check that it behaves properly when it's invoked through the regular
command-line interface. This doesn't actually run a new interpreter but
rather starts again from the run_bzr function.
"""


import os
import time
import bzrlib

from bzrlib.tests import TestCaseWithTransport
from bzrlib.xml_serializer import elementtree as elementtree
fromstring = elementtree.fromstring

class TestXmlAnnotate(TestCaseWithTransport):

    def setUp(self):
        super(TestXmlAnnotate, self).setUp()
        self.wt = self.make_branch_and_tree('.')
        b = self.wt.branch
        self.build_tree_contents([('hello.txt', 'my helicopter\n'),
                                  ('nomail.txt', 'nomail\n')])
        self.wt.add(['hello.txt'])
        self.revision_id_1 = self.wt.commit('add hello',
                              committer='test@user',
                              timestamp=1165960000.00, timezone=0)
        self.wt.add(['nomail.txt'])
        self.revision_id_2 = self.wt.commit('add nomail',
                              committer='no mail',
                              timestamp=1165970000.00, timezone=0)
        self.build_tree_contents([('hello.txt', 'my helicopter\n'
                                                'your helicopter\n')])
        self.revision_id_3 = self.wt.commit('mod hello',
                              committer='user@test',
                              timestamp=1166040000.00, timezone=0)
        self.build_tree_contents([('hello.txt', 'my helicopter\n'
                                                'your helicopter\n'
                                                'all of\n'
                                                'our helicopters\n'
                                  )])
        self.revision_id_4 = self.wt.commit('mod hello',
                              committer='user@test',
                              timestamp=1166050000.00, timezone=0)
        self.time_revision_id_1 = date_str = time.strftime('%Y%m%d',
                                     time.gmtime(1165960000.00))
        self.time_revision_id_2 = date_str = time.strftime('%Y%m%d',
                                     time.gmtime(1165970000.00))
        self.time_revision_id_3 = date_str = time.strftime('%Y%m%d',
                                     time.gmtime(1166040000.00))
        self.time_revision_id_4 = date_str = time.strftime('%Y%m%d',
                                     time.gmtime(1166050000.00))

    def test_help_xmlannotate(self):
        """XmlAnnotate command exists"""
        out, err = self.run_bzr('xmlannotate --help')

    def test_xmlannotate_cmd(self):
        out, err = self.run_bzr('xmlannotate hello.txt')
        wt_root_path = self.wt.id2abspath(self.wt.get_root_id())
        expected_xml = (''.join(['<?xml version="1.0"?>',
                        '<annotation workingtree-root="%s" file="hello.txt">',
                        '<entry revno="1" author="test@user" date="%s">my helicopter</entry>',
                        '<entry revno="3" author="user@test" date="%s">your helicopter</entry>',
                        '<entry revno="4" author="user@test" date="%s">all of</entry>',
                        '<entry revno="4" author="user@test" date="%s">our helicopters</entry>',
                        '</annotation>\n',]) %
                        (wt_root_path, self.time_revision_id_1, self.time_revision_id_3,
                         self.time_revision_id_4, self.time_revision_id_4))
        #TODO: assert xml and elementree (including attributes)
        self.assertEqual('', err)
        self.assertEqualDiff(expected_xml, out)
        expected_elementtree = fromstring(expected_xml)
        current_elementtree = fromstring(out)
        self.assertEquals(elementtree.tostring(expected_elementtree),
                elementtree.tostring(current_elementtree))

    def test_xmlannotate_cmd_show_ids(self):
        out, err = self.run_bzr('xmlannotate hello.txt --show-ids')
        wt_root_path = self.wt.id2abspath(self.wt.get_root_id())

        expected_xml = (''.join(['<?xml version="1.0"?>',
                                '<annotation workingtree-root="%s" file="hello.txt">',
                                '<entry revno="1" author="test@user" date="%s"',
                                ' fid="%s">my helicopter</entry>',
                                '<entry revno="3" author="user@test" date="%s"',
                                ' fid="%s">your helicopter</entry>',
                                '<entry revno="4" author="user@test" date="%s"',
                                ' fid="%s">all of</entry>',
                                '<entry revno="4" author="user@test" date="%s"',
                                ' fid="%s">our helicopters</entry>',
                                '</annotation>\n',]) %
                                (wt_root_path,
                                self.time_revision_id_1, self.revision_id_1,
                                self.time_revision_id_3, self.revision_id_3,
                                self.time_revision_id_4, self.revision_id_4,
                                self.time_revision_id_4, self.revision_id_4))
        #TODO: assert xml and elementree (including attributes)
        max_len = max([len(self.revision_id_1),
                       len(self.revision_id_3),
                       len(self.revision_id_4)])
        self.assertEqual('', err)
        self.assertEqualDiff(expected_xml, out)
        #        self.assertEqualDiff('''\
        #%*s | my helicopter
        #%*s | your helicopter
        #%*s | all of
        #%*s | our helicopters
        #''' % (max_len, self.revision_id_1,
        #max_len, self.revision_id_3,
        #max_len, self.revision_id_4,
        #max_len, '',
        #)
        #, out)

    def test_no_mail(self):
        out, err = self.run_bzr('xmlannotate nomail.txt')
        wt_root_path = self.wt.id2abspath(self.wt.get_root_id())
        expected_xml = (''.join(['<?xml version="1.0"?>',
                        '<annotation workingtree-root="%s" file="nomail.txt">',
                        '<entry revno="2" author="no mail" date="%s">nomail</entry>',
                        '</annotation>\n']) % (wt_root_path, self.time_revision_id_2))
        #TODO: assert xml and elementree (including attributes)
        self.assertEqual('', err)
        self.assertEqualDiff(expected_xml, out)
        #        self.assertEqualDiff('''\
        #2   no mail | nomail
        #''', out)

    def test_xmlannotate_cmd_revision(self):
        out, err = self.run_bzr('xmlannotate hello.txt -r1')
        wt_root_path = self.wt.id2abspath(self.wt.get_root_id())
        expected_xml = (''.join(['<?xml version="1.0"?>',
                                '<annotation workingtree-root="%s" file="hello.txt">',
                                '<entry revno="1" author="test@user" date="%s">my helicopter</entry>',
                                '</annotation>\n']) % (wt_root_path,
                                                    self.time_revision_id_1))
        #TODO: assert xml and elementree (including attributes)
        self.assertEqual('', err)
        self.assertEqualDiff(expected_xml, out)
        #self.assertEqualDiff('''\
        #1   test@us | my helicopter
        #''', out)

    def test_xmlannotate_cmd_revision3(self):
        out, err = self.run_bzr('xmlannotate hello.txt -r3')
        wt_root_path = self.wt.id2abspath(self.wt.get_root_id())
        expected_xml = (''.join(['<?xml version="1.0"?>',
                                '<annotation workingtree-root="%s" file="hello.txt">',
                                '<entry revno="1" author="test@user" date="%s">my helicopter</entry>',
                                '<entry revno="3" author="user@test" date="%s">your helicopter</entry>',
                                '</annotation>\n'])  % (wt_root_path,
                                                     self.time_revision_id_1,
                                                     self.time_revision_id_3))
        #TODO: assert xml and elementree (including attributes)
        self.assertEqual('', err)
        self.assertEqualDiff(expected_xml, out)
        #        self.assertEqualDiff('''\
        #1   test@us | my helicopter
        #3   user@te | your helicopter
        #''', out)

    def test_xmlannotate_cmd_unknown_revision(self):
        out, err = self.run_bzr('xmlannotate hello.txt -r 10',
                                retcode=3)
        self.assertEqual('', out)
        self.assertContainsRe(err, 'Requested revision: \'10\' does not exist')

    def test_xmlannotate_cmd_two_revisions(self):
        out, err = self.run_bzr('xmlannotate hello.txt -r1..2',
                                retcode=3)
        self.assertEqual('', out)
        self.assertEqual('<?xml version="1.0" encoding="%s"?><error><class>'
                'BzrCommandError</class><dict><key>_preformatted_string</key><value>xmlannotate'
                ' --revision takes exactly 1 argument</value></dict><message>'
                'xmlannotate --revision takes exactly 1 argument</message>'
                '</error>' % bzrlib.osutils.get_user_encoding(), err)

    def test_xmlannotate_empty_file(self):
        tree = self.make_branch_and_tree('tree')
        self.build_tree_contents([('tree/empty', '')])
        tree.add('empty')
        tree.commit('add empty file')

        os.chdir('tree')
        out, err = self.run_bzr('xmlannotate empty')
        wt_root_path = self.wt.id2abspath(self.wt.get_root_id())
        #TODO: assert xml and elementree (including attributes)'
        expected_xml = (''.join(['<?xml version="1.0"?>',
                                '<annotation workingtree-root="%s" file="empty">',
                                '</annotation>\n']) % (wt_root_path+'tree/',))
        self.assertEqual(expected_xml, out)

    def test_xmlannotate_nonexistant_file(self):
        tree = self.make_branch_and_tree('tree')
        self.build_tree(['tree/file'])
        tree.add(['file'])
        tree.commit('add a file')

        os.chdir('tree')
        out, err = self.run_bzr("xmlannotate doesnotexist", retcode=3)
        self.assertEqual('', out)
        self.assertContainsRe(err, '<error><class>NotVersionedError.*'
                '<dict><key>path.*<value>doesnotexist'
                '.*<message>doesnotexist is not versioned.</message></error>')
