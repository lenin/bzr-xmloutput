# -*- encoding: utf-8 -*-
#
# Copyright (C) 2006, 2007 Canonical Ltd
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


"""Tests for the info command of bzr."""

import os
import sys

import bzrlib
from bzrlib import (
    bzrdir,
    errors,
    osutils,
    repository,
    tests,
    urlutils,
    upgrade,
    )
from bzrlib.tests import blackbox


class TestInfoXml(blackbox.ExternalBase):

    def test_should_normalize_non_ascii_url(self):
        # we disable isolation because the error we want to catch is triggered
        # outside of the jail
        self.disable_directory_isolation()
        root = '/C:' if sys.platform == 'win32' else ''
        url = u'file://%s/Maçã/does/not/exist' % root
        out, err = self.run_bzr(['xmlinfo', url], retcode=3)
        from bzrlib.urlutils import normalize_url
        nurl = normalize_url(url)
        self.assertEqual(
            '<?xml version="1.0" encoding="%s"?>'
            '<error><class>NotBranchError</class><dict><key>path</key>'
            '<value>%s/</value><key>extra</key><value></value>'
            '<key>detail</key><value></value></dict>'
            '<message>Not a branch: "%s/".</message>'
            '</error>' % (osutils.get_user_encoding(), nurl, nurl), err)


    def test_info_non_existing(self):
        # we disable isolation because the error we want to catch is triggered
        # outside of the jail
        self.disable_directory_isolation()
        if sys.platform == "win32":
            location = "C:/i/do/not/exist/"
        else:
            location = "/i/do/not/exist/"
        out, err = self.run_bzr('xmlinfo '+location, retcode=3)
        self.assertEqual(out, '')
        self.assertEqual(
            '<?xml version="1.0" encoding="%s"?><error>'
            '<class>NotBranchError</class><dict><key>path</key><value>'
            '%s</value><key>extra</key><value></value>'
            '<key>detail</key><value></value></dict>'
            '<message>Not a branch: "%s".</message>'
            '</error>' % (osutils.get_user_encoding(),
                          location, location), err)

    def test_info_standalone(self):
        transport = self.get_transport()

        # Create initial standalone branch
        tree1 = self.make_branch_and_tree('standalone', 'weave')
        self.build_tree(['standalone/a'])
        tree1.add('a')
        branch1 = tree1.branch

        out, err = self.run_bzr('xmlinfo standalone')
        expected_xml = '''<?xml version="1.0"?>
<info>
<layout>Standalone tree</layout>
<formats>
<format>weave</format>
</formats>
<location>
<branch_root>standalone</branch_root></location>
</info>

'''
        expected_xml = ''.join(expected_xml.split('\n'))+'\n'
        self.assertEqualDiff(expected_xml, out)
        self.assertEqual('', err)

        out, err = self.run_bzr('xmlinfo standalone -v')
        expected_xml = '''<?xml version="1.0"?>
<info>
<layout>Standalone tree</layout>
<formats>
<format>weave</format>
</formats>
<location>
<branch_root>standalone</branch_root></location>
<format>
<control>All-in-one format 6</control>
<working_tree>Working tree format 2</working_tree>
<branch>Branch format 4</branch>
<repository>Weave repository format 6</repository>
</format>
<working_tree_stats>
<unchanged>0</unchanged>
<modified>0</modified>
<added>1</added>
<removed>0</removed>
<renamed>0</renamed>
<unknown>0</unknown>
<ignored>0</ignored>
<versioned_subdirectories>0</versioned_subdirectories>
</working_tree_stats>
<branch_history>
<revisions>0</revisions>
<committers>0</committers>
</branch_history>
<repository_stats>
<revisions>0</revisions>
</repository_stats>
</info>

'''
        expected_xml = ''.join(expected_xml.split('\n'))+'\n'
        self.assertEqualDiff(expected_xml, out)
        self.assertEqual('', err)
        tree1.commit('commit one')
        rev = branch1.repository.get_revision(branch1.revision_history()[0])
        datestring_first = osutils.format_date(rev.timestamp, rev.timezone)

        # Branch standalone with push location
        branch2 = branch1.bzrdir.sprout('branch').open_branch()
        branch2.set_push_location(branch1.bzrdir.root_transport.base)

        out, err = self.run_bzr('xmlinfo branch')
        expected_xml = '''<?xml version="1.0"?>
<info>
<layout>Standalone tree</layout>
<formats>
<format>weave</format>
</formats>
<location>
<branch_root>branch</branch_root></location>
<related_branches>
<push_branch>standalone</push_branch><parent_branch>standalone</parent_branch></related_branches>
</info>

'''
        expected_xml = ''.join(expected_xml.split('\n'))+'\n'
        self.assertEqualDiff(expected_xml, out)
        self.assertEqual('', err)

        out, err = self.run_bzr('xmlinfo branch --verbose')
        expected_xml = '''<?xml version="1.0"?>
<info>
<layout>Standalone tree</layout>
<formats>
<format>weave</format>
</formats>
<location>
<branch_root>branch</branch_root></location>
<related_branches>
<push_branch>standalone</push_branch><parent_branch>standalone</parent_branch></related_branches>
<format>
<control>All-in-one format 6</control>
<working_tree>Working tree format 2</working_tree>
<branch>Branch format 4</branch>
<repository>Weave repository format 6</repository>
</format>
<working_tree_stats>
<unchanged>1</unchanged>
<modified>0</modified>
<added>0</added>
<removed>0</removed>
<renamed>0</renamed>
<unknown>0</unknown>
<ignored>0</ignored>
<versioned_subdirectories>0</versioned_subdirectories>
</working_tree_stats>
<branch_history>
<revisions>1</revisions>
<committers>1</committers>
<days_old>0</days_old>
<first_revision>%s</first_revision>
<latest_revision>%s</latest_revision>
</branch_history>
<repository_stats>
<revisions>1</revisions>
</repository_stats>
</info>

''' % (datestring_first, datestring_first,
       )
        expected_xml = ''.join(expected_xml.split('\n'))+'\n'
        self.assertEqualDiff(expected_xml, out)
        self.assertEqual('', err)

        # Branch and bind to standalone, needs upgrade to metadir
        # (creates backup as unknown)
        branch1.bzrdir.sprout('bound')
        knit1_format = bzrdir.format_registry.make_bzrdir('knit')
        bzrlib.upgrade.upgrade('bound', knit1_format)
        branch3 = bzrlib.bzrdir.BzrDir.open('bound').open_branch()
        branch3.bind(branch1)
        bound_tree = branch3.bzrdir.open_workingtree()
        out, err = self.run_bzr('xmlinfo -v bound')
        expected_xml = '''<?xml version="1.0"?>
<info>
<layout>Checkout</layout>
<formats>
<format>knit</format>
</formats>
<location>
<checkout_root>bound</checkout_root><checkout_of_branch>standalone</checkout_of_branch></location>
<related_branches>
<parent_branch>standalone</parent_branch></related_branches>
<format>
<control>Meta directory format 1</control>
<working_tree>%s</working_tree>
<branch>%s</branch>
<repository>%s</repository>
</format>
<working_tree_stats>
<unchanged>1</unchanged>
<modified>0</modified>
<added>0</added>
<removed>0</removed>
<renamed>0</renamed>
<unknown>0</unknown>
<ignored>1</ignored>
<versioned_subdirectories>0</versioned_subdirectories>
</working_tree_stats>
<branch_history>
<revisions>1</revisions>
<committers>1</committers>
<days_old>0</days_old>
<first_revision>%s</first_revision>
<latest_revision>%s</latest_revision>
</branch_history>
<repository_stats>
<revisions>1</revisions>
</repository_stats>
</info>

''' % (bound_tree._format.get_format_description(),
       branch3._format.get_format_description(),
       branch3.repository._format.get_format_description(),
       datestring_first, datestring_first,
       )
        expected_xml = ''.join(expected_xml.split('\n'))+'\n'
        self.assertEqualDiff(expected_xml, out)
        self.assertEqual('', err)

        # Checkout standalone (same as above, but does not have parent set)
        branch4 = bzrlib.bzrdir.BzrDir.create_branch_convenience('checkout',
            format=knit1_format)
        branch4.bind(branch1)
        branch4.bzrdir.open_workingtree().update()
        out, err = self.run_bzr('xmlinfo checkout --verbose')
        expected_xml = '''<?xml version="1.0"?>
<info>
<layout>Checkout</layout>
<formats>
<format>knit</format>
</formats>
<location>
<checkout_root>checkout</checkout_root><checkout_of_branch>standalone</checkout_of_branch></location>
<format>
<control>Meta directory format 1</control>
<working_tree>Working tree format 3</working_tree>
<branch>Branch format 5</branch>
<repository>%s</repository>
</format>
<working_tree_stats>
<unchanged>1</unchanged>
<modified>0</modified>
<added>0</added>
<removed>0</removed>
<renamed>0</renamed>
<unknown>0</unknown>
<ignored>0</ignored>
<versioned_subdirectories>0</versioned_subdirectories>
</working_tree_stats>
<branch_history>
<revisions>1</revisions>
<committers>1</committers>
<days_old>0</days_old>
<first_revision>%s</first_revision>
<latest_revision>%s</latest_revision>
</branch_history>
<repository_stats>
<revisions>1</revisions>
</repository_stats>
</info>

''' % (branch4.repository._format.get_format_description(),
       datestring_first, datestring_first,
       )
        expected_xml = ''.join(expected_xml.split('\n'))+'\n'
        self.assertEqualDiff(expected_xml , out)
        self.assertEqual('', err)

        # Lightweight checkout (same as above, different branch and repository)
        tree5 = branch1.create_checkout('lightcheckout', lightweight=True)
        branch5 = tree5.branch
        out, err = self.run_bzr('xmlinfo -v lightcheckout')
        expected_xml = '''<?xml version="1.0"?>
<info>
<layout>Lightweight checkout</layout>
<formats>
<format>2a</format>
</formats>
<location>
<light_checkout_root>lightcheckout</light_checkout_root><checkout_of_branch>standalone</checkout_of_branch></location>
<format>
<control>Meta directory format 1</control>
<working_tree>Working tree format 6</working_tree>
<branch>Branch format 4</branch>
<repository>Weave repository format 6</repository>
</format>
<working_tree_stats>
<unchanged>1</unchanged>
<modified>0</modified>
<added>0</added>
<removed>0</removed>
<renamed>0</renamed>
<unknown>0</unknown>
<ignored>0</ignored>
<versioned_subdirectories>0</versioned_subdirectories>
</working_tree_stats>
<branch_history>
<revisions>1</revisions>
<committers>1</committers>
<days_old>0</days_old>
<first_revision>%s</first_revision>
<latest_revision>%s</latest_revision>
</branch_history>
<repository_stats>
<revisions>1</revisions>
</repository_stats>
</info>

''' % (datestring_first, datestring_first)
        expected_xml = ''.join(expected_xml.split('\n'))+'\n'
        self.assertEqualDiff(expected_xml, out)
        self.assertEqual('', err)

        # Update initial standalone branch
        self.build_tree(['standalone/b'])
        tree1.add('b')
        tree1.commit('commit two')
        rev = branch1.repository.get_revision(branch1.revision_history()[-1])
        datestring_last = osutils.format_date(rev.timestamp, rev.timezone)

        # Out of date branched standalone branch will not be detected
        out, err = self.run_bzr('xmlinfo -v branch')
        expected_xml = '''<?xml version="1.0"?>
<info>
<layout>Standalone tree</layout>
<formats>
<format>weave</format>
</formats>
<location>
<branch_root>branch</branch_root></location>
<related_branches>
<push_branch>standalone</push_branch><parent_branch>standalone</parent_branch></related_branches>
<format>
<control>All-in-one format 6</control>
<working_tree>Working tree format 2</working_tree>
<branch>Branch format 4</branch>
<repository>Weave repository format 6</repository>
</format>
<working_tree_stats>
<unchanged>1</unchanged>
<modified>0</modified>
<added>0</added>
<removed>0</removed>
<renamed>0</renamed>
<unknown>0</unknown>
<ignored>0</ignored>
<versioned_subdirectories>0</versioned_subdirectories>
</working_tree_stats>
<branch_history>
<revisions>1</revisions>
<committers>1</committers>
<days_old>0</days_old>
<first_revision>%s</first_revision>
<latest_revision>%s</latest_revision>
</branch_history>
<repository_stats>
<revisions>1</revisions>
</repository_stats>
</info>

''' % (datestring_first, datestring_first,)
        expected_xml = ''.join(expected_xml.split('\n'))+'\n'
        self.assertEqualDiff(expected_xml, out)
        self.assertEqual('', err)

        # Out of date bound branch
        out, err = self.run_bzr('xmlinfo -v bound')
        expected_xml = '''<?xml version="1.0"?>
<info>
<layout>Checkout</layout>
<formats>
<format>knit</format>
</formats>
<location>
<checkout_root>bound</checkout_root><checkout_of_branch>standalone</checkout_of_branch></location>
<related_branches>
<parent_branch>standalone</parent_branch></related_branches>
<format>
<control>Meta directory format 1</control>
<working_tree>Working tree format 3</working_tree>
<branch>Branch format 5</branch>
<repository>%s</repository>
</format>
<branch_stats>
<missing_revisions>1<missing_revisions>
</branch_stats>
<working_tree_stats>
<unchanged>1</unchanged>
<modified>0</modified>
<added>0</added>
<removed>0</removed>
<renamed>0</renamed>
<unknown>0</unknown>
<ignored>1</ignored>
<versioned_subdirectories>0</versioned_subdirectories>
</working_tree_stats>
<branch_history>
<revisions>1</revisions>
<committers>1</committers>
<days_old>0</days_old>
<first_revision>%s</first_revision>
<latest_revision>%s</latest_revision>
</branch_history>
<repository_stats>
<revisions>1</revisions>
</repository_stats>
</info>

''' % (branch3.repository._format.get_format_description(),
       datestring_first, datestring_first,
       )
        expected_xml = ''.join(expected_xml.split('\n'))+'\n'
        self.assertEqualDiff(expected_xml, out)
        self.assertEqual('', err)

        # Out of date checkout
        out, err = self.run_bzr('xmlinfo -v checkout')
        expected_xml = '''<?xml version="1.0"?>
<info>
<layout>Checkout</layout>
<formats>
<format>knit</format>
</formats>
<location>
<checkout_root>checkout</checkout_root><checkout_of_branch>standalone</checkout_of_branch></location>
<format>
<control>Meta directory format 1</control>
<working_tree>Working tree format 3</working_tree>
<branch>Branch format 5</branch>
<repository>%s</repository>
</format>
<branch_stats>
<missing_revisions>1<missing_revisions>
</branch_stats>
<working_tree_stats>
<unchanged>1</unchanged>
<modified>0</modified>
<added>0</added>
<removed>0</removed>
<renamed>0</renamed>
<unknown>0</unknown>
<ignored>0</ignored>
<versioned_subdirectories>0</versioned_subdirectories>
</working_tree_stats>
<branch_history>
<revisions>1</revisions>
<committers>1</committers>
<days_old>0</days_old>
<first_revision>%s</first_revision>
<latest_revision>%s</latest_revision>
</branch_history>
<repository_stats>
<revisions>1</revisions>
</repository_stats>
</info>

''' % (branch4.repository._format.get_format_description(),
       datestring_first, datestring_first,
       )
        expected_xml = ''.join(expected_xml.split('\n'))+'\n'
        self.assertEqualDiff(expected_xml, out)
        self.assertEqual('', err)

        # Out of date lightweight checkout
        out, err = self.run_bzr('xmlinfo lightcheckout --verbose')
        expected_xml = '''<?xml version="1.0"?>
<info>
<layout>Lightweight checkout</layout>
<formats>
<format>2a</format>
</formats>
<location>
<light_checkout_root>lightcheckout</light_checkout_root><checkout_of_branch>standalone</checkout_of_branch></location>
<format>
<control>Meta directory format 1</control>
<working_tree>Working tree format 6</working_tree>
<branch>Branch format 4</branch>
<repository>Weave repository format 6</repository>
</format>
<working_tree_stats>
<missing_revisions>1</missing_revisions>
<unchanged>1</unchanged>
<modified>0</modified>
<added>0</added>
<removed>0</removed>
<renamed>0</renamed>
<unknown>0</unknown>
<ignored>0</ignored>
<versioned_subdirectories>0</versioned_subdirectories>
</working_tree_stats>
<branch_history>
<revisions>2</revisions>
<committers>1</committers>
<days_old>0</days_old>
<first_revision>%s</first_revision>
<latest_revision>%s</latest_revision>
</branch_history>
<repository_stats>
<revisions>2</revisions>
</repository_stats>
</info>

''' % (datestring_first, datestring_last,)
        expected_xml = ''.join(expected_xml.split('\n'))+'\n'
        self.assertEqualDiff(expected_xml, out)
        self.assertEqual('', err)

    def test_info_standalone_no_tree(self):
        # create standalone branch without a working tree
        format = bzrdir.format_registry.make_bzrdir('default')
        branch = self.make_branch('branch')
        repo = branch.repository
        out, err = self.run_bzr('xmlinfo branch -v')
        expected_xml = '''<?xml version="1.0"?>
<info>
<layout>Standalone branch</layout>
<formats>
<format>2a</format>
</formats>
<location>
<branch_root>branch</branch_root></location>
<format>
<control>Meta directory format 1</control>
<branch>%s</branch>
<repository>%s</repository>
</format>
<branch_history>
<revisions>0</revisions>
<committers>0</committers>
</branch_history>
<repository_stats>
<revisions>0</revisions>
</repository_stats>
</info>

''' % (format.get_branch_format().get_format_description(),
       format.repository_format.get_format_description(),
       )
        expected_xml = ''.join(expected_xml.split('\n'))+'\n'
        self.assertEqualDiff(expected_xml, out)
        self.assertEqual('', err)

    def test_info_shared_repository(self):
        format = bzrdir.format_registry.make_bzrdir('knit')
        transport = self.get_transport()

        # Create shared repository
        repo = self.make_repository('repo', shared=True, format=format)
        repo.set_make_working_trees(False)
        out, err = self.run_bzr('xmlinfo -v repo')
        expected_xml = '''<?xml version="1.0"?>
<info>
<layout>Shared repository</layout>
<formats>
<format>dirstate</format>
<format>dirstate-tags</format>
<format>knit</format>
</formats>
<location>
<shared_repository>%s</shared_repository></location>
<format>
<control>Meta directory format 1</control>
<repository>%s</repository>
</format>
<repository_stats>
<revisions>0</revisions>
</repository_stats>
</info>

''' % ('repo', format.repository_format.get_format_description(),
       )
        expected_xml = ''.join(expected_xml.split('\n'))+'\n'
        self.assertEqualDiff(expected_xml, out)
        self.assertEqual('', err)

        # Create branch inside shared repository
        repo.bzrdir.root_transport.mkdir('branch')
        branch1 = repo.bzrdir.create_branch_convenience('repo/branch',
            format=format)
        out, err = self.run_bzr('xmlinfo -v repo/branch')
        expected_xml = '''<?xml version="1.0"?>
<info>
<layout>Repository branch</layout>
<formats>
<format>dirstate</format>
<format>knit</format>
</formats>
<location>
<shared_repository>repo</shared_repository><repository_branch>repo/branch</repository_branch></location>
<format>
<control>Meta directory format 1</control>
<branch>%s</branch>
<repository>%s</repository>
</format>
<branch_history>
<revisions>0</revisions>
<committers>0</committers>
</branch_history>
<repository_stats>
<revisions>0</revisions>
</repository_stats>
</info>

''' % (format.get_branch_format().get_format_description(),
       format.repository_format.get_format_description(),
       )
        expected_xml = ''.join(expected_xml.split('\n'))+'\n'
        self.assertEqualDiff(expected_xml, out)
        self.assertEqual('', err)

        # Create lightweight checkout
        transport.mkdir('tree')
        transport.mkdir('tree/lightcheckout')
        tree2 = branch1.create_checkout('tree/lightcheckout',
            lightweight=True)
        branch2 = tree2.branch
        self.assertCheckoutStatusOutput('-v tree/lightcheckout', tree2,
                   shared_repo=repo, repo_branch=branch1, verbose=True)

        # Create normal checkout
        tree3 = branch1.create_checkout('tree/checkout')
        self.assertCheckoutStatusOutput('tree/checkout --verbose', tree3,
            verbose=True,
            light_checkout=False, repo_branch=branch1)
        # Update lightweight checkout
        self.build_tree(['tree/lightcheckout/a'])
        tree2.add('a')
        tree2.commit('commit one')
        rev = repo.get_revision(branch2.revision_history()[0])
        datestring_first = osutils.format_date(rev.timestamp, rev.timezone)
        out, err = self.run_bzr('xmlinfo tree/lightcheckout --verbose')
        expected_xml = '''<?xml version="1.0"?>
<info>
<layout>Lightweight checkout</layout>
<formats>
<format>2a</format>
</formats>
<location>
<light_checkout_root>tree/lightcheckout</light_checkout_root><checkout_of_branch>repo/branch</checkout_of_branch><shared_repository>repo</shared_repository></location>
<format>
<control>Meta directory format 1</control>
<working_tree>Working tree format 6</working_tree>
<branch>%s</branch>
<repository>%s</repository>
</format>
<working_tree_stats>
<unchanged>1</unchanged>
<modified>0</modified>
<added>0</added>
<removed>0</removed>
<renamed>0</renamed>
<unknown>0</unknown>
<ignored>0</ignored>
<versioned_subdirectories>0</versioned_subdirectories>
</working_tree_stats>
<branch_history>
<revisions>1</revisions>
<committers>1</committers>
<days_old>0</days_old>
<first_revision>%s</first_revision>
<latest_revision>%s</latest_revision>
</branch_history>
<repository_stats>
<revisions>1</revisions>
</repository_stats>
</info>

''' % (format.get_branch_format().get_format_description(),
       format.repository_format.get_format_description(),
       datestring_first, datestring_first,
       )
        expected_xml = ''.join(expected_xml.split('\n'))+'\n'
        self.assertEqualDiff(expected_xml, out)
        self.assertEqual('', err)

        # Out of date checkout
        out, err = self.run_bzr('xmlinfo -v tree/checkout')
        expected_xml = '''<?xml version="1.0"?>
<info>
<layout>Checkout</layout>
<formats>
<format>unnamed</format>
</formats>
<location>
<checkout_root>tree/checkout</checkout_root><checkout_of_branch>repo/branch</checkout_of_branch></location>
<format>
<control>Meta directory format 1</control>
<working_tree>Working tree format 6</working_tree>
<branch>%s</branch>
<repository>%s</repository>
</format>
<branch_stats>
<missing_revisions>1<missing_revisions>
</branch_stats>
<working_tree_stats>
<unchanged>0</unchanged>
<modified>0</modified>
<added>0</added>
<removed>0</removed>
<renamed>0</renamed>
<unknown>0</unknown>
<ignored>0</ignored>
<versioned_subdirectories>0</versioned_subdirectories>
</working_tree_stats>
<branch_history>
<revisions>0</revisions>
<committers>0</committers>
</branch_history>
<repository_stats>
<revisions>0</revisions>
</repository_stats>
</info>

''' % (format.get_branch_format().get_format_description(),
       format.repository_format.get_format_description(),
       )
        expected_xml = ''.join(expected_xml.split('\n'))+'\n'
        self.assertEqualDiff(expected_xml, out)
        self.assertEqual('', err)

        # Update checkout
        tree3.update()
        self.build_tree(['tree/checkout/b'])
        tree3.add('b')
        out, err = self.run_bzr('xmlinfo tree/checkout --verbose')
        expected_xml = '''<?xml version="1.0"?>
<info>
<layout>Checkout</layout>
<formats>
<format>unnamed</format>
</formats>
<location>
<checkout_root>tree/checkout</checkout_root><checkout_of_branch>repo/branch</checkout_of_branch></location>
<format>
<control>Meta directory format 1</control>
<working_tree>Working tree format 6</working_tree>
<branch>%s</branch>
<repository>%s</repository>
</format>
<working_tree_stats>
<unchanged>1</unchanged>
<modified>0</modified>
<added>1</added>
<removed>0</removed>
<renamed>0</renamed>
<unknown>0</unknown>
<ignored>0</ignored>
<versioned_subdirectories>0</versioned_subdirectories>
</working_tree_stats>
<branch_history>
<revisions>1</revisions>
<committers>1</committers>
<days_old>0</days_old>
<first_revision>%s</first_revision>
<latest_revision>%s</latest_revision>
</branch_history>
<repository_stats>
<revisions>1</revisions>
</repository_stats>
</info>

''' % (format.get_branch_format().get_format_description(),
       format.repository_format.get_format_description(),
       datestring_first, datestring_first,
       )
        expected_xml = ''.join(expected_xml.split('\n'))+'\n'
        self.assertEqualDiff(expected_xml, out)
        self.assertEqual('', err)
        tree3.commit('commit two')

        # Out of date lightweight checkout
        rev = repo.get_revision(branch1.revision_history()[-1])
        datestring_last = osutils.format_date(rev.timestamp, rev.timezone)
        out, err = self.run_bzr('xmlinfo tree/lightcheckout --verbose')
        expected_xml = '''<?xml version="1.0"?>
<info>
<layout>Lightweight checkout</layout>
<formats>
<format>2a</format>
</formats>
<location>
<light_checkout_root>tree/lightcheckout</light_checkout_root><checkout_of_branch>repo/branch</checkout_of_branch><shared_repository>repo</shared_repository></location>
<format>
<control>Meta directory format 1</control>
<working_tree>Working tree format 6</working_tree>
<branch>%s</branch>
<repository>%s</repository>
</format>
<working_tree_stats>
<missing_revisions>1</missing_revisions>
<unchanged>1</unchanged>
<modified>0</modified>
<added>0</added>
<removed>0</removed>
<renamed>0</renamed>
<unknown>0</unknown>
<ignored>0</ignored>
<versioned_subdirectories>0</versioned_subdirectories>
</working_tree_stats>
<branch_history>
<revisions>2</revisions>
<committers>1</committers>
<days_old>0</days_old>
<first_revision>%s</first_revision>
<latest_revision>%s</latest_revision>
</branch_history>
<repository_stats>
<revisions>2</revisions>
</repository_stats>
</info>

''' % (format.get_branch_format().get_format_description(),
       format.repository_format.get_format_description(),
       datestring_first, datestring_last,
       )
        expected_xml = ''.join(expected_xml.split('\n'))+'\n'
        self.assertEqualDiff(expected_xml, out)
        self.assertEqual('', err)

        # Show info about shared branch
        out, err = self.run_bzr('xmlinfo repo/branch --verbose')
        expected_xml = '''<?xml version="1.0"?>
<info>
<layout>Repository branch</layout>
<formats>
<format>dirstate</format>
<format>knit</format>
</formats>
<location>
<shared_repository>repo</shared_repository><repository_branch>repo/branch</repository_branch></location>
<format>
<control>Meta directory format 1</control>
<branch>%s</branch>
<repository>%s</repository>
</format>
<branch_history>
<revisions>2</revisions>
<committers>1</committers>
<days_old>0</days_old>
<first_revision>%s</first_revision>
<latest_revision>%s</latest_revision>
</branch_history>
<repository_stats>
<revisions>2</revisions>
</repository_stats>
</info>

''' % (format.get_branch_format().get_format_description(),
       format.repository_format.get_format_description(),
       datestring_first, datestring_last,
       )
        expected_xml = ''.join(expected_xml.split('\n'))+'\n'
        self.assertEqualDiff(expected_xml, out)
        self.assertEqual('', err)

        # Show info about repository with revisions
        out, err = self.run_bzr('xmlinfo -v repo')
        expected_xml = '''<?xml version="1.0"?>
<info>
<layout>Shared repository</layout>
<formats>
<format>dirstate</format>
<format>dirstate-tags</format>
<format>knit</format>
</formats>
<location>
<shared_repository>repo</shared_repository></location>
<format>
<control>Meta directory format 1</control>
<repository>%s</repository>
</format>
<repository_stats>
<revisions>2</revisions>
</repository_stats>
</info>

''' % (format.repository_format.get_format_description(),
       )
        expected_xml = ''.join(expected_xml.split('\n'))+'\n'
        self.assertEqualDiff(expected_xml, out)
        self.assertEqual('', err)

    def test_info_shared_repository_with_trees(self):
        format = bzrdir.format_registry.make_bzrdir('knit')
        transport = self.get_transport()

        # Create shared repository with working trees
        repo = self.make_repository('repo', shared=True, format=format)
        repo.set_make_working_trees(True)
        out, err = self.run_bzr('xmlinfo -v repo')
        expected_xml = '''<?xml version="1.0"?>
<info>
<layout>Shared repository with trees</layout>
<formats>
<format>dirstate</format>
<format>dirstate-tags</format>
<format>knit</format>
</formats>
<location>
<shared_repository>repo</shared_repository></location>
<format>
<control>Meta directory format 1</control>
<repository>%s</repository>
</format>
<repository_stats>
<revisions>0</revisions>
</repository_stats>
</info>

''' % (format.repository_format.get_format_description(),
       )
        expected_xml = ''.join(expected_xml.split('\n'))+'\n'
        self.assertEqualDiff(expected_xml, out)
        self.assertEqual('', err)

        # Create two branches
        repo.bzrdir.root_transport.mkdir('branch1')
        branch1 = repo.bzrdir.create_branch_convenience('repo/branch1',
            format=format)
        branch2 = branch1.bzrdir.sprout('repo/branch2').open_branch()

        # Empty first branch
        out, err = self.run_bzr('xmlinfo repo/branch1 --verbose')
        expected_xml = '''<?xml version="1.0"?>
<info>
<layout>Repository tree</layout>
<formats>
<format>knit</format>
</formats>
<location>
<shared_repository>repo</shared_repository><repository_branch>repo/branch1</repository_branch></location>
<format>
<control>Meta directory format 1</control>
<working_tree>Working tree format 3</working_tree>
<branch>%s</branch>
<repository>%s</repository>
</format>
<working_tree_stats>
<unchanged>0</unchanged>
<modified>0</modified>
<added>0</added>
<removed>0</removed>
<renamed>0</renamed>
<unknown>0</unknown>
<ignored>0</ignored>
<versioned_subdirectories>0</versioned_subdirectories>
</working_tree_stats>
<branch_history>
<revisions>0</revisions>
<committers>0</committers>
</branch_history>
<repository_stats>
<revisions>0</revisions>
</repository_stats>
</info>

''' % (format.get_branch_format().get_format_description(),
       format.repository_format.get_format_description(),
       )
        expected_xml = ''.join(expected_xml.split('\n'))+'\n'
        self.assertEqualDiff(expected_xml, out)
        self.assertEqual('', err)

        # Update first branch
        self.build_tree(['repo/branch1/a'])
        tree1 = branch1.bzrdir.open_workingtree()
        tree1.add('a')
        tree1.commit('commit one')
        rev = repo.get_revision(branch1.revision_history()[0])
        datestring_first = osutils.format_date(rev.timestamp, rev.timezone)
        out, err = self.run_bzr('xmlinfo -v repo/branch1')
        expected_xml = '''<?xml version="1.0"?>
<info>
<layout>Repository tree</layout>
<formats>
<format>knit</format>
</formats>
<location>
<shared_repository>repo</shared_repository><repository_branch>repo/branch1</repository_branch></location>
<format>
<control>Meta directory format 1</control>
<working_tree>Working tree format 3</working_tree>
<branch>%s</branch>
<repository>%s</repository>
</format>
<working_tree_stats>
<unchanged>1</unchanged>
<modified>0</modified>
<added>0</added>
<removed>0</removed>
<renamed>0</renamed>
<unknown>0</unknown>
<ignored>0</ignored>
<versioned_subdirectories>0</versioned_subdirectories>
</working_tree_stats>
<branch_history>
<revisions>1</revisions>
<committers>1</committers>
<days_old>0</days_old>
<first_revision>%s</first_revision>
<latest_revision>%s</latest_revision>
</branch_history>
<repository_stats>
<revisions>1</revisions>
</repository_stats>
</info>

'''  % (format.get_branch_format().get_format_description(),
       format.repository_format.get_format_description(),
       datestring_first, datestring_first,
       )
        expected_xml = ''.join(expected_xml.split('\n'))+'\n'
        self.assertEqualDiff(expected_xml, out)
        self.assertEqual('', err)

        # Out of date second branch
        out, err = self.run_bzr('xmlinfo repo/branch2 --verbose')
        expected_xml = '''<?xml version="1.0"?>
<info>
<layout>Repository tree</layout>
<formats>
<format>knit</format>
</formats>
<location>
<shared_repository>repo</shared_repository><repository_branch>repo/branch2</repository_branch></location>
<related_branches>
<parent_branch>repo/branch1</parent_branch></related_branches>
<format>
<control>Meta directory format 1</control>
<working_tree>Working tree format 3</working_tree>
<branch>%s</branch>
<repository>%s</repository>
</format>
<working_tree_stats>
<unchanged>0</unchanged>
<modified>0</modified>
<added>0</added>
<removed>0</removed>
<renamed>0</renamed>
<unknown>0</unknown>
<ignored>0</ignored>
<versioned_subdirectories>0</versioned_subdirectories>
</working_tree_stats>
<branch_history>
<revisions>0</revisions>
<committers>0</committers>
</branch_history>
<repository_stats>
<revisions>1</revisions>
</repository_stats>
</info>

''' % (format.get_branch_format().get_format_description(),
       format.repository_format.get_format_description(),
       )
        expected_xml = ''.join(expected_xml.split('\n'))+'\n'
        self.assertEqualDiff(expected_xml, out)
        self.assertEqual('', err)

        # Update second branch
        tree2 = branch2.bzrdir.open_workingtree()
        tree2.pull(branch1)
        out, err = self.run_bzr('xmlinfo -v repo/branch2')
        expected_xml = '''<?xml version="1.0"?>
<info>
<layout>Repository tree</layout>
<formats>
<format>knit</format>
</formats>
<location>
<shared_repository>repo</shared_repository><repository_branch>repo/branch2</repository_branch></location>
<related_branches>
<parent_branch>repo/branch1</parent_branch></related_branches>
<format>
<control>Meta directory format 1</control>
<working_tree>Working tree format 3</working_tree>
<branch>%s</branch>
<repository>%s</repository>
</format>
<working_tree_stats>
<unchanged>1</unchanged>
<modified>0</modified>
<added>0</added>
<removed>0</removed>
<renamed>0</renamed>
<unknown>0</unknown>
<ignored>0</ignored>
<versioned_subdirectories>0</versioned_subdirectories>
</working_tree_stats>
<branch_history>
<revisions>1</revisions>
<committers>1</committers>
<days_old>0</days_old>
<first_revision>%s</first_revision>
<latest_revision>%s</latest_revision>
</branch_history>
<repository_stats>
<revisions>1</revisions>
</repository_stats>
</info>

''' % (format.get_branch_format().get_format_description(),
       format.repository_format.get_format_description(),
       datestring_first, datestring_first,
       )
        expected_xml = ''.join(expected_xml.split('\n'))+'\n'
        self.assertEqualDiff(expected_xml, out)
        self.assertEqual('', err)

        # Show info about repository with revisions
        out, err = self.run_bzr('xmlinfo -v repo')
        expected_xml = '''<?xml version="1.0"?>
<info>
<layout>Shared repository with trees</layout>
<formats>
<format>dirstate</format>
<format>dirstate-tags</format>
<format>knit</format>
</formats>
<location>
<shared_repository>repo</shared_repository></location>
<format>
<control>Meta directory format 1</control>
<repository>%s</repository>
</format>
<repository_stats>
<revisions>1</revisions>
</repository_stats>
</info>

''' % (format.repository_format.get_format_description(),
       )
        expected_xml = ''.join(expected_xml.split('\n'))+'\n'
        self.assertEqualDiff(expected_xml, out)
        self.assertEqual('', err)

    def test_info_shared_repository_with_tree_in_root(self):
        format = bzrdir.format_registry.make_bzrdir('knit')
        transport = self.get_transport()

        # Create shared repository with working trees
        repo = self.make_repository('repo', shared=True, format=format)
        repo.set_make_working_trees(True)
        out, err = self.run_bzr('xmlinfo -v repo')
        expected_xml = '''<?xml version="1.0"?>
<info>
<layout>Shared repository with trees</layout>
<formats>
<format>dirstate</format>
<format>dirstate-tags</format>
<format>knit</format>
</formats>
<location>
<shared_repository>repo</shared_repository></location>
<format>
<control>Meta directory format 1</control>
<repository>%s</repository>
</format>
<repository_stats>
<revisions>0</revisions>
</repository_stats>
</info>

''' % (format.repository_format.get_format_description(),)
        expected_xml = ''.join(expected_xml.split('\n'))+'\n'
        self.assertEqualDiff(expected_xml, out)
        self.assertEqual('', err)

        # Create branch in root of repository
        control = repo.bzrdir
        branch = control.create_branch()
        control.create_workingtree()
        out, err = self.run_bzr('xmlinfo -v repo')
        expected_xml = '''<?xml version="1.0"?>
<info>
<layout>Repository tree</layout>
<formats>
<format>knit</format>
</formats>
<location>
<shared_repository>repo</shared_repository><repository_branch>repo</repository_branch></location>
<format>
<control>Meta directory format 1</control>
<working_tree>Working tree format 3</working_tree>
<branch>%s</branch>
<repository>%s</repository>
</format>
<working_tree_stats>
<unchanged>0</unchanged>
<modified>0</modified>
<added>0</added>
<removed>0</removed>
<renamed>0</renamed>
<unknown>0</unknown>
<ignored>0</ignored>
<versioned_subdirectories>0</versioned_subdirectories>
</working_tree_stats>
<branch_history>
<revisions>0</revisions>
<committers>0</committers>
</branch_history>
<repository_stats>
<revisions>0</revisions>
</repository_stats>
</info>

''' % (format.get_branch_format().get_format_description(),
       format.repository_format.get_format_description(),
       )
        expected_xml = ''.join(expected_xml.split('\n'))+'\n'
        self.assertEqualDiff(expected_xml, out)
        self.assertEqual('', err)

    def assertCheckoutStatusOutput(self,
        command_string, lco_tree, shared_repo=None,
        repo_branch=None,
        tree_locked=False,
        branch_locked=False, repo_locked=False,
        verbose=False,
        light_checkout=True,
        checkout_root=None):
        """Check the output of info in a checkout.

        This is not quite a mirror of the info code: rather than using the
        tree being examined to predict output, it uses a bunch of flags which
        allow us, the test writers, to document what *should* be present in
        the output. Removing this separation would remove the value of the
        tests.

        :param path: the path to the light checkout.
        :param lco_tree: the tree object for the light checkout.
        :param shared_repo: A shared repository is in use, expect that in
            the output.
        :param repo_branch: A branch in a shared repository for non light
            checkouts.
        :param tree_locked: If true, expect the tree to be locked.
        :param branch_locked: If true, expect the branch to be locked.
        :param repo_locked: If true, expect the repository to be locked.
        :param verbose: If true, expect verbose output
        """
        def friendly_location(url):
            path = urlutils.unescape_for_display(url, 'ascii')
            try:
                return osutils.relpath(osutils.getcwd(), path)
            except errors.PathNotChild:
                return path

        if tree_locked:
            # We expect this to fail because of locking errors, dirstate
            # can't be read locked while a write lock is open.
            self.run_bzr_error([], 'xmlinfo ' + command_string)
            return
        out, err = self.run_bzr('xmlinfo %s' % command_string)
        description = {
            (True, True): 'Lightweight checkout',
            (True, False): 'Repository checkout',
            (False, True): 'Lightweight checkout',
            (False, False): 'Checkout',
            }[(shared_repo is not None, light_checkout)]
        format = {True: '<format>2a</format>\n',
                  False: '<format>unnamed</format>'}[light_checkout]
        if repo_locked:
            repo_locked = lco_tree.branch.repository.get_physical_lock_status()
        if repo_locked or branch_locked or tree_locked:
            def locked_message(a_bool):
                if a_bool:
                    return 'locked'
                else:
                    return 'unlocked'
            expected_lock_output = (
                "\n<lock_status>\n"
                "<working_tree>%s</<working_tree>\n"
                "<branch>%s</branch>\n"
                "<repository>%s</repository>\n"
                "</lock_status>" % (
                    locked_message(tree_locked),
                    locked_message(branch_locked),
                    locked_message(repo_locked)))
        else:
            expected_lock_output = ''
        tree_data = ''
        extra_space = ''
        if light_checkout:
            tree_data = ("<light_checkout_root>%s</light_checkout_root>" %
                friendly_location(lco_tree.bzrdir.root_transport.base))
            extra_space = ' '
        if lco_tree.branch.get_bound_location() is not None:
            tree_data += ("<checkout_root>%s</checkout_root>" % (
                friendly_location(lco_tree.branch.bzrdir.root_transport.base)))
        if shared_repo is not None:
            branch_data = (
                "<checkout_of_branch>%s</checkout_of_branch>"
                "<shared_repository>%s</shared_repository>" %
                (friendly_location(repo_branch.bzrdir.root_transport.base),
                 friendly_location(shared_repo.bzrdir.root_transport.base)))
        elif repo_branch is not None:
            branch_data = ("<checkout_of_branch>%s</checkout_of_branch>" %
                (friendly_location(repo_branch.bzrdir.root_transport.base)))
        else:
            branch_data = ("<checkout_of_branch>%s</checkout_of_branch>" %
                lco_tree.branch.bzrdir.root_transport.base)

        if verbose:
            verbose_info = '<committers>0</committers>'
        else:
            verbose_info = ''

        expected_xml = '''<?xml version="1.0"?>
<info>
<layout>%s</layout>
<formats>
%s
</formats>
<location>
%s%s</location>
<format>
<control>Meta directory format 1</control>
<working_tree>%s</working_tree>
<branch>%s</branch>
<repository>%s</repository>
</format>%s
<working_tree_stats>
<unchanged>0</unchanged>
<modified>0</modified>
<added>0</added>
<removed>0</removed>
<renamed>0</renamed>
<unknown>0</unknown>
<ignored>0</ignored>
<versioned_subdirectories>0</versioned_subdirectories>
</working_tree_stats>
<branch_history>
<revisions>0</revisions>
%s
</branch_history>
<repository_stats>
<revisions>0</revisions>
</repository_stats>
</info>

'''  %  (description,
        format,
        tree_data,
        branch_data,
        lco_tree._format.get_format_description(),
        lco_tree.branch._format.get_format_description(),
        lco_tree.branch.repository._format.get_format_description(),
        expected_lock_output,
        verbose_info,
        )
        expected_xml = ''.join(expected_xml.split('\n'))+'\n'
        self.assertEqualDiff(expected_xml, out)
        self.assertEqual('', err)

    def test_info_locking(self):
        transport = self.get_transport()
        # Create shared repository with a branch
        repo = self.make_repository('repo', shared=True,
                                    format=bzrlib.bzrdir.BzrDirMetaFormat1())
        repo.set_make_working_trees(False)
        repo.bzrdir.root_transport.mkdir('branch')
        repo_branch = repo.bzrdir.create_branch_convenience('repo/branch',
                                    format=bzrlib.bzrdir.BzrDirMetaFormat1())
        # Do a heavy checkout
        transport.mkdir('tree')
        transport.mkdir('tree/checkout')
        co_branch = bzrlib.bzrdir.BzrDir.create_branch_convenience('tree/checkout',
            format=bzrlib.bzrdir.BzrDirMetaFormat1())
        co_branch.bind(repo_branch)
        # Do a light checkout of the heavy one
        transport.mkdir('tree/lightcheckout')
        lco_dir = bzrlib.bzrdir.BzrDirMetaFormat1().initialize('tree/lightcheckout')
        bzrlib.branch.BranchReferenceFormat().initialize(lco_dir,
                                                         target_branch=co_branch)
        lco_dir.create_workingtree()
        lco_tree = lco_dir.open_workingtree()

        # Test all permutations of locking the working tree, branch and repository
        # W B R

        # U U U
        self.assertCheckoutStatusOutput('-v tree/lightcheckout', lco_tree,
                                        repo_branch=repo_branch,
                                        verbose=True, light_checkout=True)
        # U U L
        lco_tree.branch.repository.lock_write()
        try:
            self.assertCheckoutStatusOutput('-v tree/lightcheckout',
            lco_tree, repo_branch=repo_branch,
            repo_locked=True, verbose=True, light_checkout=True)
        finally:
            lco_tree.branch.repository.unlock()
        # U L L
        lco_tree.branch.lock_write()
        try:
            self.assertCheckoutStatusOutput('-v tree/lightcheckout',
            lco_tree,
            branch_locked=True,
            repo_locked=True,
            repo_branch=repo_branch,
            verbose=True)
        finally:
            lco_tree.branch.unlock()
        # L L L
        lco_tree.lock_write()
        try:
            self.assertCheckoutStatusOutput('-v tree/lightcheckout',
            lco_tree, repo_branch=repo_branch,
            tree_locked=True,
            branch_locked=True,
            repo_locked=True,
            verbose=True)
        finally:
            lco_tree.unlock()
        # L L U
        lco_tree.lock_write()
        lco_tree.branch.repository.unlock()
        try:
            self.assertCheckoutStatusOutput('-v tree/lightcheckout',
            lco_tree, repo_branch=repo_branch,
            tree_locked=True,
            branch_locked=True,
            verbose=True)
        finally:
            lco_tree.branch.repository.lock_write()
            lco_tree.unlock()
        # L U U
        lco_tree.lock_write()
        lco_tree.branch.unlock()
        try:
            self.assertCheckoutStatusOutput('-v tree/lightcheckout',
            lco_tree, repo_branch=repo_branch,
            tree_locked=True,
            verbose=True)
        finally:
            lco_tree.branch.lock_write()
            lco_tree.unlock()
        # L U L
        lco_tree.lock_write()
        lco_tree.branch.unlock()
        lco_tree.branch.repository.lock_write()
        try:
            self.assertCheckoutStatusOutput('-v tree/lightcheckout',
            lco_tree, repo_branch=repo_branch,
            tree_locked=True,
            repo_locked=True,
            verbose=True)
        finally:
            lco_tree.branch.repository.unlock()
            lco_tree.branch.lock_write()
            lco_tree.unlock()
        # U L U
        lco_tree.branch.lock_write()
        lco_tree.branch.repository.unlock()
        try:
            self.assertCheckoutStatusOutput('-v tree/lightcheckout',
            lco_tree, repo_branch=repo_branch,
            branch_locked=True,
            verbose=True)
        finally:
            lco_tree.branch.repository.lock_write()
            lco_tree.branch.unlock()

        if sys.platform == 'win32':
            self.knownFailure('Win32 cannot run "bzr info"'
                              ' when the tree is locked.')

    def test_info_locking_oslocks(self):
        if sys.platform == "win32":
            raise tests.TestSkipped("don't use oslocks on win32 in unix manner")
        # This test tests old (all-in-one, OS lock using) behaviour which
        # simply cannot work on windows (and is indeed why we changed our
        # design. As such, don't try to remove the thisFailsStrictLockCheck
        # call here.
        self.thisFailsStrictLockCheck()

        tree = self.make_branch_and_tree('branch',
                                         format=bzrlib.bzrdir.BzrDirFormat6())

        # Test all permutations of locking the working tree, branch and repository
        # XXX: Well not yet, as we can't query oslocks yet. Currently, it's
        # implemented by raising NotImplementedError and get_physical_lock_status()
        # always returns false. This makes bzr info hide the lock status.  (Olaf)
        # W B R

        # U U U
        out, err = self.run_bzr('xmlinfo -v branch')
        expected_xml = '''<?xml version="1.0"?>
<info>
<layout>Standalone tree</layout>
<formats>
<format>weave</format>
</formats>
<location>
<branch_root>%s</branch_root></location>
<format>
<control>All-in-one format 6</control>
<working_tree>Working tree format 2</working_tree>
<branch>Branch format 4</branch>
<repository>%s</repository>
</format>
<working_tree_stats>
<unchanged>0</unchanged>
<modified>0</modified>
<added>0</added>
<removed>0</removed>
<renamed>0</renamed>
<unknown>0</unknown>
<ignored>0</ignored>
<versioned_subdirectories>0</versioned_subdirectories>
</working_tree_stats>
<branch_history>
<revisions>0</revisions>
<committers>0</committers>
</branch_history>
<repository_stats>
<revisions>0</revisions>
</repository_stats>
</info>

''' % ('branch', tree.branch.repository._format.get_format_description(),
       )
        expected_xml = ''.join(expected_xml.split('\n'))+'\n'
        self.assertEqualDiff(expected_xml, out)
        self.assertEqual('', err)
        # L L L
        tree.lock_write()
        out, err = self.run_bzr('xmlinfo -v branch')
        expected_xml = '''<?xml version="1.0"?>
<info>
<layout>Standalone tree</layout>
<formats>
<format>weave</format>
</formats>
<location>
<branch_root>%s</branch_root></location>
<format>
<control>All-in-one format 6</control>
<working_tree>Working tree format 2</working_tree>
<branch>Branch format 4</branch>
<repository>%s</repository>
</format>
<working_tree_stats>
<unchanged>0</unchanged>
<modified>0</modified>
<added>0</added>
<removed>0</removed>
<renamed>0</renamed>
<unknown>0</unknown>
<ignored>0</ignored>
<versioned_subdirectories>0</versioned_subdirectories>
</working_tree_stats>
<branch_history>
<revisions>0</revisions>
<committers>0</committers>
</branch_history>
<repository_stats>
<revisions>0</revisions>
</repository_stats>
</info>

'''% ('branch', tree.branch.repository._format.get_format_description(),
       )
        expected_xml = ''.join(expected_xml.split('\n'))+'\n'
        self.assertEqualDiff(expected_xml, out)
        self.assertEqual('', err)
        tree.unlock()

    def test_info_stacked(self):
        # We have a mainline
        trunk_tree = self.make_branch_and_tree('mainline', format='1.6')
        trunk_tree.commit('mainline')
        # and a branch from it which is stacked
        new_dir = trunk_tree.bzrdir.sprout('newbranch', stacked=True)
        out, err = self.run_bzr('xmlinfo  newbranch')
        expected_xml = '''<?xml version="1.0"?>
<info>
<layout>Standalone tree</layout>
<formats>
<format>1.6</format>
</formats>
<location><branch_root>newbranch</branch_root></location>
<related_branches>
<parent_branch>mainline</parent_branch>
<stacked_on>mainline</stacked_on>
</related_branches>
</info>'''
        expected_xml = ''.join(expected_xml.split('\n'))+'\n'
        self.assertEqual(expected_xml, out)
        self.assertEqual("", err)

