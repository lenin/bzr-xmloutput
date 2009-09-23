# Copyright (C) 2005, 2006 Canonical Ltd
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

"""Tests of status command.

Most of these depend on the particular formatting used.
As such they really are blackbox tests even though some of the
tests are not using self.capture. If we add tests for the programmatic
interface later, they will be non blackbox tests.
"""

from cStringIO import StringIO
import codecs
from os import mkdir, chdir, rmdir, unlink
import sys
from tempfile import TemporaryFile

from bzrlib import (
    bzrdir,
    conflicts,
    errors,
    osutils,
    )
import bzrlib.branch
from bzrlib.osutils import pathjoin
from bzrlib.revisionspec import RevisionSpec
from bzrlib.tests import TestCaseWithTransport, TestSkipped
from bzrlib.workingtree import WorkingTree
from bzrlib.xml_serializer import elementtree as elementtree

import bzrlib.plugin
from bzrlib.status import show_tree_status
fromstring = elementtree.ElementTree.fromstring
from elementtree_builder import (ET, _E)

## little hack to load functions from parent module
show_tree_status_xml = None
plugins = bzrlib.plugin.plugins()
for p in plugins:
    if getattr(plugins[p].module, 'plugin_name', None) is not None \
        and plugins[p].module.plugin_name == 'xmloutput':
        from sys import path
        import imp
        path.append(plugins[p].module.__path__[0])
        fp, pathname, description = imp.find_module('statusxml')
        show_tree_status_xml = imp.load_module('statusxml', fp, pathname,
            description).show_tree_status_xml

def create_xml(wt, status_dict):
    E = _E()
    status = E('status')
    status.attrib["workingtree_root"] = wt.id2abspath(wt.get_root_id())
    for key in status_dict.keys():
        status_kind = E(key)
        for file_kind, name, attributes in status_dict[key]:
            kind = E(file_kind, name)
            for attrib in attributes.keys():
                kind.attrib[attrib] = attributes[attrib]
            status_kind.append(kind)
        status.append(status_kind)
    return status

class TestXmlStatus(TestCaseWithTransport):

    def assertStatus(self, expected_xml_element, working_tree,
        revision=None, specific_files=None):
        """Run status in working_tree and look for output.

        :param expected_lines: The lines to look for.
        :param working_tree: The tree to run status in.
        """
        output_string = self.status_string(working_tree, revision,
            specific_files)
        output_elem = fromstring(output_string)
        self.assertEqual(len(output_elem.findall('added/*')),
            len(expected_xml_element.findall('added/*')))
        self.assertEqual(len(output_elem.findall('modified')),
            len(expected_xml_element.findall('modified')))
        self.assertEqual(len(output_elem.findall('unknown')),
            len(expected_xml_element.findall('unknown')))
        self.assertEqual(len(output_elem.findall('deleted')),
            len(expected_xml_element.findall('deleted')))
        self.assertEqual(len(output_elem.findall('renamed')),
            len(expected_xml_element.findall('renamed')))
        self.assertEqual(len(output_elem.findall('kind_changed')),
            len(expected_xml_element.findall('kind_changed')))
        self.assertEqual(len(output_elem.findall('removed')),
            len(expected_xml_element.findall('removed')))
        self.assertEqual(len(output_elem.findall('pending_merges')),
            len(expected_xml_element.findall('pending_merges')))
        self.assertEqual(len(output_elem.findall('conflicts')),
            len(expected_xml_element.findall('conflicts')))

    def status_string(self, wt, revision=None, specific_files=None):
        # use a real file rather than StringIO because it doesn't handle
        # Unicode very well.
        tof = codecs.getwriter('utf-8')(TemporaryFile())
        show_tree_status_xml(wt, to_file=tof, revision=revision, specific_files=specific_files)
        tof.seek(0)
        return tof.read().decode('utf-8')


class BranchStatus(TestXmlStatus):

    def test_branch_statusxml(self):
        """Test basic branch status"""
        wt = self.make_branch_and_tree('.')

        # status with no commits or files - it must
        # work and show no output. We do this with no
        # commits to be sure that it's not going to fail
        # as a corner case.
        self.assertStatus(create_xml(wt, {}), wt)

        self.build_tree(['hello.c', 'bye.c'])
        two_unknowns = create_xml(wt, {'unknown':[('file','bye.c', {}),
            ('file','hello.c', {})]})
        self.assertStatus(two_unknowns, wt)

        # add a commit to allow showing pending merges.
        wt.commit('create a parent to allow testing merge output')

        wt.add_parent_tree_id('pending@pending-0-0')
        with_pending_merges = create_xml(wt, {'unknown':[('file', 'bye.c', {}),
            ('file', 'hello.c', {})],
                'pending_merges':[('pending_merge','pending@pending-0-0', {})]})
        self.assertStatus(with_pending_merges, wt)

    def test_branch_statusxml_revisions(self):
        """Tests branch status with revisions"""
        wt = self.make_branch_and_tree('.')

        self.build_tree(['hello.c', 'bye.c'])
        wt.add('hello.c')
        wt.add('bye.c')
        wt.commit('Test message')

        revs = [RevisionSpec.from_string('0')]
        two_added = create_xml(wt, {'added':[('file', 'bye.c', {}),
            ('file', 'hello.c', {})]})
        self.assertStatus(two_added, wt, revision=revs)

        self.build_tree(['more.c'])
        wt.add('more.c')
        wt.commit('Another test message')

        revs.append(RevisionSpec.from_string('1'))
        self.assertStatus(two_added, wt, revision=revs)

    def test_pending_xml(self):
        """Pending merges display works, including Unicode"""
        mkdir("./branch")
        wt = self.make_branch_and_tree('branch')
        b = wt.branch
        wt.commit("Empty commit 1")
        b_2_dir = b.bzrdir.sprout('./copy')
        b_2 = b_2_dir.open_branch()
        wt2 = b_2_dir.open_workingtree()
        wt.commit(u"\N{TIBETAN DIGIT TWO} Empty commit 2")
        wt2.merge_from_branch(wt.branch)
        message = self.status_string(wt2)
        messageElem = fromstring(message.encode('utf-8','replace'))
        self.assertEquals(1, len(messageElem.findall('pending_merges')))
        self.assertEquals(1, len(messageElem.findall('pending_merges/log')))
        self.assertEndsWith(
            messageElem.findall('pending_merges/log/message')[0].text,
            "Empty commit 2")
        wt2.commit("merged")
        # must be long to make sure we see elipsis at the end
        wt.commit("Empty commit 3 " +
                   "blah blah blah blah " * 100)
        wt2.merge_from_branch(wt.branch)
        message = self.status_string(wt2)
        messageElem = fromstring(message)
        self.assertEquals(1, len(messageElem.findall('pending_merges')))
        self.assert_("Empty commit 3" in \
            messageElem.findall('pending_merges/log/message')[0].text)

    def test_tree_statusxml_ignores(self):
        """Tests branch status with ignores"""
        wt = self.make_branch_and_tree('.')
        self.run_bzr('ignore *~')
        wt.commit('commit .bzrignore')
        self.build_tree(['foo.c', 'foo.c~'])
        one_unknown = create_xml(wt, {'unknown':[('file','foo.c', {})]})
        self.assertStatus(one_unknown, wt)

    def test_tree_statusxml_specific_files(self):
        """Tests branch status with given specific files"""
        wt = self.make_branch_and_tree('.')
        b = wt.branch

        self.build_tree(['directory/','directory/hello.c',
            'bye.c','test.c','dir2/'])
        wt.add('directory')
        wt.add('test.c')
        wt.commit('testing')

        xml_status = create_xml(wt, {'unknown':[('file','bye.c', {}),
            ('directory', 'dir2', {}), ('file', 'directory/hello.c', {})]})
        self.assertStatus(xml_status, wt)

        tof = StringIO()
        show_tree_status_xml(wt, specific_files=['bye.c','test.c','absent.c'], to_file=tof)
        log_xml = fromstring(tof.getvalue())
        nonexistents = log_xml.findall('nonexistents/nonexistent')
        unknowns = log_xml.findall('unknown')
        self.assertEquals(1, len(nonexistents))
        self.assertEquals(1, len(unknowns))

        self.assertStatus(create_xml(wt, {'unknown':[('file',
            'directory/hello.c', {})]}), wt, specific_files=['directory'])

        self.assertStatus(create_xml(wt, {'unknown':[('directory',
            'dir2', {})]}), wt, specific_files=['dir2'])

        revs = [RevisionSpec.from_string('0'), RevisionSpec.from_string('1')]
        self.assertStatus(create_xml(wt, {'added':[('file', 'test.c', {})]}),
            wt, revs, specific_files=['test.c'])

    def test_specific_files_conflicts_xml(self):
        tree = self.make_branch_and_tree('.')
        self.build_tree(['dir2/'])
        tree.add('dir2')
        tree.commit('added dir2')
        tree.set_conflicts(conflicts.ConflictList(
            [conflicts.ContentsConflict('foo')]))
        self.assertStatus(create_xml(tree, {}), tree, specific_files=['dir2'])

        tree.set_conflicts(conflicts.ConflictList(
            [conflicts.ContentsConflict('dir2')]))
        self.assertStatus(create_xml(tree,
            {'conflicts':[('directory','dir2', {})]}),
            tree, specific_files=['dir2'])

        tree.set_conflicts(conflicts.ConflictList(
            [conflicts.ContentsConflict('dir2/file1')]))
        self.assertStatus(create_xml(tree,
            {'conflicts':[('file','dir2/file1', {})]}),
            tree, specific_files=['dir2'])

    def test_statusxml_nonexistent_file(self):
        # files that don't exist in either the basis tree or working tree
        # should give an error
        wt = self.make_branch_and_tree('.')
        out, err = self.run_bzr('xmlstatus does-not-exist')
        log_xml = fromstring(out)
        status = log_xml.findall('nonexistents/nonexistent')
        self.assertEquals(1, len([elem for elem in status]))
        self.assertEquals(status[0].text, 'does-not-exist')

    def test_statusxml_out_of_date(self):
        """Simulate status of out-of-date tree after remote push"""
        # TODO: implement this error handling in xml specific way?
        tree = self.make_branch_and_tree('.')
        self.build_tree_contents([('a', 'foo\n')])
        tree.lock_write()
        try:
            tree.add(['a'])
            tree.commit('add test file')
            # simulate what happens after a remote push
            tree.set_last_revision("0")
        finally:
            # before run another commands we should unlock tree
            tree.unlock()
        out, err = self.run_bzr('status')
        self.assertEqual("working tree is out of date, run 'bzr update'\n",
                         err)


class CheckoutStatus(BranchStatus):

    def setUp(self):
        super(CheckoutStatus, self).setUp()
        mkdir('codir')
        chdir('codir')

    def make_branch_and_tree(self, relpath):
        source = self.make_branch(pathjoin('..', relpath))
        checkout = bzrdir.BzrDirMetaFormat1().initialize(relpath)
        bzrlib.branch.BranchReferenceFormat().initialize(checkout, source)
        return checkout.create_workingtree()


class TestStatus(TestCaseWithTransport):

    def test_statusxml_plain(self):
        tree = self.make_branch_and_tree('.')

        self.build_tree(['hello.txt'])
        result = fromstring(self.run_bzr("xmlstatus")[0])
        self.assertEquals(result.findall('unknown/file')[0].text, "hello.txt")

        tree.add("hello.txt")
        result = fromstring(self.run_bzr("xmlstatus")[0])
        self.assertEquals(result.findall('added/file')[0].text, "hello.txt")

        tree.commit(message="added")
        result = fromstring(self.run_bzr("xmlstatus -r 0..1")[0])
        self.assertEquals(result.findall('added/file')[0].text, "hello.txt")

        result = fromstring(self.run_bzr("xmlstatus -c 1")[0])
        self.assertEquals(result.findall('added/file')[0].text, "hello.txt")

        self.build_tree(['world.txt'])
        result = fromstring(self.run_bzr("xmlstatus -r 0")[0])
        self.assertEquals(result.findall('added/file')[0].text, "hello.txt")
        self.assertEquals(result.findall('unknown/file')[0].text, "world.txt")

        result2 = fromstring(self.run_bzr("xmlstatus -r 0..")[0])
        self.assertEquals(elementtree.ElementTree.tostring(result2),
            elementtree.ElementTree.tostring(result))

    def test_statusxml_versioned(self):
        tree = self.make_branch_and_tree('.')

        self.build_tree(['hello.txt'])
        result = fromstring(self.run_bzr("xmlstatus --versioned")[0])
        self.assert_(len(result.findall('unknown/*')) == 0)

        tree.add("hello.txt")
        result = fromstring(self.run_bzr("xmlstatus --versioned")[0])
        self.assertEquals(result.findall('added/file')[0].text, "hello.txt")

        tree.commit("added")
        result = fromstring(self.run_bzr("xmlstatus --versioned -r 0..1")[0])
        self.assertEquals(result.findall('added/file')[0].text, "hello.txt")

        self.build_tree(['world.txt'])
        result = fromstring(self.run_bzr("xmlstatus --versioned -r 0")[0])
        self.assertEquals(result.findall('added/file')[0].text, "hello.txt")
        self.assert_(len(result.findall('unknown/*')) == 0)

        result2 = fromstring(self.run_bzr("xmlstatus --versioned -r 0..")[0])
        self.assertEquals(elementtree.ElementTree.tostring(result2),
            elementtree.ElementTree.tostring(result))

    # Not yet implemneted
    #def assertStatusContains(self, xpath):
    #    """Run status, and assert it contains the given attribute at the
    #       given element"""
    #    for key in changes.keys():
    #        status_kind = E(key)
    #        for file_kind, name, attributes in status_dict[key]:
    #            kind = E(file_kind, name)
    #            for attrib in attributes.keys():
    #                kind.attrib[attrib] = attributes[attrib]
    #            status_kind.append(kind)
    #        status.append(status_kind)
    #    return status

    #    result = fromstring(self.run_bzr("xmlstatus")[0])
    #    result = self.run_bzr("xmlstatus")[0]
    #    self.assertContainsRe(result, pattern)

    def test_kind_change_xml(self):
        tree = self.make_branch_and_tree('.')
        self.build_tree(['file'])
        tree.add('file')
        tree.commit('added file')
        unlink('file')
        self.build_tree(['file/'])
        #self.assertStatusContains('K  file => file/')
        result = fromstring(self.run_bzr("xmlstatus")[0])
        self.assert_(result.findall('kind_changed/*')[0].attrib['oldkind'] == 'file')
        self.assert_(result.findall('kind_changed/*')[0].tag == 'directory')
        tree.rename_one('file', 'directory')
        result = fromstring(self.run_bzr("xmlstatus")[0])
        self.assert_(result.findall('renamed/directory')[0].attrib['oldpath'] == 'file')
        self.assert_(result.findall('renamed/directory')[0].text == 'directory')
        #self.assertStatusContains('RK  file => directory/')
        rmdir('directory')
        result = fromstring(self.run_bzr("xmlstatus")[0])
        self.assert_(result.findall('removed/*')[0].text == 'file')
        #self.assertStatusContains('RD  file => directory')

    def test_statusxml_illegal_revision_specifiers(self):
        out, err = self.run_bzr('status -r 1..23..123', retcode=3)
        self.assertContainsRe(err, 'one or two revision specifiers')


class TestXmlStatusEncodings(TestXmlStatus):

    def setUp(self):
        TestCaseWithTransport.setUp(self)
        self.old_user_encoding = osutils._cached_user_encoding
        self.old_get_user_encoding = osutils.get_user_encoding
        self.stdout = sys.stdout

    def tearDown(self):
        osutils._cached_user_encoding = self.old_user_encoding
        if hasattr(bzrlib, 'user_encoding'):
            bzrlib.user_encoding = self.old_user_encoding
        osutils._cached_user_encoding = self.old_user_encoding
        osutils.get_user_encoding = self.old_get_user_encoding
        sys.stdout = self.stdout
        TestCaseWithTransport.tearDown(self)

    def make_uncommitted_tree(self):
        """Build a branch with uncommitted unicode named changes in the cwd."""
        working_tree = self.make_branch_and_tree(u'.')
        filename = u'hell\u00d8'
        try:
            self.build_tree_contents([(filename, 'contents of hello')])
        except UnicodeEncodeError:
            raise TestSkipped("can't build unicode working tree in "
                "filesystem encoding %s" % sys.getfilesystemencoding())
        working_tree.add(filename)
        return working_tree

    def test_stdout_ascii_xml(self):
        sys.stdout = StringIO()
        osutils._cached_user_encoding = 'ascii'
        bzrlib.osutils.get_user_encoding = lambda: 'ascii'
        if hasattr(bzrlib, 'user_encoding'):
            bzrlib.user_encoding = 'ascii'
        working_tree = self.make_uncommitted_tree()
        stdout, stderr = self.run_bzr("xmlstatus")
        messageElem = fromstring(stdout)
        self.assertEquals(messageElem.findall('added/file')[0].text, "hell?")

