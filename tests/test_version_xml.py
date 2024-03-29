# Copyright (C) 2007 Canonical Ltd
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

"""Black-box tests for bzr version."""

import sys

import bzrlib
from bzrlib import osutils, trace
from bzrlib.tests import (
    probe_unicode_in_user_encoding,
    TestCaseInTempDir,
    TestSkipped,
    )

from bzrlib.xml_serializer import elementtree as elementtree
fromstring = elementtree.fromstring

from bzrlib.plugins.xmloutput import versionxml


class BaseVersionXMLTestCase(TestCaseInTempDir):
    """Base versionxml testcase."""

    def setUp(self):
        TestCaseInTempDir.setUp(self)
        # versionxml tries to call bzrlib.version._get_bzr_source_tree(), which
        # tries an open_containing within the bzr installation. This will cause
        # a test isolation failure. You might hope that you could avoid this
        # with TestCase.permit_source_tree_branch_repo(), but this does not
        # work when running against a bzr installation that has no source tree,
        # as in this case, the open_containing operation needs to recurse
        # upwards to the filesystem root before it knows that it is finished.
        # Therefore we just stub out the relevant function so that it does not
        # call the problem method.
        self.old_show_source_tree = versionxml._show_source_tree
        versionxml._show_source_tree = lambda _: None

    def tearDown(self):
        # restore the patched function.
        versionxml._show_source_tree = self.old_show_source_tree
        TestCaseInTempDir.tearDown(self)


class TestVersionXML(BaseVersionXMLTestCase):

    def test_version(self):
        out = self.run_bzr("xmlversion")[0]
        versionElem = fromstring(out)
        self.assertTrue(len(out) > 0)
        self.assertEquals(1, len(versionElem.findall('bazaar/version')))
        self.assertEquals(1, len(versionElem.findall('bazaar/bzrlib')))
        self.assertEquals(1, len(versionElem.findall('bazaar/configuration')))
        self.assertEquals(1, len(versionElem.findall('bazaar/log_file')))
        self.assertEquals(1, len(versionElem.findall('bazaar/copyright')))
        if sys.platform == "win32":
            self.assertEquals(1, len(versionElem.findall('python/dll')))
        else:
            self.assertEquals(1, len(versionElem.findall('python/executable')))
        self.assertEquals(1, len(versionElem.findall('python/version')))
        self.assertEquals(1, len(versionElem.findall('python/standard_library')))


class TestVersionXMLUnicodeOutput(BaseVersionXMLTestCase):

    def _check(self, args):
        # Even though trace._bzr_log_filename variable
        # is used only to keep actual log filename
        # and changing this variable in selftest
        # don't change main .bzr.log location,
        # and therefore pretty safe,
        # but we run these tests in separate temp dir
        # with relative unicoded path
        old_trace_file = trace._bzr_log_filename
        trace._bzr_log_filename = u'\u1234/.bzr.log'
        try:
            out = self.run_bzr(args)[0]
        finally:
            trace._bzr_log_filename = old_trace_file
        versionElem = fromstring(out)
        self.assertTrue(len(out) > 0)
        self.assertEquals(1, len(versionElem.findall('bazaar/log_file')))

    def test_command(self):
        self._check("xmlversion")

    def test_unicode_bzr_home(self):
        uni_val, str_val = probe_unicode_in_user_encoding()
        if uni_val is None:
            raise TestSkipped('Cannot find a unicode character that works in'
                              ' encoding %s' % \
                              bzrlib.osutils.get_user_encoding())
        osutils.set_or_unset_env('BZR_HOME', str_val)
        out = self.run_bzr("xmlversion")[0]
        self.assertTrue(len(out) > 0)
        versionElem = fromstring(out)
        self.assertEquals(1, len(versionElem.findall('bazaar/configuration')))
        self.assertContainsRe(out, r"<configuration>" + str_val)



